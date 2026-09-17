import re
import unicodedata

# Padrões para captura de intenção
PATTERNS_ONDE_RETIRAR = [
    r"(?:onde|qual\s+posto|qual\s+farmacia|como|aonde)\s+(?:posso|consigo|consigo\s+encontrar)?\s*(?:retirar|pegar|encontrar|achar|tem|comprar)\s+(?:o|a|os|as)?\s*(.+)",
    r"(?:onde\s+tem|onde\s+fica|tem|onde\0encontro)\s+(?:o|a|os|as)?\s*(.+)",
    r"(?:locais|pontos)\s+de\s+(?:retirada|entrega)\s+(?:do|da|de)?\s*(.+)",
]

PATTERNS_CID = [
    r"(?:cid|codigo|doenca|diagnostico)\s+(?:do|da|para|de)?\s*(.+)",
    r"^([a-zA-Z]\d{2}(?:\.\d{1,2})?)$",  # Padrão numérico de CID (ex: M79.1)
]

PATTERNS_INFO_MEDICAMENTO = [
    r"(?:para\s+que\s+serve|informacoesp?|bula|como\s+tomar|detalhes|oque\s+e)\s+(?:o|a|os|as|do|da|de)?\s*(.+)",
    r"(?:sobre\s+o|sobre\s+a)\s*(.+)",
]

# Palavras de ruído comuns para remover da entidade capturada
NOISE_WORDS = [
    r"\bpor\s+favor\b",
    r"\bagora\b",
    r"\bhoje\b",
    r"\bgentileza\b",
    r"\bpra\s+mim\b",
    r"\bno\s+posto\b",
]

def remover_acentos(texto: str) -> str:
    """Remove acentos mantendo o texto em minúsculas."""
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn').lower()

def limpar_entidade(entidade: str) -> str:
    """Remove pontuações e palavras de ruído no final/inicio da entidade."""
    texto = re.sub(r'[?\.!;,]+$', '', entidade).strip()
    
    for noise in NOISE_WORDS:
        texto = re.sub(noise, '', texto, flags=re.IGNORECASE).strip()
        
    return texto

def extrair_intencao_e_entidade(mensagem: str) -> dict:
    texto_raw = mensagem.strip()
    texto_norm = remover_acentos(texto_raw)

    # 1. Checa busca por CID
    for pattern in PATTERNS_CID:
        match = re.search(pattern, texto_norm, re.IGNORECASE)
        if match:
            entidade = limpar_entidade(match.group(1))
            return {
                "intent": "cid",
                "termo": entidade,  # Padronizado para 'termo'
                "texto_original": mensagem,
            }

    # 2. Checa intenção de "Onde Retirar"
    for pattern in PATTERNS_ONDE_RETIRAR:
        match = re.search(pattern, texto_norm, re.IGNORECASE)
        if match:
            entidade = limpar_entidade(match.group(1))
            return {
                "intent": "onde_retirar",
                "termo": entidade,  # Padronizado para 'termo'
                "texto_original": mensagem,
            }

    # 3. Checa intenção de Informações sobre Medicamento
    for pattern in PATTERNS_INFO_MEDICAMENTO:
        match = re.search(pattern, texto_norm, re.IGNORECASE)
        if match:
            entidade = limpar_entidade(match.group(1))
            return {
                "intent": "medicamento",
                "termo": entidade,  # Padronizado para 'termo'
                "texto_original": mensagem,
            }

    # 4. Fallback: Assume que o texto completo pode ser o nome do medicamento
    entidade_limpa = limpar_entidade(texto_norm)
    return {
        "intent": "medicamento",
        "termo": entidade_limpa,  # Padronizado para 'termo'
        "texto_original": mensagem,
    }