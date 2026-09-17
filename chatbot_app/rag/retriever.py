"""
Substitui procura_palavra_semelhante/retorna_palavra_mais_semelhante (thefuzz)
por uma busca semântica via embeddings. A busca EXATA continua em pandas
(é barata, 100% confiável e não precisa de LLM/rede).

Regras de negócio deste módulo:
  1) Tenta match exato (substring) primeiro — igual ao comportamento atual.
  2) Se não achar, cai para busca semântica no Chroma.
  3) Resultados semânticos abaixo do threshold de similaridade são descartados
     (evita "match_type: semelhante" para coisas completamente diferentes).
"""
import functools

import pandas as pd
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from . import config


@functools.lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(
        model=config.EMBEDDING_MODEL,
        base_url=config.OLLAMA_BASE_URL,
    )
    return Chroma(
        embedding_function=embeddings,
        persist_directory=str(config.CHROMA_PERSIST_DIR),
        collection_name=config.COLLECTION_NAME,
    )


def busca_exata(df: pd.DataFrame, texto: str, coluna: str) -> pd.DataFrame:
    """Mesma lógica de procura_palavra_exata em services.py."""
    return df[df[coluna].astype(str).str.contains(texto, case=False, na=False)]


def busca_semantica(texto: str, k: int = 5) -> list[dict]:
    """
    Busca vetorial no Chroma. Retorna uma lista de dicts com o metadata
    de cada Document (equivalente a uma "linha do CSV"), já ordenados por
    relevância e filtrados pelo threshold de distância.

    Cada dict tem as mesmas chaves usadas hoje pelo pandas: medicamento,
    cid, informacoes_adicionais, local_de_dispensacao + colunas de local.
    """
    vectorstore = get_vectorstore()
    resultados = vectorstore.similarity_search_with_score(texto, k=k)

    candidatos = []
    for doc, distancia in resultados:
        if distancia > config.SIMILARITY_DISTANCE_THRESHOLD:
            continue
        candidatos.append(doc.metadata)

    return candidatos


def resultados_semanticos_para_df(candidatos: list[dict]) -> pd.DataFrame:
    """Reaproveita as funções de formatação de services.py, que esperam
    um DataFrame com colunas MEDICAMENTO/CID/INFORMAÇÕES ADICIONAIS."""
    if not candidatos:
        return pd.DataFrame()

    linhas = []
    for c in candidatos:
        linhas.append({
            "MEDICAMENTO": c.get("medicamento", ""),
            "CID": c.get("cid", ""),
            "INFORMAÇÕES ADICIONAIS": c.get("informacoes_adicionais", ""),
            "LOCAL_DE_DISPENSACAO": c.get("local_de_dispensacao", ""),
            **{col: c.get(col, 0) for col in config.COLUNAS_LOCAIS},
        })

    return pd.DataFrame(linhas)