from io import BytesIO

import pandas as pd
from pandas.testing import assert_frame_equal

from utils.exportacao import gerar_csv_seguro


def test_csv_neutraliza_formulas_preserva_numeros_e_dataframe():
    perigosos = ["=1+1", "+CMD", "-CMD", "@SUM(1)", "  =2", "\t=3", "\r=4", "\n=5", "＝1"]
    df = pd.DataFrame({"=cabecalho": perigosos, "numero": [-10.5] * len(perigosos)})
    original = df.copy(deep=True)
    arquivo = gerar_csv_seguro(df)
    assert arquivo.startswith(b"\xef\xbb\xbf")
    leitura = pd.read_csv(BytesIO(arquivo))
    assert leitura.columns[0] == "'=cabecalho"
    assert leitura.iloc[:, 0].tolist() == ["'" + valor for valor in perigosos]
    assert leitura.numero.eq(-10.5).all()
    assert_frame_equal(df, original)


def test_csv_strings_categorias_e_nulos():
    df = pd.DataFrame(
        {
            "texto": pd.Series(["Feijão", "=1", None], dtype="string"),
            "categoria": pd.Categorical(["@abc", "normal", None]),
        }
    )
    leitura = pd.read_csv(BytesIO(gerar_csv_seguro(df)))
    assert leitura.texto.iloc[:2].tolist() == ["Feijão", "'=1"]
    assert leitura.categoria.iloc[0] == "'@abc"
    assert pd.isna(leitura.texto.iloc[2])
