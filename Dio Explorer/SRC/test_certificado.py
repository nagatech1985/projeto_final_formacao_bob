"""
Unit tests for the /certificado command logic.
Tests cover: buscar_trilha_para_certificado, gerar_certificado, formatar_certificado,
             _gerar_codigo_verificacao.
"""

import os
import re
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from dio_explorer import (
    _gerar_codigo_verificacao,
    buscar_trilha_para_certificado,
    formatar_certificado,
    gerar_certificado,
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
    "lives_ao_vivo": [],
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

TRILHA_SEM_VITALICIO = {**TRILHA_JAVA, "vitalicio": False}

SAMPLE_TRILHAS = [TRILHA_JAVA, TRILHA_PYTHON]


# ─── Tests: _gerar_codigo_verificacao ────────────────────────────────────────


class TestGerarCodigoVerificacao(unittest.TestCase):

    def test_comeca_com_dio(self):
        codigo = _gerar_codigo_verificacao()
        self.assertTrue(codigo.startswith("DIO-"))

    def test_comprimento_total(self):
        # "DIO-" = 4 chars + 12 alphanumeric = 16 total
        codigo = _gerar_codigo_verificacao()
        self.assertEqual(len(codigo), 16)

    def test_apenas_maiusculas_e_digitos_apos_prefixo(self):
        codigo = _gerar_codigo_verificacao()
        sufixo = codigo[4:]  # after "DIO-"
        self.assertTrue(sufixo.isalnum())
        self.assertEqual(sufixo, sufixo.upper())

    def test_codigos_diferentes_a_cada_chamada(self):
        codigos = {_gerar_codigo_verificacao() for _ in range(20)}
        # With 36^12 possible values, duplicates are astronomically unlikely
        self.assertGreater(len(codigos), 1)


# ─── Tests: buscar_trilha_para_certificado ────────────────────────────────────


class TestBuscarTrilhaParaCertificado(unittest.TestCase):

    def test_busca_por_nome_exato_parcial(self):
        resultado = buscar_trilha_para_certificado("Fullstack Java", SAMPLE_TRILHAS)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["nome"], "Fullstack Java + Angular")

    def test_busca_por_nome_case_insensitive(self):
        resultado = buscar_trilha_para_certificado("fullstack java", SAMPLE_TRILHAS)
        self.assertIsNotNone(resultado)

    def test_busca_por_tecnologia_fallback(self):
        """When name doesn't match, falls back to searching by tecnologia."""
        resultado = buscar_trilha_para_certificado("Spring Boot", SAMPLE_TRILHAS)
        self.assertIsNotNone(resultado)
        self.assertIn("Spring Boot", resultado["tecnologia"])

    def test_trilha_nao_encontrada_retorna_none(self):
        resultado = buscar_trilha_para_certificado("Rust", SAMPLE_TRILHAS)
        self.assertIsNone(resultado)

    def test_busca_com_espacos_extras(self):
        resultado = buscar_trilha_para_certificado("  python  ", SAMPLE_TRILHAS)
        self.assertIsNotNone(resultado)

    def test_busca_java_no_arquivo_real(self):
        """Integration test: search Java in the real data file."""
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "Data", "trilhas_dio.json"
        )
        trilhas = load_trilhas(data_path)
        resultado = buscar_trilha_para_certificado("Java", trilhas)
        self.assertIsNotNone(resultado)
        self.assertIn("Java", resultado["tecnologia"])


# ─── Tests: gerar_certificado ────────────────────────────────────────────────


class TestGerarCertificado(unittest.TestCase):

    def setUp(self):
        self.cert = gerar_certificado("João da Silva", TRILHA_JAVA)

    def test_retorna_dict(self):
        self.assertIsInstance(self.cert, dict)

    def test_chaves_obrigatorias(self):
        chaves = {
            "nome_aluno", "trilha", "tecnologia", "nivel",
            "numero_modulos", "xp_total", "vitalicio",
            "badges", "codigo_verificacao", "emitido_em",
        }
        for chave in chaves:
            self.assertIn(chave, self.cert)

    def test_nome_aluno_preservado(self):
        self.assertEqual(self.cert["nome_aluno"], "João da Silva")

    def test_nome_aluno_com_espacos_extras(self):
        cert = gerar_certificado("  João  ", TRILHA_JAVA)
        self.assertEqual(cert["nome_aluno"], "João")

    def test_trilha_correta(self):
        self.assertEqual(self.cert["trilha"], "Fullstack Java + Angular")

    def test_xp_total_correto(self):
        self.assertEqual(self.cert["xp_total"], 18500)

    def test_numero_modulos_correto(self):
        self.assertEqual(self.cert["numero_modulos"], 12)

    def test_vitalicio_verdadeiro(self):
        self.assertTrue(self.cert["vitalicio"])

    def test_vitalicio_falso(self):
        cert = gerar_certificado("Maria", TRILHA_SEM_VITALICIO)
        self.assertFalse(cert["vitalicio"])

    def test_badges_corretas(self):
        self.assertIn("Java Developer", self.cert["badges"])
        self.assertIn("Spring Boot Expert", self.cert["badges"])

    def test_codigo_verificacao_formato(self):
        self.assertTrue(self.cert["codigo_verificacao"].startswith("DIO-"))

    def test_data_emissao_hoje(self):
        hoje = date.today().strftime("%d/%m/%Y")
        self.assertEqual(self.cert["emitido_em"], hoje)


# ─── Tests: formatar_certificado ─────────────────────────────────────────────


class TestFormatarCertificado(unittest.TestCase):

    def setUp(self):
        self.cert = gerar_certificado("João da Silva", TRILHA_JAVA)
        self.saida = formatar_certificado(self.cert)

    def test_saida_e_string(self):
        self.assertIsInstance(self.saida, str)

    def test_saida_nao_vazia(self):
        self.assertGreater(len(self.saida.strip()), 0)

    def test_contem_nome_aluno(self):
        self.assertIn("João da Silva", self.saida)

    def test_contem_nome_trilha(self):
        self.assertIn("Fullstack Java + Angular", self.saida)

    def test_contem_tecnologia(self):
        self.assertIn("Java, Angular, Spring Boot", self.saida)

    def test_contem_nivel(self):
        self.assertIn("Intermediário", self.saida)

    def test_contem_xp(self):
        self.assertIn("18500", self.saida)

    def test_contem_modulos(self):
        self.assertIn("12", self.saida)

    def test_vitalicio_sim(self):
        self.assertIn("Sim", self.saida)

    def test_vitalicio_nao(self):
        cert_nao = gerar_certificado("Maria", TRILHA_SEM_VITALICIO)
        saida = formatar_certificado(cert_nao)
        self.assertIn("Não", saida)

    def test_contem_badges(self):
        self.assertIn("Java Developer", self.saida)
        self.assertIn("✅", self.saida)

    def test_contem_codigo_verificacao(self):
        self.assertIn(self.cert["codigo_verificacao"], self.saida)

    def test_contem_data_emissao(self):
        self.assertIn(self.cert["emitido_em"], self.saida)

    def test_contem_plataforma_dio(self):
        self.assertIn("Digital Innovation One", self.saida)

    def test_fluxo_completo_java_arquivo_real(self):
        """
        End-to-end integration test:
        1. Load real JSON
        2. Find Java trail
        3. Generate certificate
        4. Format and validate output
        """
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "Data", "trilhas_dio.json"
        )
        trilhas = load_trilhas(data_path)
        trilha = buscar_trilha_para_certificado("Java", trilhas)
        self.assertIsNotNone(trilha)

        cert = gerar_certificado("Aluno Teste DIO", trilha)
        saida = formatar_certificado(cert)

        self.assertIn("Aluno Teste DIO", saida)
        self.assertIn("DIO-", saida)
        self.assertIn("Certificado de Conclusão", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
