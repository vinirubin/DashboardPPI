import pandas as pd
import streamlit as st

from utils.cache import cache_calculo
from utils.exportacao import gerar_csv_seguro

LINHAS_POR_PAGINA = 100

csv_em_cache = cache_calculo(gerar_csv_seguro, max_entries=4)


def mostrar_paginado(df: pd.DataFrame, nome_df: str, linhas_por_pagina: int = LINHAS_POR_PAGINA):
    """Exibe DataFrame com paginação e botão de download."""
    if (
        isinstance(linhas_por_pagina, bool)
        or not isinstance(linhas_por_pagina, int)
        or linhas_por_pagina <= 0
    ):
        raise ValueError("linhas_por_pagina deve ser um inteiro positivo.")
    if df is None or df.empty:
        st.info(f"O DataFrame '{nome_df}' está vazio ou não foi carregado.")
        return

    total_linhas = len(df)
    num_paginas = (total_linhas - 1) // linhas_por_pagina + 1

    chave = f"pagina_{nome_df}"
    atual = st.session_state.get(chave, 1)
    st.session_state[chave] = max(1, min(int(atual), num_paginas))

    pagina = st.number_input(
        f"Página de visualização ({nome_df})", min_value=1, max_value=num_paginas, step=1, key=chave
    )

    inicio = (pagina - 1) * linhas_por_pagina
    fim = inicio + linhas_por_pagina
    st.dataframe(df.iloc[inicio:fim], width="stretch")
    st.caption(f"Exibindo linhas {inicio + 1} a {min(fim, total_linhas)} de {total_linhas}.")

    csv = csv_em_cache(df)
    st.download_button(
        label=f"📥 Baixar CSV completo ({nome_df})",
        data=csv,
        file_name=f"{nome_df}.csv",
        mime="text/csv",
        key=f"download_{nome_df}",
    )
