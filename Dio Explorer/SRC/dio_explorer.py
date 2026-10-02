"""
DIO Explorer — core business logic module.

Contains the functions that back the /trilha, /desafio and /certificado
commands so they can be unit-tested independently of the chat interface.
"""

import json
import os
import re
import random
import string
from datetime import date
from typing import Optional

# ─── Path helpers ────────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_FILE = os.path.join(_ROOT, "Data", "trilhas_dio.json")


def load_trilhas(data_file: str = _DATA_FILE) -> list[dict]:
    """Load and return the list of trilhas from the JSON data file."""
    with open(data_file, encoding="utf-8") as fh:
        return json.load(fh)["trilhas"]


# ─── /trilha ─────────────────────────────────────────────────────────────────


def buscar_trilhas(tecnologia: str, trilhas: list[dict]) -> list[dict]:
    """
    Return every trilha whose *tecnologia* field contains the given term
    (case-insensitive, partial match).
    """
    termo = tecnologia.strip().lower()
    return [t for t in trilhas if termo in t["tecnologia"].lower()]


def formatar_plano_de_estudos(trilha: dict) -> str:
    """
    Render a /trilha result as a Markdown string that matches the template
    defined in `.bob/commands/trilha.md`.
    """
    promo = trilha.get("promocoes", {})
    desconto = promo.get("desconto_percentual", 0)
    vitalicio = "Sim" if trilha.get("vitalicio") else "Não"

    # Header
    lines = [
        f"# 📚 Plano de Estudos — {trilha['nome']}",
        "",
        f"**🏷️ Tecnologia:** {trilha['tecnologia']}  ",
        f"**📊 Nível:** {trilha['nivel']}  ",
        f"**📦 Total de Módulos:** {trilha['numero_modulos']}  ",
        f"**⭐ XP Total ao concluir:** {trilha['xp_total']} XP  ",
        f"**♾️ Acesso Vitalício:** {vitalicio}  ",
        "",
        "---",
        "",
    ]

    # Badges
    lines.append("## 🏅 Badges Disponíveis")
    lines.append("")
    for badge in trilha.get("badges_disponiveis", []):
        lines.append(f"- [ ] {badge}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Lives
    lives = trilha.get("lives_ao_vivo", [])
    lines.append("## 🎥 Lives ao Vivo")
    lines.append("")
    if lives:
        for live in lives:
            lines.append(
                f"- **{live['titulo']}** — 📅 {live['data']} — 👨‍🏫 {live['instrutor']}"
            )
    else:
        lines.append("Nenhuma live agendada.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Promo
    lines.append("## 🏷️ Promoção Ativa")
    lines.append("")
    if desconto > 0:
        lines.append(
            f"> 🔖 Use o cupom **{promo['codigo_cupom']}** e ganhe "
            f"**{desconto}% de desconto**! Válido até {promo['validade']}."
        )
    else:
        lines.append("> Nenhuma promoção ativa no momento.")
    lines.append("")
    lines.append("---")

    return "\n".join(lines)


# ─── /desafio ────────────────────────────────────────────────────────────────

_NIVEIS_VALIDOS = {"basico", "básico", "intermediario", "intermediário", "avancado", "avançado"}
_NIVEL_PADRAO = "Intermediário"

_XP_POR_NIVEL = {
    "basico": 200,
    "básico": 200,
    "intermediario": 800,
    "intermediário": 800,
    "avancado": 1800,
    "avançado": 1800,
}

_TIPOS_POR_NIVEL = {
    "basico": ["Algoritmo", "Manipulação de Strings", "Estrutura de Laço"],
    "básico": ["Algoritmo", "Manipulação de Strings", "Estrutura de Laço"],
    "intermediario": ["Estrutura de Dados", "Orientação a Objetos", "Consumo de API"],
    "intermediário": ["Estrutura de Dados", "Orientação a Objetos", "Consumo de API"],
    "avancado": ["Design Pattern", "Concorrência/Async", "Algoritmo de Grafos"],
    "avançado": ["Design Pattern", "Concorrência/Async", "Algoritmo de Grafos"],
}


def normalizar_nivel(nivel: str) -> tuple[str, bool]:
    """
    Normalise the *nivel* string.
    Returns ``(nivel_normalizado, usado_padrao)`` where *usado_padrao* is True
    when the input was not recognised and the default was applied.
    """
    lower = nivel.strip().lower()
    if lower in _NIVEIS_VALIDOS:
        return nivel.strip(), False
    return _NIVEL_PADRAO, True


def gerar_desafio(tecnologia: str, nivel: str) -> dict:
    """
    Generate a challenge dict for the given technology and difficulty level.
    The returned dict has the keys: tecnologia, nivel, tipo, xp, aviso_padrao.
    """
    nivel_norm, usado_padrao = normalizar_nivel(nivel)
    nivel_key = nivel_norm.lower()

    tipos = _TIPOS_POR_NIVEL.get(nivel_key, _TIPOS_POR_NIVEL["intermediário"])
    tipo = random.choice(tipos)
    xp = _XP_POR_NIVEL.get(nivel_key, 800)

    return {
        "tecnologia": tecnologia.strip(),
        "nivel": nivel_norm,
        "tipo": tipo,
        "xp": xp,
        "aviso_padrao": usado_padrao,
    }


def formatar_desafio(desafio: dict) -> str:
    """Render a desafio dict as a Markdown string."""
    aviso = (
        f"\n> ⚠️ Nível não reconhecido. Usando **{_NIVEL_PADRAO}** como padrão.\n"
        if desafio.get("aviso_padrao")
        else ""
    )
    return (
        f"{aviso}"
        f"# ⚡ Desafio DIO — {desafio['tecnologia']} · Nível {desafio['nivel']}\n\n"
        f"**🎯 Tipo:** {desafio['tipo']}  \n"
        f"**⭐ XP ao concluir:** {desafio['xp']} XP  \n"
    )


# ─── /certificado ────────────────────────────────────────────────────────────


def _gerar_codigo_verificacao() -> str:
    """Return a random 12-character alphanumeric uppercase verification code."""
    chars = string.ascii_uppercase + string.digits
    return "DIO-" + "".join(random.choices(chars, k=12))


def buscar_trilha_para_certificado(nome_trilha: str, trilhas: list[dict]) -> Optional[dict]:
    """
    Find a trilha by name or tecnologia (case-insensitive partial match).
    Returns the first match or None if not found.
    """
    termo = nome_trilha.strip().lower()
    # Try by name first
    for t in trilhas:
        if termo in t["nome"].lower():
            return t
    # Fallback to tecnologia
    for t in trilhas:
        if termo in t["tecnologia"].lower():
            return t
    return None


def gerar_certificado(nome_aluno: str, trilha: dict) -> dict:
    """
    Generate a certificate dict for the given student and trilha.
    """
    return {
        "nome_aluno": nome_aluno.strip(),
        "trilha": trilha["nome"],
        "tecnologia": trilha["tecnologia"],
        "nivel": trilha["nivel"],
        "numero_modulos": trilha["numero_modulos"],
        "xp_total": trilha["xp_total"],
        "vitalicio": trilha.get("vitalicio", False),
        "badges": trilha.get("badges_disponiveis", []),
        "codigo_verificacao": _gerar_codigo_verificacao(),
        "emitido_em": date.today().strftime("%d/%m/%Y"),
    }


def formatar_certificado(cert: dict) -> str:
    """Render a certificate dict as a Markdown string."""
    vitalicio_str = "Sim ♾️" if cert["vitalicio"] else "Não ❌"
    badges_lines = "\n".join(f"- ✅ {b}" for b in cert["badges"])

    return (
        "# 🏆 Certificado de Conclusão\n\n"
        f"**Certificamos que**\n\n"
        f"## {cert['nome_aluno']}\n\n"
        "concluiu com êxito a trilha de aprendizado:\n\n"
        "---\n\n"
        f"## 🎯 {cert['trilha']}\n\n"
        f"| Campo | Detalhes |\n"
        f"|---|---|\n"
        f"| **Tecnologia** | {cert['tecnologia']} |\n"
        f"| **Nível** | {cert['nivel']} |\n"
        f"| **Módulos Concluídos** | {cert['numero_modulos']} de {cert['numero_modulos']} ✅ |\n"
        f"| **XP Conquistado** | {cert['xp_total']} XP ⭐ |\n"
        f"| **Acesso Vitalício** | {vitalicio_str} |\n\n"
        "---\n\n"
        "## 🏅 Badges Conquistadas\n\n"
        f"{badges_lines}\n\n"
        "---\n\n"
        "## 📜 Informações do Certificado\n\n"
        f"| Campo | Valor |\n"
        f"|---|---|\n"
        f"| **Emitido em** | {cert['emitido_em']} |\n"
        f"| **Código de Verificação** | {cert['codigo_verificacao']} |\n"
        f"| **Plataforma** | Digital Innovation One |\n"
        f"| **Validade** | Vitalício |\n"
    )
