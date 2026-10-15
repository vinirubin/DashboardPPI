from decimal import Decimal
from math import isfinite
from numbers import Real


def formatar_moeda_brasileira(valor: object) -> str:
    """Formata valor numérico como moeda brasileira."""
    if isinstance(valor, bool) or not isinstance(valor, (Real, Decimal)):
        return "R$ 0,00"
    try:
        if not isfinite(valor):
            return "R$ 0,00"
    except (OverflowError, TypeError, ValueError):
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
