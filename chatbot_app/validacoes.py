from pydantic import BaseModel
from django.http import JsonResponse
import json

class ChatRequest(BaseModel):
    text: str
    intent: str


def validar_chat_request(data):
    try:
        chat_request = ChatRequest(**data)
        return chat_request
    except Exception as e:
        
        return JsonResponse({"detail": "Dados de entrada inválidos.", "error": str(e)}, status=400)


def validar_intent_cid(data:ChatRequest):
    campo_intent = data.intent.lower().strip()
    
    if len(campo_intent) <=3 or len(campo_intent) > 5:
        return "Tamanho cid inválido"
    
    return "ok"

def validar_request(request, tipo): 
    """_summary_

    Args:
        request (_type_): _description_
        tipo (str): tipo de request a ser validado

    Returns:
        _type_: _description_
    """
    if request.method != 'POST':
        return JsonResponse({"detail": "Método não permitido."}, status=405)
    
    data = json.loads(request.body)

    if tipo =='conversation':
        req = validar_chat_request(data)
        
    return req


