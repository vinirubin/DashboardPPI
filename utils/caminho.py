"""Resolução de caminhos independente do diretório de execução."""

from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]


def resolver_caminho(path: str | Path) -> Path:
    caminho = Path(path).expanduser()
    return caminho if caminho.is_absolute() else RAIZ_PROJETO / caminho


def caminho_valido(path: object) -> bool:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        return False
    try:
        return resolver_caminho(path).is_file()
    except (OSError, ValueError):
        return False
