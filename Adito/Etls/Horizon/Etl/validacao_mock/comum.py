"""Funções compartilhadas pelo gerador de mocks e pelo validador.

As normalizações abaixo reproduzem as regras documentadas do ETL do Horizon
(casamento de pessoas, nomes de grupos/áreas/organizações), para que o gabarito
seja calculado sem importar o código que está sendo validado.
"""

import re
import unicodedata
from datetime import date, datetime
from typing import Any, Optional

PARTICULAS = {"DA", "DE", "DI", "DO", "DOS", "DAS", "DU", "DEL", "DELA"}


def sem_acento(valor: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", valor) if unicodedata.category(c) != "Mn"
    )


def normalizar_texto(valor: Any) -> str:
    """Mesma ideia do normalize_text do ETL: sem acento, minúsculo, só alfanumérico."""
    if valor is None:
        return ""
    texto = sem_acento(str(valor))
    texto = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in texto)
    return " ".join(texto.lower().split())


def chave_pessoa(nome: Optional[str]) -> str:
    """Chave canônica de nome de pessoa (regra do PersonMatcher)."""
    if not nome:
        return ""
    texto = re.sub(r"[^A-Z\s]", " ", sem_acento(nome).upper())
    tokens = [t if t not in PARTICULAS else t.lower() for t in texto.split()]
    return " ".join(tokens)


def data_br(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def iso(valor: Optional[Any]) -> Optional[str]:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def slug(valor: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", sem_acento(valor).lower())
