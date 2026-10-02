"""
Unit tests for the /trilha command logic.
Tests cover: buscar_trilhas, formatar_plano_de_estudos, load_trilhas.
Target: buscar trilhas de JAVA.
"""

import json
import os
import sys
import tempfile
import unittest

# Allow importing the module from the same directory
sys.path.insert(0, os.path.dirname(__file__))
from dio_explorer import (
    buscar_trilhas,
    formatar_plano_de_estudos,
    load_trilhas,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────

TRILHA_JAVA = {
    "id": 1,
    "nome": "Fullstack Java + Angular",
    "tecnologia": "Java, Angular, Spring Boot",
    "nivel": "Intermediário",
    "numero_modulos": 12,
    "xp_total": 18500,
    "badges_disponiveis": ["Java Developer", "Spring Boot Expert", "Angular Fundamentals"],
    "promocoes": {
        "desconto_percentual": 30,
        "validade": "2025-12-31",
        "codigo_cupom": "JAVA30",
    },
    "vitalicio": True,
    "lives_ao_vivo": [
        {"titulo": "Spring Boot na Prática", "data": "2025-08-10", "instrutor": "Felipe Aguiar"}
    ],
}

TRILHA_PYTHON = {
    "id": 2,
    "nome": "Python Data Analytics",
    "tecnologia": "Python, Pandas, NumPy, Power BI",
    "nivel": "Básico",
    "numero_modulos": 10,
    "xp_total": 14000,
    "badges_disponiveis": ["Python Starter", "Data Analyst"],
    "promocoes": {"desconto_percentual": 0, "validade": None, "codigo_cupom": None},
    "vitalicio": False,
    "lives_ao_vivo": [],
}

SAMPLE_TRILHAS = [TRILHA_JAVA, TRILHA_PYTHON]


# ─── Tests: buscar_trilhas ────────────────────────────────────────────────────


class TestBuscarTrilhas(unittest.TestCase):

    def test_busca_java_retorna_trilha_java(self):
        resultado = buscar_trilhas("Java", SAMPLE_TRILHAS)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "Fullstack Java + Angular")

    def test_busca_java_case_insensitive_minusculo(self):
        resultado = buscar_trilhas("java", SAMPLE_TRILHAS)
        self.assertEqual(len(resultado), 1)

    def test_busca_java_case_insensitive_maiusculo(self):
        resultado = buscar_trilhas("JAVA", SAMPLE_TRILHAS)
        self.assertEqual(len(resultado), 1)

    def test_busca_java_parcial_spring(self):
        """'spring boot' is part of the Java trail's tecnologia field."""
        resultado = buscar_trilhas("Spring Boot", SAMPLE_TRILHAS)
        self.assertEqual(len(resultado), 1)
        self.assertIn("Java", resultado[0]["tecnologia"])

    def test_busca_tecnologia_inexistente_retorna_lista_vazia(self):
        resultado = buscar_trilhas("Kotlin", SAMPLE_TRILHAS)
        self.assertEqual(resultado, [])

    def test_busca_retorna_multiplas_trilhas(self):
        """Both trails contain 'python' if we add a second python trail."""
        trilha_python2 = {**TRILHA_PYTHON, "id": 99, "nome": "Python Avançado"}
        resultado = buscar_trilhas("python", [TRILHA_JAVA, TRILHA_PYTHON, trilha_python2])
        self.assertEqual(len(resultado), 2)

    def test_busca_com_espacos_extras_no_termo(self):
        resultado = buscar_trilhas("  java  ", SAMPLE_TRILHAS)
        self.assertEqual(len(resultado), 1)


# ─── Tests: formatar_plano_de_estudos ────────────────────────────────────────


class TestFormatarPlanoDeEstudos(unittest.TestCase):

    def setUp(self):
        self.saida = formatar_plano_de_estudos(TRILHA_JAVA)

    def test_contem_nome_da_trilha(self):
        self.assertIn("Fullstack Java + Angular", self.saida)

    def test_contem_tecnologia(self):
        self.assertIn("Java, Angular, Spring Boot", self.saida)

    def test_contem_nivel(self):
        self.assertIn("Intermediário", self.saida)

    def test_contem_numero_de_modulos(self):
        self.assertIn("12", self.saida)

    def test_contem_xp_total(self):
        self.assertIn("18500", self.saida)

    def test_vitalicio_sim(self):
        self.assertIn("Sim", self.saida)

    def test_vitalicio_nao(self):
        saida_nao = formatar_plano_de_estudos(TRILHA_PYTHON)
        self.assertIn("Não", saida_nao)

    def test_contem_badges(self):
        self.assertIn("Java Developer", self.saida)
        self.assertIn("Spring Boot Expert", self.saida)

    def test_contem_cupom_de_desconto(self):
        self.assertIn("JAVA30", self.saida)
        self.assertIn("30%", self.saida)

    def test_sem_promocao_exibe_mensagem(self):
        saida_sem_promo = formatar_plano_de_estudos(TRILHA_PYTHON)
        self.assertIn("Nenhuma promoção ativa", saida_sem_promo)

    def test_contem_live(self):
        self.assertIn("Spring Boot na Prática", self.saida)
        self.assertIn("Felipe Aguiar", self.saida)

    def test_sem_lives_exibe_mensagem(self):
        saida_sem_live = formatar_plano_de_estudos(TRILHA_PYTHON)
        self.assertIn("Nenhuma live agendada", saida_sem_live)


# ─── Tests: load_trilhas ─────────────────────────────────────────────────────


class TestLoadTrilhas(unittest.TestCase):

    def test_load_retorna_lista(self):
        """Integration test: load real JSON file and verify list returned."""
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "Data", "trilhas_dio.json"
        )
        trilhas = load_trilhas(data_path)
        self.assertIsInstance(trilhas, list)
        self.assertGreater(len(trilhas), 0)

    def test_load_trilhas_contem_campos_obrigatorios(self):
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "Data", "trilhas_dio.json"
        )
        trilhas = load_trilhas(data_path)
        campos = {"id", "nome", "tecnologia", "nivel", "numero_modulos", "xp_total"}
        for t in trilhas:
            for campo in campos:
                self.assertIn(campo, t, msg=f"Campo '{campo}' ausente na trilha id={t.get('id')}")

    def test_load_de_arquivo_temporario(self):
        data = {"trilhas": [TRILHA_JAVA]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False)
            tmp_path = tmp.name
        try:
            trilhas = load_trilhas(tmp_path)
            self.assertEqual(len(trilhas), 1)
            self.assertEqual(trilhas[0]["nome"], "Fullstack Java + Angular")
        finally:
            os.unlink(tmp_path)

    def test_busca_java_no_arquivo_real(self):
        """End-to-end: search Java in the real data file."""
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "Data", "trilhas_dio.json"
        )
        trilhas = load_trilhas(data_path)
        resultado = buscar_trilhas("java", trilhas)
        self.assertGreater(len(resultado), 0, "Nenhuma trilha de Java encontrada no arquivo real")
        tecnologias = [t["tecnologia"].lower() for t in resultado]
        for tec in tecnologias:
            self.assertIn("java", tec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
