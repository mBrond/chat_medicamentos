import json

from django.http import JsonResponse
from django.shortcuts import render
from .validacoes import validar_request
from django.views.decorators.csrf import csrf_exempt

from .services import buscando_com_cid, formata_resposta_cid, buscando_com_nome_medicamento, formata_resposta_medicamento, buscando_endereco

@csrf_exempt
def landing_page(request):
    return render(request, 'index.html', {})

@csrf_exempt
def health_check(request):
    """
    Endpoint de health check (GET)
    """
    return JsonResponse({"status": "ok"})

@csrf_exempt
def conversation(request):
    """Controla as mensagens que serão mostradas no chat

    Args:
        request (_type_): _description_

    Returns:
        JsonResponse: _description_
    """
    req = validar_request(request, 'conversation')
    if type(req) == JsonResponse: #requisicao invalida
        return req
    
    if req.intent.lower() == 'cid':
        df_dados = buscando_com_cid(req.text)
        resposta_chat_str = formata_resposta_cid(df_dados)

    elif req.intent.lower() == 'medicamento':
        df_dados = buscando_com_nome_medicamento(req.text)
        resposta_chat_str = formata_resposta_medicamento(df_dados)

    elif req.intent.lower() == 'onde retirar medicamento':
        dict_enderecos = buscando_endereco(req.text)
        nome_medicamento_buscado = dict_enderecos['medicamento']
        conjunto_farmacia = dict_enderecos['locais']

        with open('chatbot_app/static/dados/enderecos.json', 'r', encoding='utf-8') as f:
            enderecos = json.load(f)

        marcadores_formatados = []

        for farmacia in conjunto_farmacia:
            info = enderecos.get(farmacia)
            if info:
                marcadores_formatados.append({
                "nome": farmacia,
                "lat": info['marker'][0],
                "lng": info['marker'][1],
                "endereco": info.get('endereco', "Endereço não informado"),
                "imagem": info.get('imagem', None)
            })
                
                
        if not marcadores_formatados:
            return JsonResponse({"error": "Nenhum local encontrado com coordenadas"})

        

        return JsonResponse({'map_data': {
            "center": [marcadores_formatados[0]["lat"], marcadores_formatados[0]["lng"]],
            "markers": marcadores_formatados
        }})
    

    return JsonResponse({"answer": resposta_chat_str})