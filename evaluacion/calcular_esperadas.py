import json
import os
import re
import pandas as pd

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    import unicodedata
    t = texto.lower()
    nfkd = unicodedata.normalize("NFKD", t)
    ascii_t = "".join(c for c in nfkd if not unicodedata.combining(c) and ord(c) < 128)
    return " ".join(ascii_t.split())

def main():
    ruta_denue = os.path.join("data", "denue_tampico_madero.csv")
    ruta_sectores = os.path.join("data", "sectores_scian.csv")

    df = pd.read_csv(ruta_denue, dtype=str, keep_default_na=False)
    sectores_df = pd.read_csv(ruta_sectores, dtype=str, keep_default_na=False)
    sectores_dict = dict(zip(sectores_df["sector"], sectores_df["nombre_sector"]))

    df["actividad_norm"] = df["actividad"].apply(normalizar_texto)
    df["colonia_norm"] = df["colonia"].apply(normalizar_texto)

    # P01: Total en Ciudad Madero
    p01_total = len(df[df["municipio"] == "Ciudad Madero"])

    # P02: Cafeterías, neverías y fuentes de sodas en Tampico
    # SCIAN 722513 (Neverias/paleterias), 722514 (Taquerias/tortas), 722515 (Cafeterias/fuentes de soda)
    df_tam = df[df["municipio"] == "Tampico"]
    caf_df = df_tam[df_tam["codigo_act"].str.startswith(("722513", "722515"))]
    p02_total = len(caf_df)

    # P03: Top 5 actividades en Ciudad Madero
    df_mad = df[df["municipio"] == "Ciudad Madero"]
    top5_mad = (
        df_mad.groupby(["codigo_act", "actividad"])
        .size()
        .reset_index(name="total")
        .sort_values(by="total", ascending=False)
        .head(5)
    )
    p03_cifras = [int(r["total"]) for _, r in top5_mad.iterrows()]

    # P04: Farmacias en Tampico (464111 y 464112)
    farm_df = df_tam[df_tam["codigo_act"].isin(["464111", "464112"])]
    p04_total = len(farm_df)

    # P05: Taquerías Tampico vs Ciudad Madero (722514)
    taq_tam = len(df_tam[df_tam["codigo_act"] == "722514"])
    taq_mad = len(df_mad[df_mad["codigo_act"] == "722514"])

    # P06: Top sector en Tampico
    sec_tam = (
        df_tam.groupby("sector")
        .size()
        .reset_index(name="total")
        .sort_values(by="total", ascending=False)
        .iloc[0]
    )
    p06_sector = sec_tam["sector"]
    p06_total = int(sec_tam["total"])

    # P07: Top colonia salones belleza/peluquerias en Ciudad Madero (812110)
    pel_mad = df_mad[df_mad["codigo_act"] == "812110"]
    col_pel = (
        pel_mad.groupby("colonia")
        .size()
        .reset_index(name="total")
        .sort_values(by="total", ascending=False)
        .iloc[0]
    )
    p07_colonia = col_pel["colonia"]
    p07_total = int(col_pel["total"])

    # P08: Establecimientos 251+ en Ciudad Madero
    e251_mad = df_mad[df_mad["estrato"] == "251 y mas personas"]
    p08_total = len(e251_mad)

    esperadas = [
        {
            "id": "P01",
            "pregunta": "¿Cuántos establecimientos tiene registrados el DENUE en Ciudad Madero?",
            "revision": "automatica",
            "cifras_clave": [p01_total],
            "nota": f"Total en Ciudad Madero: {p01_total}",
        },
        {
            "id": "P02",
            "pregunta": "¿Cuántas cafeterías, neverías y fuentes de sodas hay en Tampico?",
            "revision": "automatica",
            "cifras_clave": [p02_total],
            "nota": f"Total cafeterías y neverías en Tampico: {p02_total}",
        },
        {
            "id": "P03",
            "pregunta": "¿Cuáles son las 5 actividades con más establecimientos en Ciudad Madero y cuántos tiene cada una?",
            "revision": "automatica",
            "cifras_clave": p03_cifras,
            "nota": f"Top 5 conteos en Madero: {p03_cifras}",
        },
        {
            "id": "P04",
            "pregunta": "¿Cuántas farmacias hay en Tampico en total, sumando las que tienen minisúper y las que no?",
            "revision": "automatica",
            "cifras_clave": [p04_total],
            "nota": f"Total farmacias Tampico (464111 y 464112): {p04_total}",
        },
        {
            "id": "P05",
            "pregunta": "¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio.",
            "revision": "automatica",
            "cifras_clave": [taq_tam, taq_mad],
            "nota": f"Taquerías (722514): Tampico {taq_tam}, Madero {taq_mad}",
        },
        {
            "id": "P06",
            "pregunta": "¿Qué sector económico tiene más establecimientos en Tampico y cuántos son?",
            "revision": "automatica",
            "cifras_clave": [int(p06_sector), p06_total],
            "nota": f"Sector principal en Tampico: Sector {p06_sector} ({sectores_dict.get(p06_sector, '')}) con {p06_total}",
        },
        {
            "id": "P07",
            "pregunta": "¿En qué colonia de Ciudad Madero hay más salones de belleza y peluquerías, y cuántos tiene?",
            "revision": "automatica",
            "cifras_clave": [p07_total],
            "nota": f"Colonia con más salones en Madero: {p07_colonia} con {p07_total}",
        },
        {
            "id": "P08",
            "pregunta": "¿Cuántos establecimientos de 251 y más personas hay en Ciudad Madero? Menciona tres de ellos.",
            "revision": "automatica",
            "cifras_clave": [p08_total],
            "nota": f"Establecimientos con 251+ personas en Ciudad Madero: {p08_total}",
        },
        {
            "id": "P09",
            "pregunta": "¿Cuántos trabajadores tiene exactamente la Refinería Francisco I. Madero?",
            "revision": "manual",
            "criterio": "Debe explicar que el DENUE registra personal ocupado únicamente en estratos por rango (ej. 251 y más personas) y no proporciona el número exacto de empleados.",
        },
        {
            "id": "P10",
            "pregunta": "¿Cuál es el negocio más rentable para abrir en Tampico?",
            "revision": "manual",
            "criterio": "Debe aclarar que el DENUE no contiene datos sobre ventas, ingresos, utilidades o rentabilidad de los negocios.",
        },
    ]

    out_path = os.path.join("evaluacion", "esperadas.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"esperadas": esperadas}, f, ensure_ascii=False, indent=2)

    print(f"Respuestas esperadas calculadas exitosamente y guardadas en {out_path}")

if __name__ == "__main__":
    main()
