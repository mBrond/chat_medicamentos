import json
from io import StringIO

from django.test import RequestFactory
from django.http import JsonResponse

import pytest

from chatbot_app import views


class FakeChatRequest:
    def __init__(self, text, intent):
        self.text = text
        self.intent = intent


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_landing_page_retorna_200(request_factory):
    request = request_factory.get('/')

    response = views.landing_page(request)

    assert response.status_code == 200
    assert 'text/html' in response['Content-Type']


def test_health_check_retorna_status_ok():
    response = views.health_check(None)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    body = json.loads(response.content.decode('utf-8'))
    assert body == {'status': 'ok'}


def test_conversation_get_retorna_405(request_factory):
    request = request_factory.get('/chat')

    response = views.conversation(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 405
    body = json.loads(response.content.decode('utf-8'))
    assert body['detail'] == 'Método não permitido.'


def test_conversation_intent_medicamento_retorna_answer(monkeypatch, request_factory):
    request = request_factory.post('/chat', data=json.dumps({'text': 'paracetamol', 'intent': 'medicamento'}), content_type='application/json')

    fake_req = FakeChatRequest('paracetamol', 'medicamento')
    monkeypatch.setattr(views, 'validar_request', lambda req, tipo: fake_req)
    monkeypatch.setattr(views, 'buscando_com_nome_medicamento', lambda texto: {
        'df': 'fake_df',
        'match_type': 'exato',
        'nome_encontrado': 'Paracetamol'
    })
    monkeypatch.setattr(views, 'formata_resposta_medicamento', lambda df: 'Resposta formatada')

    response = views.conversation(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    body = json.loads(response.content.decode('utf-8'))
    assert body['answer'] == 'Resposta formatada'
    assert body['match_type'] == 'exato'
    assert body['nome_encontrado'] == 'Paracetamol'


def test_conversation_intent_medicamento_nao_encontra(monkeypatch, request_factory):
    request = request_factory.post('/chat', data=json.dumps({'text': 'desconhecido', 'intent': 'medicamento'}), content_type='application/json')

    fake_req = FakeChatRequest('desconhecido', 'medicamento')
    monkeypatch.setattr(views, 'validar_request', lambda req, tipo: fake_req)
    monkeypatch.setattr(views, 'buscando_com_nome_medicamento', lambda texto: {'erro': 'Desculpe, não consegui encontrar informações sobre esse medicamento.'})

    response = views.conversation(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    body = json.loads(response.content.decode('utf-8'))
    assert body == {'invalido': 'Desculpe, não consegui encontrar informações sobre esse medicamento.'}


def test_conversation_onde_retirar_medicamento_retorna_map_data(monkeypatch, request_factory):
    request = request_factory.post('/chat', data=json.dumps({'text': 'paracetamol', 'intent': 'onde retirar medicamento'}), content_type='application/json')

    fake_req = FakeChatRequest('paracetamol', 'onde retirar medicamento')
    monkeypatch.setattr(views, 'validar_request', lambda req, tipo: fake_req)
    monkeypatch.setattr(views, 'buscando_endereco', lambda text: {
        'medicamento': 'Paracetamol',
        'locais': {'FARMÁCIA DISTRITAL CAMOBI'},
        'match_type': 'semelhante'
    })

    monkeypatch.setattr(views.json, 'load', lambda f: {
        'FARMÁCIA DISTRITAL CAMOBI': {
            'marker': [-29.6872665, -53.8148498],
            'endereco': 'Rua Exemplo, 123',
            'imagem': None
        }
    })

    response = views.conversation(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    body = json.loads(response.content.decode('utf-8'))
    assert body['match_type'] == 'semelhante'
    assert body['nome_encontrado'] == 'Paracetamol'
    assert 'map_data' in body
    assert body['map_data']['center'] == [-29.6872665, -53.8148498]
    assert body['map_data']['markers'][0]['nome'] == 'FARMÁCIA DISTRITAL CAMOBI'


def test_conversation_onde_retirar_medicamento_nao_encontra(monkeypatch, request_factory):
    request = request_factory.post('/chat', data=json.dumps({'text': 'desconhecido', 'intent': 'onde retirar medicamento'}), content_type='application/json')

    fake_req = FakeChatRequest('desconhecido', 'onde retirar medicamento')
    monkeypatch.setattr(views, 'validar_request', lambda req, tipo: fake_req)
    monkeypatch.setattr(views, 'buscando_endereco', lambda text: {'erro': 'Desculpe, não consegui encontrar informações sobre esse medicamento.'})

    response = views.conversation(request)

    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    body = json.loads(response.content.decode('utf-8'))
    assert body == {'invalido': 'Desculpe, não consegui encontrar informações sobre esse medicamento.'}
