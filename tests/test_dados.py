from io import BytesIO, StringIO

import pandas as pd
import pytest

from utils.dados import ErroDados, ler_cadastro, ler_vendas


def test_preserva_codigos_totais_datas_e_posicao(vendas_csv):
    fonte = StringIO(vendas_csv)
    fonte.seek(10)
    df = ler_vendas(fonte)
    assert fonte.tell() == 10
    assert df.ProCod.tolist() == ["001", "002", "001", "004"]
    assert df.Cliente.iloc[0] == "0007"
    assert df.TotalItem.sum() == pytest.approx(47.75)
    assert df.Data.iloc[0] == pd.Timestamp("2024-12-31")
    assert df.Data.iloc[1] == pd.Timestamp("2024-12-31")
    assert df.Data.iloc[2] == pd.Timestamp("2025-01-01")


@pytest.mark.parametrize("valor", ["abc", "1,50", "inf", "-inf", "NaN", "", "1e400"])
@pytest.mark.parametrize("coluna", ["Quantidade", "TotalItem"])
def test_rejeita_numeros_invalidos(valor, coluna):
    registro = {"Quantidade": "1", "TotalItem": "2.50"}
    registro[coluna] = valor
    fonte = StringIO(
        "ProCod;Quantidade;TotalItem;Data;Controle;Cliente\n"
        f"001;{registro['Quantidade']};{registro['TotalItem']};2025-01-01;A;7\n"
    )
    with pytest.raises(ErroDados, match=coluna):
        ler_vendas(fonte)


@pytest.mark.parametrize("valor", ["31/02/2025", "", "segredo-invalido"])
def test_data_invalida_nao_e_descartada_ou_exposta(vendas_csv, valor):
    with pytest.raises(ErroDados) as exc:
        ler_vendas(StringIO(vendas_csv.replace("2025-01-01", valor)))
    assert "Nenhuma linha foi descartada" in str(exc.value)
    assert "segredo" not in str(exc.value)


def test_bairro_opcional_e_cliente_ausente(vendas_csv):
    linhas = vendas_csv.splitlines()
    sem_bairro = "\n".join(";".join(linha.split(";")[:-1]) for linha in linhas)
    df = ler_vendas(StringIO(sem_bairro.replace(";0007", ";")))
    assert df.Bairro.isna().all()
    assert pd.isna(df.Cliente.iloc[0])


@pytest.mark.parametrize("csv", ["", "ProCod;ProNom\n", "Outra\n1\n"])
def test_arquivo_vazio_ou_sem_esquema(csv):
    with pytest.raises(ErroDados):
        ler_cadastro(StringIO(csv))


def test_cadastro_deduplica_sem_multiplicar(cadastro_csv):
    df = ler_cadastro(StringIO(cadastro_csv + "001;Arroz;Alimento\n"))
    assert len(df) == 3
    assert "Categoria" in df


def test_cadastro_conflitante_e_rejeitado(cadastro_csv):
    with pytest.raises(ErroDados, match="conflitantes"):
        ler_cadastro(StringIO(cadastro_csv + "001;Outro;Alimento\n"))


@pytest.mark.parametrize("linha", [";Produto", "001;"])
def test_cadastro_com_identidade_vazia(linha):
    with pytest.raises(ErroDados, match="vazios"):
        ler_cadastro(StringIO("ProCod;ProNom\n" + linha))


def test_erro_leitura_nao_expoe_caminho(tmp_path):
    with pytest.raises(ErroDados) as exc:
        ler_vendas(tmp_path / "cliente-confidencial.csv")
    assert "cliente-confidencial" not in str(exc.value)


def test_utf8_bom_e_valores_textuais_na(tmp_path):
    arquivo = tmp_path / "cadastro.csv"
    arquivo.write_text("ProCod;ProNom\nNA;N/A\n", encoding="utf-8-sig")
    assert ler_cadastro(arquivo).iloc[0].tolist() == ["NA", "N/A"]


def test_bytes_invalidos():
    with pytest.raises(ErroDados):
        ler_cadastro(BytesIO(b"ProCod;ProNom\n1;\xff\n"))


def test_nomes_colunas_colidem_apos_strip():
    with pytest.raises(ErroDados, match="duplicados"):
        ler_cadastro(StringIO("ProCod; ProCod ;ProNom\n1;1;A\n"))


def test_devolucoes_negativas_sao_preservadas(vendas_csv):
    df = ler_vendas(StringIO(vendas_csv.replace("2;10.50", "-2;-10.50")))
    assert df.Quantidade.iloc[0] == -2
    assert df.TotalItem.iloc[0] == -10.5


@pytest.mark.parametrize("valor", ["2025-13-01", "01/13/2025", "2025-01-01T12:00:00Z", "01/02/25"])
def test_data_nao_reinterpreta_formato_invalido(vendas_csv, valor):
    with pytest.raises(ErroDados, match="data"):
        ler_vendas(StringIO(vendas_csv.replace("2025-01-01", valor)))


@pytest.mark.parametrize("valor", ["2025-01-03", "03/01/2025", "03/01/2025 14:30:00"])
def test_data_dia_mes_nao_ambiguos(vendas_csv, valor):
    df = ler_vendas(StringIO(vendas_csv.replace("2025-01-01", valor)))
    assert df.Data.iloc[2].month == 1
    assert df.Data.iloc[2].day == 3


def test_colunas_exatamente_duplicadas():
    with pytest.raises(ErroDados, match="duplicados"):
        ler_cadastro(StringIO("ProCod;ProNom;ProNom\n1;A;B\n"))


def test_registro_com_campos_excedentes_nao_perde_dados():
    with pytest.raises(ErroDados, match="mais campos"):
        ler_cadastro(StringIO("ProCod;ProNom\nextra;1;A\n"))


def test_fluxo_nao_reposicionavel_tem_erro_claro():
    class Fluxo(StringIO):
        def seekable(self):
            return False

    with pytest.raises(ErroDados, match="reposicionamento"):
        ler_cadastro(Fluxo("ProCod;ProNom\n1;A\n"))
