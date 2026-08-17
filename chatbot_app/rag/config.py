import os
from pathlib import Path

# chatbot_app/rag/config.py -> sobe dois níveis para achar a raiz do app
APP_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = APP_DIR / "static" / "dados" / "Medicamentos - unificado.csv"
CHROMA_PERSIST_DIR = APP_DIR / "rag" / "chroma_db"
COLLECTION_NAME = "medicamentos"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("RAG_EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.environ.get("RAG_LLM_MODEL", "llama3.2:3b")

# Colunas de local de dispensação (mesmas usadas hoje em services.py)
COLUNAS_LOCAIS = [
    "DISTRITAIS", "DISTRITAL TANCREDO NEVES",
    "DISTRITAL WILSON PAULO NOAL", "FARMÁCIAS DISTRITAIS",
    "MUNICIPAL", "POPULAR", "UBS",
]

# Quanto menor, mais rígido (Chroma usa distância; 0 = idêntico).
# Ajuste empiricamente rodando algumas buscas de teste.
SIMILARITY_DISTANCE_THRESHOLD = 0.65

# Liga/desliga a camada de geração via LLM (fase 3 da migração).
# Mantenha False até a etapa de retrieval estar validada em produção.
USE_LLM_GENERATION = os.environ.get("RAG_USE_LLM_GENERATION", "false").lower() == "true"