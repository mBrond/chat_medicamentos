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
    text = data.text.lower().strip()
    if len(text) >= 3 and len(text) <= 5:
        return True
    
    return False

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
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    req = None
    if tipo == 'conversation':
        req = validar_chat_request(data)
    else:
        return JsonResponse({"detail": f"Tipo de requisição desconhecido: {tipo}"}, status=400)
        
    return req


