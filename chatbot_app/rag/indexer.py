"""
Converte o CSV de medicamentos em Documents do LangChain, prontos para
serem indexados no Chroma. Mantém em metadata tudo que services.py precisa
para reconstruir uma resposta (endereço, CID, etc.) sem reler o CSV.
"""
import pandas as pd
from langchain_core.documents import Document

from . import config


def _clean(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def csv_row_to_document(index: int, row: pd.Series) -> Document:
    medicamento = _clean(row.get("MEDICAMENTO"))
    cid = _clean(row.get("CID"))
    info = _clean(row.get("INFORMAÇÕES ADICIONAIS"))
    local_dispensacao = _clean(row.get("LOCAL_DE_DISPENSACAO"))

    # page_content é o que vira embedding — inclui tudo que o usuário pode
    # digitar (nome do remédio, código CID, e a descrição da condição/CID).
    page_content = (
        f"Medicamento: {medicamento}\n"
        f"CID: {cid}\n"
        f"Informações adicionais: {info}"
    )

    metadata = {
        "medicamento": medicamento,
        "cid": cid,
        "informacoes_adicionais": info,
        "local_de_dispensacao": local_dispensacao,
    }

    # Flags de local (0/1) viram metadata individual, exatamente como
    # buscando_endereco() usa hoje (linha[linha == 1].index.tolist()).
    for col in config.COLUNAS_LOCAIS:
        val = row.get(col)
        try:
            metadata[col] = int(val) if pd.notna(val) else 0
        except (ValueError, TypeError):
            metadata[col] = 0

    return Document(page_content=page_content, metadata=metadata, id=f"row-{index}")


def load_documents() -> list[Document]:
    df = pd.read_csv(config.CSV_PATH)
    return [csv_row_to_document(i, row) for i, row in df.iterrows()]