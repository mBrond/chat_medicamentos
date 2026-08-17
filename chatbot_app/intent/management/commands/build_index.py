"""
Uso: python manage.py build_index

Reconstrói do zero o índice vetorial (Chroma) a partir do CSV de
medicamentos. Rode sempre que o CSV for atualizado — o índice NÃO
se atualiza sozinho.
"""
from django.core.management.base import BaseCommand
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from chatbot_app.rag import config
from chatbot_app.rag.indexer import load_documents


class Command(BaseCommand):
    help = "Reconstrói o índice vetorial (Chroma) a partir do CSV de medicamentos."

    def handle(self, *args, **options):
        self.stdout.write("Verificando conexão com Ollama...")
        embeddings = OllamaEmbeddings(
            model=config.EMBEDDING_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )

        self.stdout.write("Carregando documentos do CSV...")
        docs = load_documents()
        self.stdout.write(f"{len(docs)} documentos carregados.")

        vectorstore = Chroma(
            embedding_function=embeddings,
            persist_directory=str(config.CHROMA_PERSIST_DIR),
            collection_name=config.COLLECTION_NAME,
        )

        # Limpa a coleção antes de reindexar do zero, para não acumular
        # linhas fantasmas de versões antigas do CSV.
        try:
            vectorstore.delete_collection()
        except Exception:
            pass

        vectorstore = Chroma(
            embedding_function=embeddings,
            persist_directory=str(config.CHROMA_PERSIST_DIR),
            collection_name=config.COLLECTION_NAME,
        )

        batch_size = 100
        total = len(docs)
        for i in range(0, total, batch_size):
            lote = docs[i:i + batch_size]
            vectorstore.add_documents(lote, ids=[d.id for d in lote])
            self.stdout.write(f"  indexado {min(i + batch_size, total)}/{total}")

        self.stdout.write(self.style.SUCCESS("Índice reconstruído com sucesso."))