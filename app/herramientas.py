import unicodedata
import re
import pandas as pd

VALID_MUNICIPIOS = ["Tampico", "Ciudad Madero"]
VALID_ESTRATOS = [
    "0 a 5 personas",
    "6 a 10 personas",
    "11 a 30 personas",
    "31 a 50 personas",
    "51 a 100 personas",
    "101 a 250 personas",
    "251 y más personas",
]
STOPWORDS = {"de", "del", "la", "las", "los", "y", "e", "o", "u", "en", "para", "por", "con", "sin"}


def normalizar(texto: str) -> str:
    if not texto or not isinstance(texto, str):
        return ""
    texto = texto.lower()
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c) and ord(c) < 128)
    cleaned = re.sub(r"[^\w\s]", " ", ascii_text)
    return " ".join(w for w in cleaned.split() if w not in STOPWORDS)


ESTRATO_RANK = {normalizar(est): idx for idx, est in enumerate(reversed(VALID_ESTRATOS))}

def stem_word(w: str) -> str:
    w = normalizar(w)
    if len(w) > 5 and w.endswith("es"):
        return w[:-2]
    if len(w) > 4 and w.endswith("s"):
        return w[:-1]
    return w

def cargar_datos(ruta_denue: str, ruta_sectores: str):
    df = pd.read_csv(ruta_denue, dtype=str, keep_default_na=False)
    sectores_df = pd.read_csv(ruta_sectores, dtype=str, keep_default_na=False)
    
    # Map sector code to sector name
    sectores_dict = dict(zip(sectores_df["sector"], sectores_df["nombre_sector"]))
    
    # Add normalized columns
    df["colonia_norm"] = df["colonia"].apply(normalizar)
    df["actividad_norm"] = df["actividad"].apply(normalizar)
    
    return df, sectores_dict


class Herramientas:
    def __init__(self, df: pd.DataFrame, sectores: dict):
        self.df = df
        self.sectores = sectores
        self.valid_sectores = sorted(list(sectores.keys()))

    def _aplicar_filtros(self, municipio=None, codigo_act=None, sector=None, estrato=None, colonia=None, ignorar_colonia=False):
        sub_df = self.df
        filtros_aplicados = {}

        # 1. Municipio
        if municipio is not None and str(municipio).strip():
            mun_norm = normalizar(str(municipio))
            found = None
            for v in VALID_MUNICIPIOS:
                if normalizar(v) == mun_norm:
                    found = v
                    break
            if not found:
                return None, None, {
                    "ok": False,
                    "error": f"Municipio invalido: '{municipio}'",
                    "valores_validos": VALID_MUNICIPIOS,
                }
            filtros_aplicados["municipio"] = found
            sub_df = sub_df[sub_df["municipio"] == found]

        # 2. codigo_act
        if codigo_act is not None and str(codigo_act).strip():
            cods = [c.strip() for c in str(codigo_act).split(",") if c.strip()]
            for c in cods:
                if not c.isdigit() or not (2 <= len(c) <= 6):
                    return None, None, {
                        "ok": False,
                        "error": f"Codigo SCIAN invalido: '{c}' (debe contener entre 2 y 6 digitos)",
                        "valores_validos": None,
                    }
            filtros_aplicados["codigo_act"] = ",".join(cods)
            
            # Filter by any prefix
            pattern = "^(" + "|".join(cods) + ")"
            sub_df = sub_df[sub_df["codigo_act"].str.contains(pattern, regex=True, na=False)]

        # 3. Sector
        if sector is not None and str(sector).strip():
            sec_val = str(sector).strip()
            if sec_val not in self.sectores:
                return None, None, {
                    "ok": False,
                    "error": f"Sector invalido: '{sec_val}'",
                    "valores_validos": self.valid_sectores,
                }
            filtros_aplicados["sector"] = sec_val
            sub_df = sub_df[sub_df["sector"] == sec_val]

        # 4. Estrato
        if estrato is not None and str(estrato).strip():
            est_norm = normalizar(str(estrato))
            found_est = None
            for e in VALID_ESTRATOS:
                if normalizar(e) == est_norm:
                    found_est = e
                    break
            if not found_est:
                return None, None, {
                    "ok": False,
                    "error": f"Estrato invalido: '{estrato}'",
                    "valores_validos": VALID_ESTRATOS,
                }
            filtros_aplicados["estrato"] = found_est
            sub_df = sub_df[sub_df["estrato"].map(normalizar) == normalizar(found_est)]

        # 5. Colonia
        if not ignorar_colonia and colonia is not None and str(colonia).strip():
            col_raw = str(colonia).strip()
            col_norm = normalizar(col_raw)
            res_df = sub_df[sub_df["colonia_norm"] == col_norm]
            if res_df.empty:
                sug_colonias = sub_df[sub_df["colonia_norm"].str.contains(col_norm, regex=False, na=False)]["colonia"].unique()
                sug_list = sorted(list(sug_colonias))[:10]
                return None, None, {
                    "ok": False,
                    "error": f"No se encontraron establecimientos en la colonia '{col_raw}' con los filtros aplicados",
                    "valores_validos": sug_list,
                }
            filtros_aplicados["colonia"] = res_df["colonia"].iloc[0]
            sub_df = res_df

        return sub_df, filtros_aplicados, None

    def buscar_actividades(self, texto: str) -> dict:
        if not texto or not str(texto).strip():
            return {
                "ok": False,
                "error": "El parametro 'texto' es obligatorio",
                "valores_validos": None,
            }
        
        words = [w for w in normalizar(str(texto)).split() if len(w) >= 3]
        if not words:
            words = [normalizar(str(texto))]

        stemmed_words = [stem_word(w) for w in words]
        
        sub = self.df
        for sw in stemmed_words:
            sub = sub[sub["actividad_norm"].str.contains(sw, regex=False, na=False)]

        if sub.empty:
            return {
                "ok": True,
                "fuente": "DENUE 05/2026, INEGI",
                "actividades": [],
            }

        grouped = (
            sub.groupby(["codigo_act", "actividad"])
            .size()
            .reset_index(name="establecimientos")
            .sort_values(by=["establecimientos", "codigo_act"], ascending=[False, True])
            .head(15)
        )

        res = []
        for _, row in grouped.iterrows():
            res.append({
                "codigo_act": row["codigo_act"],
                "actividad": row["actividad"],
                "establecimientos": int(row["establecimientos"]),
            })

        return {
            "ok": True,
            "fuente": "DENUE 05/2026, INEGI",
            "actividades": res,
        }

    def contar(
        self,
        municipio=None,
        codigo_act=None,
        sector=None,
        estrato=None,
        colonia=None,
        por=None,
    ) -> dict:
        valid_por = ["municipio", "colonia", "sector", "codigo_act", "estrato"]
        por_val = None
        if por is not None and str(por).strip():
            por_val = str(por).strip()
            if por_val == "actividad":
                por_val = "codigo_act"
            if por_val not in valid_por:
                return {
                    "ok": False,
                    "error": f"parametro 'por' invalido: '{por_val}'",
                    "valores_validos": valid_por,
                }

        sub_df, filtros, err = self._aplicar_filtros(municipio, codigo_act, sector, estrato, colonia)
        if err:
            return err

        if por_val:
            grouped = sub_df.groupby(por_val).size().reset_index(name="total")
            grouped = grouped.sort_values(by="total", ascending=False)
            filas = [
                {"valor": row[por_val], "total": int(row["total"])}
                for _, row in grouped.iterrows()
            ]
            return {
                "ok": True,
                "fuente": "DENUE 05/2026, INEGI",
                "por": por_val,
                "filtros": filtros,
                "total_filtrado": int(len(sub_df)),
                "filas": filas,
            }

        return {
            "ok": True,
            "fuente": "DENUE 05/2026, INEGI",
            "total": int(len(sub_df)),
            "total_filtrado": int(len(sub_df)),
            "filtros": filtros,
        }

    def ranking(
        self,
        por: str,
        top: int = 5,
        municipio=None,
        codigo_act=None,
        sector=None,
        estrato=None,
    ) -> dict:
        valid_por = ["municipio", "colonia", "sector", "codigo_act", "estrato"]
        por_str = str(por).strip() if por else ""
        if por_str == "actividad":
            por_str = "codigo_act"

        if not por_str or por_str not in valid_por:
            return {
                "ok": False,
                "error": f"parametro 'por' invalido: '{por}'",
                "valores_validos": valid_por,
            }

        try:
            top_val = int(top)
        except (ValueError, TypeError):
            top_val = 5
        if top_val < 1:
            return {
                "ok": False,
                "error": "top debe ser mayor que 0",
                "valores_validos": "1 a 20",
            }
        if top_val > 20:
            top_val = 20

        sub_df, filtros, err = self._aplicar_filtros(
            municipio=municipio,
            codigo_act=codigo_act,
            sector=sector,
            estrato=estrato,
            ignorar_colonia=True,
        )
        if err:
            return err

        if sub_df.empty:
            return {
                "ok": True,
                "fuente": "DENUE 05/2026, INEGI",
                "por": por_str,
                "top": top_val,
                "total_filtrado": 0,
                "filas": [],
                "filtros": filtros,
            }

        grouped = sub_df.groupby(por_str).size().reset_index(name="total").sort_values(by="total", ascending=False)
        top_rows = grouped.head(top_val)

        filas = []
        for idx, r in enumerate(top_rows.iterrows(), 1):
            row_data = r[1]
            val = row_data[por_str]
            item = {"valor": val, "total": int(row_data["total"])}
            if por_str == "codigo_act":
                act_rows = sub_df[sub_df["codigo_act"] == val]["actividad"]
                item["actividad"] = act_rows.iloc[0] if not act_rows.empty else ""
            elif por_str == "sector":
                item["nombre_sector"] = self.sectores.get(val, "")
            filas.append(item)

        return {
            "ok": True,
            "fuente": "DENUE 05/2026, INEGI",
            "por": por_str,
            "top": top_val,
            "total_filtrado": len(sub_df),
            "filas": filas,
            "filtros": filtros,
        }

    def listar(
        self,
        limite: int = 10,
        municipio=None,
        codigo_act=None,
        sector=None,
        estrato=None,
        colonia=None,
    ) -> dict:
        # Require at least one filter
        filters_given = [municipio, codigo_act, sector, estrato, colonia]
        if not any(f is not None and str(f).strip() for f in filters_given):
            return {
                "ok": False,
                "error": "listar exige al menos un filtro",
                "valores_validos": None,
            }

        try:
            lim_val = int(limite)
        except (ValueError, TypeError):
            lim_val = 10
        if lim_val < 1:
            lim_val = 1
        if lim_val > 20:
            lim_val = 20

        sub_df, filtros, err = self._aplicar_filtros(municipio, codigo_act, sector, estrato, colonia)
        if err:
            return err

        if sub_df.empty:
            return {
                "ok": True,
                "fuente": "DENUE 05/2026, INEGI",
                "total": 0,
                "mostrados": 0,
                "establecimientos": [],
                "filtros": filtros,
            }

        # Sort: estrato rank (largest to smallest), then name
        sub_df = sub_df.copy()
        sub_df["estrato_rank"] = sub_df["estrato"].map(lambda x: ESTRATO_RANK.get(normalizar(x), 0))
        sorted_df = sub_df.sort_values(by=["estrato_rank", "nombre"], ascending=[True, True])

        head_df = sorted_df.head(lim_val)

        estabs = []
        for _, r in head_df.iterrows():
            estabs.append({
                "id": r["id"],
                "nombre": r["nombre"],
                "actividad": r["actividad"],
                "estrato": r["estrato"],
                "colonia": r["colonia"],
                "municipio": r["municipio"],
            })

        return {
            "ok": True,
            "fuente": "DENUE 05/2026, INEGI",
            "total": len(sub_df),
            "mostrados": len(estabs),
            "establecimientos": estabs,
            "filtros": filtros,
        }


DECLARACIONES = [
    {
        "name": "buscar_actividades",
        "description": "Busca clases de actividad SCIAN por palabras clave en su nombre. Devuelve codigos SCIAN, nombres de actividad y conteos.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "texto": {
                    "type": "STRING",
                    "description": "Palabra o palabras clave del giro buscado (ej: 'farmacia', 'restaurante', 'escuela').",
                }
            },
            "required": ["texto"],
        },
    },
    {
        "name": "contar",
        "description": "Cuenta establecimientos que cumplen todos los filtros dados. Sin filtros cuenta todo el conjunto de Tampico y Ciudad Madero.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo_act": {
                    "type": "STRING",
                    "description": "Uno o varios codigos SCIAN separados por coma (ej: '464111,464112' o '7225'). Cada codigo funciona como prefijo.",
                },
                "municipio": {
                    "type": "STRING",
                    "description": "'Tampico' o 'Ciudad Madero'. Omitelo para ambos municipios.",
                },
                "sector": {
                    "type": "STRING",
                    "description": "Codigo de 2 digitos del sector SCIAN (ej: '72', '46').",
                },
                "estrato": {
                    "type": "STRING",
                    "description": "Rango de personal ocupado (ej: '0 a 5 personas', '6 a 10 personas').",
                },
                "colonia": {
                    "type": "STRING",
                    "description": "Nombre de la colonia. Busca coincidencia exacta ya normalizada; si no hay filas, sugiere colonias parecidas.",
                },
            },
        },
    },
    {
        "name": "ranking",
        "description": "Agrupa establecimientos y muestra los mas frecuentes segun el criterio 'por' (municipio, colonia, sector, codigo_act, estrato).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "por": {
                    "type": "STRING",
                    "description": "Criterio de agrupacion obligatorio: 'municipio', 'colonia', 'sector', 'codigo_act' o 'estrato'.",
                },
                "top": {
                    "type": "INTEGER",
                    "description": "Numero de resultados a mostrar (de 1 a 20, por omision 5).",
                },
                "municipio": {
                    "type": "STRING",
                    "description": "Filtrar por 'Tampico' o 'Ciudad Madero'.",
                },
                "codigo_act": {
                    "type": "STRING",
                    "description": "Uno o varios codigos SCIAN separados por coma.",
                },
                "sector": {
                    "type": "STRING",
                    "description": "Codigo de 2 digitos del sector SCIAN.",
                },
                "estrato": {
                    "type": "STRING",
                    "description": "Rango de personal ocupado.",
                },
            },
            "required": ["por"],
        },
    },
    {
        "name": "listar",
        "description": "Muestra una lista detallada de establecimientos ordenados de mayor a menor estrato. Exige al menos un filtro.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "limite": {
                    "type": "INTEGER",
                    "description": "Numero maximo de establecimientos a listar (1 a 20, por omision 10).",
                },
                "municipio": {
                    "type": "STRING",
                    "description": "'Tampico' o 'Ciudad Madero'.",
                },
                "codigo_act": {
                    "type": "STRING",
                    "description": "Uno o varios codigos SCIAN separados por coma.",
                },
                "sector": {
                    "type": "STRING",
                    "description": "Codigo de 2 digitos del sector SCIAN.",
                },
                "estrato": {
                    "type": "STRING",
                    "description": "Rango de personal ocupado.",
                },
                "colonia": {
                    "type": "STRING",
                    "description": "Nombre de la colonia.",
                },
            },
        },
    },
]
