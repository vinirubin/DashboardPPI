import streamlit as st

from utils.sessao import inicializar_app, salvar_caminhos

st.set_page_config(page_title="Configurar Caminhos", layout="wide")
inicializar_app()
st.title("🗂️ Configuração de Caminhos de Arquivos")
st.markdown(
    "Informe caminhos dos arquivos locais do servidor. Caminhos relativos partem da "
    "raiz do projeto. Salvar também recarrega arquivos alterados no mesmo caminho."
)
with st.form("configurar_arquivos"):
    caminho_vendas = st.text_input(
        "📄 Caminho do Arquivo de Vendas", value=st.session_state["caminho_vendas"]
    )
    caminho_cadastro = st.text_input(
        "📦 Caminho do Arquivo de Cadastro", value=st.session_state["caminho_cadastro"]
    )
    submit = st.form_submit_button("💾 Salvar Caminhos")

if submit and salvar_caminhos(caminho_vendas, caminho_cadastro):
    st.success("Arquivos validados e recarregados com sucesso nesta sessão.")

st.markdown("### 🔍 Caminhos atuais carregados")
st.text(f"Arquivo de Vendas: {st.session_state['caminho_vendas']}")
st.text(f"Arquivo de Cadastro: {st.session_state['caminho_cadastro']}")
