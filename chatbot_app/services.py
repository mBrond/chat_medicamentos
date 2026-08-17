import pandas as pd

from .rag import config as rag_config
from .rag.retriever import busca_exata, busca_semantica, resultados_semanticos_para_df

csv_dados = 'chatbot_app/static/dados/Medicamentos - unificado.csv'


def buscar_csv_hibrido(texto: str, coluna: str) -> dict:
    """
    Substitui a antiga buscar_csv(). Faz busca exata em pandas primeiro
    (rápida e determinística); se não achar nada, cai para busca
    semântica via embeddings (Chroma), no lugar do thefuzz.

    Returns:
        dict: {'resultados_exatos': DataFrame, 'resultados_semelhantes': DataFrame}
    """
    df = pd.read_csv(csv_dados)
    texto_limpo = texto.replace(" ", "")

    resultados_exatos = busca_exata(df, texto_limpo, coluna)

    resultados_semelhantes = pd.DataFrame()
    if resultados_exatos.empty:
        candidatos = busca_semantica(texto)  # usa o texto original, não o "colado"
        resultados_semelhantes = resultados_semanticos_para_df(candidatos)

    return {
        "resultados_exatos": resultados_exatos,
        "resultados_semelhantes": resultados_semelhantes,
    }


def tradutor_csv_enderecos(lista):
    """Recebe uma lista com o escopo regional de farmácias e mapeia elas para localização dentro do arquivo enderecos.json

    Args:
        lista (list): Contém 'DISTRITAIS', 'MUNICIPAL'

    Returns:
        set: Conjunto com nome de farmácias
    """
    conjunto_traduzido = set()

    if 'DISTRITAIS' in lista:
        conjunto_traduzido.add('FARMÁCIA DISTRITAL CAMOBI')
        conjunto_traduzido.add('FARMÁCIA DISTRITAL TANCREDO NEVES')
        conjunto_traduzido.add('FARMÁCIA DISTRITAL FLORIANO ROCHA')
        conjunto_traduzido.add('FARMÁCIA DISTRITAL KENNEDY')
        conjunto_traduzido.add('FARMÁCIA DISTRITAL SÃO FRANCISCO')
        conjunto_traduzido.add('FARMÁCIA DISTRITAL ESTAÇÃO DOS VENTOS')

    if 'MUNICIPAL' in lista:
        conjunto_traduzido.add('FARMÁCIA MUNICIPAL CENTRAL')

    if 'ESPECIAIS' in lista:
        conjunto_traduzido.add('FARMÁCIA DE MEDICAMENTOS ESPECIAIS')

    return conjunto_traduzido


def formata_resposta_cid(df: pd.DataFrame):
    linhas_formatadas = []
    for _, row in df.iterrows():
        medicamento_nome = row.get('MEDICAMENTO')
        descricao = row.get('INFORMAÇÕES ADICIONAIS')
        item_texto = f" **Medicamento: {medicamento_nome}**\n {descricao}"
        linhas_formatadas.append(item_texto)

    introducao = "Encontrei as seguintes informações:\n\n"
    return introducao + "\n\n".join(linhas_formatadas)


def formata_resposta_medicamento(df: pd.DataFrame):
    linhas_formatadas = []
    for _, row in df.iterrows():
        cid_nome = row.get('CID')
        descricao = row.get('INFORMAÇÕES ADICIONAIS')

        if pd.isna(cid_nome) or cid_nome == "":
            cid_nome = 'Sem CID cadastrado para o medicamento.'
        if pd.isna(descricao) or descricao == "":
            descricao = 'Sem informação extra cadastrada para o medicamento.'

        item_texto = f" **CID: {cid_nome}**\n {descricao}"
        linhas_formatadas.append(item_texto)

    introducao = "Encontrei as seguintes informações:\n\n"
    return introducao + "\n\n".join(linhas_formatadas)


def buscando_com_cid(text):
    dict_filtros = buscar_csv_hibrido(text, 'CID')

    if not dict_filtros['resultados_exatos'].empty:
        resultado = dict_filtros['resultados_exatos']
        resultado.drop_duplicates(inplace=True)
        resultado.drop_duplicates(subset='MEDICAMENTO', inplace=True)
    elif not dict_filtros['resultados_semelhantes'].empty:
        resultado = dict_filtros['resultados_semelhantes']
        resultado.drop_duplicates(subset='MEDICAMENTO', inplace=True)
    else:
        resultado = pd.DataFrame()

    return resultado


def buscando_com_nome_medicamento(text):
    dict_filtros = buscar_csv_hibrido(text, 'MEDICAMENTO')

    if not dict_filtros['resultados_exatos'].empty:
        resultado = dict_filtros['resultados_exatos']
        resultado.drop_duplicates(inplace=True)
        match_type = 'exato'
    elif dict_filtros['resultados_semelhantes'].empty:
        return {"erro": "Desculpe, não consegui encontrar informações sobre esse medicamento."}
    else:
        resultado = dict_filtros['resultados_semelhantes']
        match_type = 'semelhante'

    resultado.drop_duplicates(subset='CID', inplace=True)

    if resultado.empty:
        return {"erro": "Desculpe, não consegui encontrar informações sobre esse medicamento."}

    return {
        "df": resultado,
        "match_type": match_type,
        "nome_encontrado": resultado.iloc[0]['MEDICAMENTO']
    }


def buscando_endereco(nome_medicamento):
    dict_filtros = buscar_csv_hibrido(nome_medicamento, 'MEDICAMENTO')

    if not dict_filtros['resultados_exatos'].empty:
        resultado = dict_filtros['resultados_exatos']
        resultado.drop_duplicates(inplace=True)
        match_type = 'exato'
    elif dict_filtros['resultados_semelhantes'].empty:
        return {"erro": "Desculpe, não consegui encontrar informações sobre esse medicamento."}
    else:
        resultado = dict_filtros['resultados_semelhantes']
        match_type = 'semelhante'

    if resultado.empty:
        return {"erro": "Desculpe, não consegui encontrar informações sobre esse medicamento."}

    linha = resultado.iloc[0]
    a = str(linha['LOCAL_DE_DISPENSACAO'])

    if a == 'nan' or a == '':
        locais = ['ESPECIAIS']
    else:
        locais = [col for col in rag_config.COLUNAS_LOCAIS if linha.get(col) == 1]

    conjunto_traduzido = tradutor_csv_enderecos(locais)

    return {
        "medicamento": linha['MEDICAMENTO'],
        "locais": conjunto_traduzido,
        "match_type": match_type,
    }