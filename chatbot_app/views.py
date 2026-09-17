import json

from django.http import JsonResponse
from django.shortcuts import render
from .validacoes import validar_request, validar_intent_cid
from django.views.decorators.csrf import csrf_exempt

from .services import buscando_com_cid, formata_resposta_cid, buscando_com_nome_medicamento, formata_resposta_medicamento, buscando_endereco

from .nlu import extrair_intencao_e_entidade

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
    req = validar_request(request, 'conversation')

    if type(req) == JsonResponse:
        return req

    # Obtém o texto e a intenção recebidos
    texto = req.text

    print("get intent")
    intent = getattr(req, 'intent', None)

    # 2. SE NÃO VEIO INTENÇÃO (Digitação livre/Voz), EXECUTA O NLU
    if not intent:
        resultado_nlu = extrair_intencao_e_entidade(texto)
        intent = resultado_nlu.get('intent')
        termo_extraido = resultado_nlu.get('termo')
        
        # Só atualiza 'texto' se o NLU retornou um termo válido (não None/vazio/string 'None')
        if termo_extraido and str(termo_extraido).strip().lower() not in ['none', 'null', '']:
            texto = termo_extraido

    if not intent:
        return JsonResponse({"invalido": "Não entendi sua solicitação. Tente informar o nome de um medicamento ou CID."})

    intent_clean = str(intent).lower().strip().replace('_', ' ')

    MAPA_INTENCOES = {
        'cid': 'cid',
        'buscar cid': 'cid',
        'medicamento': 'medicamento',
        'info medicamento': 'medicamento',
        'onde retirar': 'onde retirar medicamento',
        'onde retirar medicamento': 'onde retirar medicamento',
        'retirar medicamento': 'onde retirar medicamento',
    }

    # Mapeia sinônimos para a intenção padrão
    intent_final = MAPA_INTENCOES.get(intent_clean, intent_clean)

    # 3. PROCESSAMENTO DAS INTENÇÕES (use intent_final aqui)
    if intent_final == 'cid':
        req.text = texto
        if not validar_intent_cid(req):
            return JsonResponse({"invalido": "CID invalido"})

        df_dados = buscando_com_cid(texto)
        
        if df_dados.empty:
            return JsonResponse({'invalido': 'cid nao encontrado'})
        else:
            resposta_chat_str = formata_resposta_cid(df_dados)
            return JsonResponse({
                "answer": resposta_chat_str,
                "match_type": "exato",
                "nome_encontrado": df_dados.iloc[0]['MEDICAMENTO']
            })

    elif intent_final == 'medicamento':
        resultado = buscando_com_nome_medicamento(texto)

        if "erro" in resultado:
            return JsonResponse({"invalido": resultado["erro"]})

        resposta_chat_str = formata_resposta_medicamento(resultado["df"])

        return JsonResponse({
            "answer": resposta_chat_str,
            "match_type": resultado["match_type"],
            "nome_encontrado": resultado["nome_encontrado"]
        })

    elif intent_final == 'onde retirar medicamento':
        dict_enderecos = buscando_endereco(texto)

        if "erro" in dict_enderecos:
            return JsonResponse({"invalido": dict_enderecos["erro"]})

        nome_medicamento_buscado = dict_enderecos['medicamento']
        conjunto_farmacia = dict_enderecos['locais']
        match_type = dict_enderecos['match_type']

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

        return JsonResponse({
            'map_data': {
                "center": [marcadores_formatados[0]["lat"], marcadores_formatados[0]["lng"]],
                "markers": marcadores_formatados
            },
            "match_type": match_type,
            "nome_encontrado": nome_medicamento_buscado
        })

    return JsonResponse({"invalido": "Opção não reconhecida."})