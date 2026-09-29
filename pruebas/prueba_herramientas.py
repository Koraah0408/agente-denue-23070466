import unittest
from app.herramientas import normalizar, cargar_datos, Herramientas, DECLARACIONES


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


if __name__ == "__main__":
    unittest.main()
