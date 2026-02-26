import pandas as pd
from fuzzywuzzy import fuzz

csv_dados = 'chatbot_app/static/dados/Medicamentos - unificado.csv'

def procura_palavra_exata(df: pd.DataFrame, palavra: str, coluna: str):
    """Retorna todas as linhas do dataframe em que a palavra aparece na coluna

    Args:
        df (pd.DataFrame): DataFrame a ser filtrado
        palavra (str): Palavra a ser buscada
        coluna (str): Coluna onde a busca será feita

    Returns:
        pd.DataFrame: DataFrame filtrado
    """

    return df[df[coluna].astype(str).str.contains(palavra, case=False, na=False)]

def procura_palavra_semelhante(df: pd.DataFrame, palavra: str, coluna: str, threshold=60):
    """Retorna todas as linhas do dataframe em que a palavra é semelhante ao valor na coluna

    Args:
        df (pd.DataFrame): DataFrame a ser filtrado
        palavra (str): Palavra a ser buscada
        coluna (str): Coluna onde a busca será feita
        threshold (float, optional): Similaridade. Valor entre 0 e 1
    """
    palavra_lower = palavra.lower()
    mask = df[coluna].astype(str)

    mask = mask.apply(
        lambda x: (
            fuzz.partial_ratio(str(x).lower(), palavra_lower) >= threshold
            and str(x).lower() != palavra_lower
        )
    )

    return df[mask]

def retorna_palavra_mais_semelhante(df: pd.DataFrame, palavra: str, coluna: str, threshold=60):

    palavra_lower = palavra.lower()

    scores = df[coluna].astype(str).apply(
        lambda x: fuzz.partial_ratio(str(x).lower(), palavra_lower)
    )

    max_score = scores.max()

    if max_score >= threshold:
        return df[scores == max_score]

    return df.iloc[0:0]

def buscar_csv(texto, coluna):
    """_summary_

    Args:
        texto (_type_): _description_
        coluna (_type_): _description_

    Returns:
        dict: Dicionário de dataframes, 'resultados_exatos' e 'resultados_semelhantes'
    """
    df = pd.read_csv(csv_dados)

    return_dict = dict()

    texto = texto.replace(" ", "")

    return_dict['resultados_exatos'] = procura_palavra_exata(df, texto, coluna)

    return_dict['resultados_semelhantes'] = retorna_palavra_mais_semelhante(df, texto, coluna)

    return return_dict

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
    """
    Transforma o DataFrame filtrado em uma string amigável para o chat.
    """

    linhas_formatadas = []

    for _, row in df.iterrows():
            medicamento_nome = row.get('MEDICAMENTO')
            descricao = row.get('INFORMAÇÕES ADICIONAIS')

            item_texto = f" **Medicamento: {medicamento_nome}**\n {descricao}"
            linhas_formatadas.append(item_texto)

    introducao = "Encontrei as seguintes informações:\n\n"
    return introducao + "\n\n".join(linhas_formatadas)

def formata_resposta_medicamento(df: pd.DataFrame):
    """
    Transforma o DataFrame filtrado em uma string amigável para o chat.
    """

    linhas_formatadas = []

    for _, row in df.iterrows():
            cid_nome = row.get('CID')
            descricao = row.get('INFORMAÇÕES ADICIONAIS')

            item_texto = f" **CID: {cid_nome}**\n {descricao}"
            linhas_formatadas.append(item_texto)

    introducao = "Encontrei as seguintes informações:\n\n"
    return introducao + "\n\n".join(linhas_formatadas)

def buscando_com_cid(text):
    dict_filtros = buscar_csv(text, 'CID')

    if not dict_filtros['resultados_exatos'].empty:
        resultado = dict_filtros['resultados_exatos']
        resultado.drop_duplicates(inplace=True)
        resultado.drop_duplicates(subset='MEDICAMENTO', inplace=True)

    else:
        resultado = pd.DataFrame()


    return resultado

def buscando_com_nome_medicamento(text):
    dict_filtros = buscar_csv(text, 'MEDICAMENTO')

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

    # Retorna dict com o df + tipo de match + nome encontrado
    return {
        "df": resultado,
        "match_type": match_type,
        "nome_encontrado": resultado.iloc[0]['MEDICAMENTO']
    }

def buscando_endereco(nome_medicamento):
    dict_filtros = buscar_csv(nome_medicamento, 'MEDICAMENTO')

    if not dict_filtros['resultados_exatos'].empty:
        resultado = dict_filtros['resultados_exatos']
        resultado.drop_duplicates(inplace=True)
        match_type = 'exato'
    elif dict_filtros['resultados_semelhantes'].empty:
        return {"erro": "Desculpe, não consegui encontrar informações sobre esse medicamento."}
    else:
        resultado = dict_filtros['resultados_semelhantes']
        match_type = 'semelhante'

    linha = resultado.iloc[0]
    a = str(linha['LOCAL_DE_DISPENSACAO'])

    if a == 'nan':
        locais = ['ESPECIAIS']
    else:
        locais = linha[linha == 1].index.tolist()

    conjunto_traduzido = tradutor_csv_enderecos(locais)

    return {
        "medicamento": linha['MEDICAMENTO'],
        "locais": conjunto_traduzido,
        "match_type": match_type,
    }