"""
Unit tests for the /desafio command logic.
Tests cover: normalizar_nivel, gerar_desafio, formatar_desafio.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from dio_explorer import (
    _NIVEL_PADRAO,
    _NIVEIS_VALIDOS,
    _TIPOS_POR_NIVEL,
    _XP_POR_NIVEL,
    formatar_desafio,
    gerar_desafio,
    normalizar_nivel,
)

# ─── Tests: normalizar_nivel ─────────────────────────────────────────────────


class TestNormalizarNivel(unittest.TestCase):

    # ── Níveis válidos ─────────────────────────────────────────────────────

    def test_basico_com_acento(self):
        nivel, padrao = normalizar_nivel("básico")
        self.assertEqual(nivel, "básico")
        self.assertFalse(padrao)

    def test_basico_sem_acento(self):
        nivel, padrao = normalizar_nivel("basico")
        self.assertFalse(padrao)

    def test_intermediario_com_acento(self):
        nivel, padrao = normalizar_nivel("intermediário")
        self.assertFalse(padrao)

    def test_intermediario_sem_acento(self):
        nivel, padrao = normalizar_nivel("intermediario")
        self.assertFalse(padrao)

    def test_avancado_com_acento(self):
        nivel, padrao = normalizar_nivel("avançado")
        self.assertFalse(padrao)

    def test_avancado_sem_acento(self):
        nivel, padrao = normalizar_nivel("avancado")
        self.assertFalse(padrao)

    def test_nivel_com_espaco_no_inicio_e_fim(self):
        nivel, padrao = normalizar_nivel("  básico  ")
        self.assertFalse(padrao)

    # ── Nível inválido → usa padrão ────────────────────────────────────────

    def test_nivel_invalido_retorna_padrao(self):
        nivel, padrao = normalizar_nivel("expert")
        self.assertEqual(nivel, _NIVEL_PADRAO)
        self.assertTrue(padrao)

    def test_string_vazia_retorna_padrao(self):
        nivel, padrao = normalizar_nivel("")
        self.assertEqual(nivel, _NIVEL_PADRAO)
        self.assertTrue(padrao)

    def test_nivel_numerico_retorna_padrao(self):
        nivel, padrao = normalizar_nivel("3")
        self.assertTrue(padrao)


# ─── Tests: gerar_desafio ────────────────────────────────────────────────────


class TestGerarDesafio(unittest.TestCase):

    def test_retorna_dict_com_chaves_obrigatorias(self):
        desafio = gerar_desafio("Java", "básico")
        chaves = {"tecnologia", "nivel", "tipo", "xp", "aviso_padrao"}
        for chave in chaves:
            self.assertIn(chave, desafio)

    def test_tecnologia_preservada(self):
        desafio = gerar_desafio("Java", "básico")
        self.assertEqual(desafio["tecnologia"], "Java")

    def test_tecnologia_com_espacos_extras(self):
        desafio = gerar_desafio("  Java  ", "básico")
        self.assertEqual(desafio["tecnologia"], "Java")

    # ── Nível básico ────────────────────────────────────────────────────────

    def test_xp_basico(self):
        desafio = gerar_desafio("Java", "básico")
        self.assertEqual(desafio["xp"], 200)

    def test_xp_basico_sem_acento(self):
        desafio = gerar_desafio("Java", "basico")
        self.assertEqual(desafio["xp"], 200)

    def test_tipo_basico_valido(self):
        desafio = gerar_desafio("Java", "básico")
        tipos_validos = _TIPOS_POR_NIVEL["básico"]
        self.assertIn(desafio["tipo"], tipos_validos)

    # ── Nível intermediário ────────────────────────────────────────────────

    def test_xp_intermediario(self):
        desafio = gerar_desafio("Java", "intermediário")
        self.assertEqual(desafio["xp"], 800)

    def test_tipo_intermediario_valido(self):
        desafio = gerar_desafio("Java", "intermediário")
        tipos_validos = _TIPOS_POR_NIVEL["intermediário"]
        self.assertIn(desafio["tipo"], tipos_validos)

    # ── Nível avançado ─────────────────────────────────────────────────────

    def test_xp_avancado(self):
        desafio = gerar_desafio("Java", "avançado")
        self.assertEqual(desafio["xp"], 1800)

    def test_tipo_avancado_valido(self):
        desafio = gerar_desafio("Java", "avançado")
        tipos_validos = _TIPOS_POR_NIVEL["avançado"]
        self.assertIn(desafio["tipo"], tipos_validos)

    # ── Nível inválido ─────────────────────────────────────────────────────

    def test_nivel_invalido_usa_padrao(self):
        desafio = gerar_desafio("Java", "senior")
        self.assertTrue(desafio["aviso_padrao"])
        self.assertEqual(desafio["nivel"], _NIVEL_PADRAO)

    def test_nivel_valido_sem_aviso_padrao(self):
        desafio = gerar_desafio("Java", "básico")
        self.assertFalse(desafio["aviso_padrao"])


# ─── Tests: formatar_desafio ─────────────────────────────────────────────────


class TestFormatarDesafio(unittest.TestCase):

    def _desafio_java_basico(self):
        return gerar_desafio("Java", "básico")

    def test_saida_contem_tecnologia(self):
        saida = formatar_desafio(self._desafio_java_basico())
        self.assertIn("Java", saida)

    def test_saida_contem_nivel(self):
        saida = formatar_desafio(self._desafio_java_basico())
        self.assertIn("básico", saida.lower())

    def test_saida_contem_tipo(self):
        desafio = self._desafio_java_basico()
        saida = formatar_desafio(desafio)
        self.assertIn(desafio["tipo"], saida)

    def test_saida_contem_xp(self):
        desafio = self._desafio_java_basico()
        saida = formatar_desafio(desafio)
        self.assertIn(str(desafio["xp"]), saida)

    def test_aviso_padrao_presente_quando_nivel_invalido(self):
        desafio = gerar_desafio("Java", "guru")
        saida = formatar_desafio(desafio)
        self.assertIn("⚠️", saida)
        self.assertIn(_NIVEL_PADRAO, saida)

    def test_sem_aviso_quando_nivel_valido(self):
        desafio = gerar_desafio("Java", "avançado")
        saida = formatar_desafio(desafio)
        self.assertNotIn("⚠️", saida)

    def test_saida_nao_vazia(self):
        saida = formatar_desafio(self._desafio_java_basico())
        self.assertGreater(len(saida.strip()), 0)

    def test_saida_e_string(self):
        saida = formatar_desafio(self._desafio_java_basico())
        self.assertIsInstance(saida, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
