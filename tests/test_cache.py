from io import BytesIO

import pandas as pd

from utils.cache import assinatura_dataframe, cache_calculo
from utils.exportacao import gerar_csv_seguro


def test_alteracao_fora_da_amostra_invalida_exportacao():
    df = pd.DataFrame({"valor": range(60000)})
    nao_amostrado = df.index.difference(df.sample(n=10000, random_state=0).index)[0]
    exportar = cache_calculo(gerar_csv_seguro)
    exportar.clear()
    antes = exportar(df)
    df.loc[nao_amostrado, "valor"] = -123
    depois = exportar(df)
    assert antes != depois
    assert pd.read_csv(BytesIO(depois)).valor.iloc[nao_amostrado] == -123
    exportar.clear()


def test_assinatura_inclui_esquema_indice_e_todas_linhas():
    df = pd.DataFrame({"valor": [1, 2]})
    assinatura = assinatura_dataframe(df)
    assert assinatura == assinatura_dataframe(df.copy())
    assert assinatura != assinatura_dataframe(df.rename(columns={"valor": "outro"}))
    assert assinatura != assinatura_dataframe(df.astype(float))
    assert assinatura != assinatura_dataframe(df.set_axis([10, 20]))
