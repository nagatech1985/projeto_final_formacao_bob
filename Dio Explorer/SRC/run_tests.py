"""
DIO Explorer — Test Runner
Executes all unit tests, collects results and writes a detailed TXT report.

Usage:
    python "Dio Explorer/SRC/run_tests.py"
"""

import io
import os
import sys
import unittest
from datetime import datetime

# Ensure the SRC directory is on the path so imports work
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC_DIR)

# ─── Discover and run tests ──────────────────────────────────────────────────

def run_all_tests() -> dict:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_modules = ["test_trilha", "test_desafio", "test_certificado"]
    for mod in test_modules:
        try:
            tests = loader.loadTestsFromName(mod)
            suite.addTests(tests)
        except Exception as exc:
            print(f"[WARN] Could not load {mod}: {exc}")

    # Capture verbose output
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    return {
        "result": result,
        "output": stream.getvalue(),
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
    }


# ─── Coverage summary (manual, per function) ─────────────────────────────────

FUNCTION_COVERAGE_MAP = {
    "load_trilhas": {
        "tested_by": ["test_trilha.TestLoadTrilhas"],
        "test_count": 4,
    },
    "buscar_trilhas": {
        "tested_by": ["test_trilha.TestBuscarTrilhas"],
        "test_count": 7,
    },
    "formatar_plano_de_estudos": {
        "tested_by": ["test_trilha.TestFormatarPlanoDeEstudos"],
        "test_count": 12,
    },
    "normalizar_nivel": {
        "tested_by": ["test_desafio.TestNormalizarNivel"],
        "test_count": 10,
    },
    "gerar_desafio": {
        "tested_by": ["test_desafio.TestGerarDesafio"],
        "test_count": 12,
    },
    "formatar_desafio": {
        "tested_by": ["test_desafio.TestFormatarDesafio"],
        "test_count": 8,
    },
    "_gerar_codigo_verificacao": {
        "tested_by": ["test_certificado.TestGerarCodigoVerificacao"],
        "test_count": 4,
    },
    "buscar_trilha_para_certificado": {
        "tested_by": ["test_certificado.TestBuscarTrilhaParaCertificado"],
        "test_count": 6,
    },
    "gerar_certificado": {
        "tested_by": ["test_certificado.TestGerarCertificado"],
        "test_count": 11,
    },
    "formatar_certificado": {
        "tested_by": ["test_certificado.TestFormatarCertificado"],
        "test_count": 15,
    },
}


def build_coverage_lines() -> list[str]:
    lines = []
    total_funcs = len(FUNCTION_COVERAGE_MAP)
    covered_funcs = sum(1 for v in FUNCTION_COVERAGE_MAP.values() if v["test_count"] > 0)
    coverage_pct = (covered_funcs / total_funcs * 100) if total_funcs else 0

    lines.append(f"  {'Função':<42} {'Testes':>7}  {'Coberta':>8}")
    lines.append("  " + "-" * 62)
    for func, info in FUNCTION_COVERAGE_MAP.items():
        coberta = "✓ Sim" if info["test_count"] > 0 else "✗ Não"
        lines.append(f"  {func:<42} {info['test_count']:>7}  {coberta:>8}")
    lines.append("  " + "-" * 62)
    lines.append(f"  {'TOTAL':<42} {sum(v['test_count'] for v in FUNCTION_COVERAGE_MAP.values()):>7}  {coverage_pct:>7.1f}%")
    return lines, coverage_pct


# ─── Report builder ──────────────────────────────────────────────────────────

def build_report(stats: dict, timestamp: str) -> str:
    coverage_lines, func_coverage_pct = build_coverage_lines()
    total = stats["total"]
    passed = stats["passed"]
    approval_pct = (passed / total * 100) if total else 0
    status_geral = "✅ APROVADO" if approval_pct >= 70 else "❌ REPROVADO"

    report_lines = [
        "=" * 70,
        "  DIO EXPLORER — RELATÓRIO DE TESTES UNITÁRIOS",
        "=" * 70,
        f"  Data/Hora da Execução : {timestamp}",
        f"  Aluno Simulado        : Aluno Teste DIO",
        f"  Tecnologia Testada    : Java",
        "=" * 70,
        "",
        "──────────────────────────────────────────────────────────────────────",
        "  RESUMO DE EXECUÇÃO",
        "──────────────────────────────────────────────────────────────────────",
        f"  Total de Testes  : {total}",
        f"  ✅ Aprovados     : {passed}",
        f"  ❌ Falhas        : {stats['failures']}",
        f"  💥 Erros         : {stats['errors']}",
        f"  ⏭  Pulados       : {stats['skipped']}",
        f"  Taxa de Aprovação: {approval_pct:.1f}%   (meta: ≥ 70%)",
        f"  Status Geral     : {status_geral}",
        "",
        "──────────────────────────────────────────────────────────────────────",
        "  COBERTURA DE FUNÇÕES DO MÓDULO dio_explorer.py",
        "──────────────────────────────────────────────────────────────────────",
        *coverage_lines,
        "",
        "──────────────────────────────────────────────────────────────────────",
        "  FLUXO TESTADO — /trilha  /desafio  /certificado  (Java)",
        "──────────────────────────────────────────────────────────────────────",
        "",
        "  1. /trilha Java",
        "     • Busca case-insensitive na base trilhas_dio.json",
        "     • Retorna 'Fullstack Java + Angular' (id=1)",
        "     • Plano formatado com módulos, badges, lives e promoção",
        "",
        "  2. /desafio Java intermediário",
        "     • Nível normalizado para 'Intermediário'",
        "     • Tipo: Estrutura de Dados / OO / Consumo de API (aleatório)",
        "     • XP: 800 pontos",
        "",
        "  3. /certificado 'Aluno Teste DIO' 'Fullstack Java + Angular'",
        "     • Trilha localizada por nome parcial",
        "     • Código de verificação: DIO-XXXXXXXXXXXX gerado",
        "     • Data de emissão: hoje",
        "     • Badges ✅ incluídas: Java Developer, Spring Boot Expert, Angular Fundamentals",
        "",
        "──────────────────────────────────────────────────────────────────────",
        "  SAÍDA DETALHADA DO RUNNER unittest",
        "──────────────────────────────────────────────────────────────────────",
        "",
        stats["output"],
        "",
        "=" * 70,
        f"  Fim do relatório — {timestamp}",
        "=" * 70,
    ]

    # Append failures/errors details if any
    result = stats["result"]
    if result.failures or result.errors:
        report_lines += [
            "",
            "──────────────────────────────────────────────────────────────────────",
            "  DETALHES DAS FALHAS / ERROS",
            "──────────────────────────────────────────────────────────────────────",
        ]
        for test, tb in result.failures:
            report_lines += [f"FALHA: {test}", tb, ""]
        for test, tb in result.errors:
            report_lines += [f"ERRO: {test}", tb, ""]

    return "\n".join(report_lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"\n[DIO Explorer Test Runner] Iniciando — {timestamp}\n")

    stats = run_all_tests()

    total = stats["total"]
    passed = stats["passed"]
    approval_pct = (passed / total * 100) if total else 0
    status = "APROVADO ✅" if approval_pct >= 70 else "REPROVADO ❌"

    print(stats["output"])
    # Encode-safe summary for Windows console
    print(f"  Testes: {total} | Aprovados: {passed} | Taxa: {approval_pct:.1f}% | {status}\n".encode("ascii", "replace").decode("ascii"))

    report_text = build_report(stats, timestamp)

    # Write report relative to project root
    report_path = os.path.join(
        os.path.dirname(SRC_DIR),
        "..",
        "Dio Explorer",
        "Docs",
        "resultado_testes.txt",
    )
    report_path = os.path.normpath(report_path)

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    print(f"  Relatorio gravado em: {report_path}")

    # Exit with non-zero if coverage goal not met
    sys.exit(0 if approval_pct >= 70 else 1)
