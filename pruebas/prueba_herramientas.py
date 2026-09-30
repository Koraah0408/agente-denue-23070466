import os
import unittest
from app.herramientas import normalizar, cargar_datos, Herramientas, DECLARACIONES
from app.agente import ejecutar, responder
from app.guardia import numeros, numeros_en, cifras_sin_respaldo
from app.bot import leer_permitidos, partir_mensaje, usuario_anonimo
from app.modelo_simulado import llamar_modelo, reset_simulado


class TestHerramientas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, cls.sectores = cargar_datos(
            "data/denue_tampico_madero.csv", "data/sectores_scian.csv"
        )
        cls.herramientas = Herramientas(cls.df, cls.sectores)

    # 1. Normalizar
    def test_01_normalizar(self):
        res = normalizar("  Cafeterías, Neverías y Fuentes de Sodas!  ")
        assert "cafeterias" in res
        assert "y" not in res.split()
        assert "de" not in res.split()

    # 2. Cargar datos
    def test_02_cargar_datos(self):
        assert len(self.df) > 0
        assert len(self.sectores) > 0

    # 3. Buscar actividades existente
    def test_03_buscar_actividades_existente(self):
        res = self.herramientas.buscar_actividades(texto="farmacia")
        assert res["ok"] is True
        assert len(res["actividades"]) > 0

    # 4. Buscar actividades sin coincidencias
    def test_04_buscar_actividades_sin_coincidencias(self):
        res = self.herramientas.buscar_actividades(texto="xyzunexistingterm999")
        assert res["ok"] is True
        assert len(res["actividades"]) == 0

    # 5. Buscar actividades argumento invalido
    def test_05_buscar_actividades_argumento_invalido(self):
        res = self.herramientas.buscar_actividades(texto="")
        assert res["ok"] is False

    # 6. Contar total municipio
    def test_06_contar_total_municipio(self):
        res = self.herramientas.contar(municipio="Tampico")
        assert res["ok"] is True
        assert res["total_filtrado"] > 0

    # 7. Contar actividad especifica
    def test_07_contar_actividad_especifica(self):
        res = self.herramientas.contar(codigo_act="464111", municipio="Tampico")
        assert res["ok"] is True

    # 8. Contar multiple actividad
    def test_08_contar_multiple_actividad(self):
        res = self.herramientas.contar(codigo_act="464111,464112", municipio="Tampico")
        assert res["ok"] is True

    # 9. Contar por colonia
    def test_09_contar_por_colonia(self):
        res = self.herramientas.contar(por="colonia", municipio="Tampico")
        assert res["ok"] is True
        assert "filas" in res

    # 10. Contar por estrato
    def test_10_contar_por_estrato(self):
        res = self.herramientas.contar(por="estrato", municipio="Tampico")
        assert res["ok"] is True

    # 11. Contar por sector
    def test_11_contar_por_sector(self):
        res = self.herramientas.contar(por="sector", municipio="Tampico")
        assert res["ok"] is True

    # 12. Contar filtro colonia
    def test_12_contar_filtro_colonia(self):
        res = self.herramientas.contar(colonia="Centro", municipio="Tampico")
        assert res["ok"] is True

    # 13. Contar filtro estrato
    def test_13_contar_filtro_estrato(self):
        res = self.herramientas.contar(estrato="0 a 5 personas", municipio="Tampico")
        assert res["ok"] is True

    # 14. Contar parametro invalido
    def test_14_contar_parametro_invalido(self):
        res = self.herramientas.contar(por="parametro_inexistente")
        assert res["ok"] is False

    # 15. Ranking colonia top
    def test_15_ranking_colonia_top(self):
        res = self.herramientas.ranking(por="colonia", top=5, municipio="Tampico")
        assert res["ok"] is True
        assert len(res["filas"]) <= 5

    # 16. Ranking actividad top
    def test_16_ranking_actividad_top(self):
        res = self.herramientas.ranking(por="actividad", top=5, municipio="Ciudad Madero")
        assert res["ok"] is True

    # 17. Ranking sector top
    def test_17_ranking_sector_top(self):
        res = self.herramientas.ranking(por="sector", top=3, municipio="Tampico")
        assert res["ok"] is True

    # 18. Ranking top invalido
    def test_18_ranking_top_invalido(self):
        res = self.herramientas.ranking(por="colonia", top=0)
        assert res["ok"] is False

    # 19. Listar filtro combinado
    def test_19_listar_filtro_combinado(self):
        res = self.herramientas.listar(municipio="Ciudad Madero", estrato="251 y mas personas", limite=5)
        assert res["ok"] is True

    # 20. Listar limite
    def test_20_listar_limite(self):
        res = self.herramientas.listar(municipio="Tampico", limite=10)
        assert res["ok"] is True
        assert len(res["establecimientos"]) <= 10

    # 21. Listar limite excedido
    def test_21_listar_limite_excedido(self):
        res = self.herramientas.listar(municipio="Tampico", limite=150)
        assert res["ok"] is True
        assert len(res["establecimientos"]) <= 100

    # 22. Listar campos requeridos
    def test_22_listar_campos_requeridos(self):
        res = self.herramientas.listar(municipio="Tampico", limite=1)
        assert res["ok"] is True
        if res["establecimientos"]:
            item = res["establecimientos"][0]
            assert "nombre" in item
            assert "actividad" in item
            assert "municipio" in item

    # 23. Declaraciones estructura
    def test_23_declaraciones_estructura(self):
        assert len(DECLARACIONES) == 4
        nombres = [d["name"] for d in DECLARACIONES]
        assert "buscar_actividades" in nombres
        assert "contar" in nombres
        assert "ranking" in nombres
        assert "listar" in nombres

    # 24. Errores estructurados de ejecutar (Sección 9.2)
    def test_24_ejecutar_errores_estructurados(self):
        # Municipio invalido
        res1 = ejecutar(self.herramientas, "contar", {"municipio": "MunicipioInexistente"})
        assert res1["ok"] is False
        assert "valores_validos" in res1

        # Codigo con letras
        res2 = ejecutar(self.herramientas, "contar", {"codigo_act": "46411a"})
        assert res2["ok"] is False

        # Listar sin filtros
        res3 = ejecutar(self.herramientas, "listar", {})
        assert res3["ok"] is False

        # Herramienta inexistente
        res4 = ejecutar(self.herramientas, "herramienta_fantasma", {})
        assert res4["ok"] is False
        assert "valores_validos" in res4

        # Argumento inexistente
        res5 = ejecutar(self.herramientas, "contar", {"arg_fantasma": 123})
        assert res5["ok"] is False

    # 25. Extracción de números con comas y marcas de lista (Sección 9.2)
    def test_25_guardia_numeros_comas_y_listas(self):
        texto = "1. Tampico tiene 7,184 negocios\n2) Madero tiene 5.5 y 05"
        nums = numeros(texto)
        assert 7184 in nums
        assert 5.5 in nums
        assert 5 in nums
        assert 1 not in nums  # Marca de lista '1. ' eliminada
        assert 2 not in nums  # Marca de lista '2) ' eliminada

    # 26. Casos de la traza E.2 (Sección 9.2)
    def test_26_guardia_traza_e2(self):
        pregunta = "¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio."
        resultados_h = [
            {
                "ok": True,
                "actividades": [{"codigo_act": "722514", "actividad": "Restaurantes con servicio de preparación de tacos y tortas", "establecimientos": 866}]
            },
            {
                "ok": True,
                "por": "municipio",
                "total_filtrado": 866,
                "filas": [{"valor": "Tampico", "total": 570}, {"valor": "Ciudad Madero", "total": 296}]
            }
        ]
        # G1: Pasa
        g1 = cifras_sin_respaldo("Tampico tiene 570 taquerías y Ciudad Madero 296.", pregunta, resultados_h)
        assert len(g1) == 0

        # G2: Rechaza 274
        g2 = cifras_sin_respaldo("Tampico 570 y Madero 296: una diferencia de 274.", pregunta, resultados_h)
        assert 274 in g2

        # G3: Rechaza 65.8
        g3 = cifras_sin_respaldo("En total hay 866; Tampico concentra el 65.8 %.", pregunta, resultados_h)
        assert 65.8 in g3

        # G4: Pasa marcas de lista
        g4 = cifras_sin_respaldo("1. Tampico: 570\n2. Ciudad Madero: 296\nClase SCIAN 722514", pregunta, resultados_h)
        assert len(g4) == 0

        # G5: Rechaza 1570
        g5 = cifras_sin_respaldo("Tampico tiene 1,570 taquerías.", pregunta, resultados_h)
        assert 1570 in g5

    # 27. Ciclo completo con el simulado (Sección 9.2)
    def test_27_agente_ciclo_simulado(self):
        reset_simulado()
        res = responder(
            pregunta="¿Cuántas farmacias hay en Tampico?",
            herramientas=self.herramientas,
            sistema="Eres un agente analista.",
            llamar=llamar_modelo,
            bitacora_path="logs/test_simulado.jsonl",
            id_pregunta="P00_test",
            canal="prueba",
            modelo_nombre="simulado",
        )
        assert "respuesta" in res
        assert res["turnos"] > 0
        assert res["herramientas"] >= 0
        assert "cifras_sin_respaldo" in res
        if os.path.exists("logs/test_simulado.jsonl"):
            os.remove("logs/test_simulado.jsonl")

    # 28. Funciones puras del bot (Sección 9.2 / 13.3)
    def test_28_bot_funciones_puras(self):
        # 1. leer_permitidos
        perm = leer_permitidos("12345, 67890, invalid")
        assert 12345 in perm
        assert 67890 in perm
        assert len(perm) == 2

        # 2. partir_mensaje
        txt_largo = "A" * 5000
        partes = partir_mensaje(txt_largo, limite=4096)
        assert len(partes) == 2
        assert len(partes[0]) <= 4096

        # 3. usuario_anonimo
        anon = usuario_anonimo(123456789)
        assert len(anon) == 10
        assert anon == usuario_anonimo(123456789)


if __name__ == "__main__":
    unittest.main()
