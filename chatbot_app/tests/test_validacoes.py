import json

import pytest
from django.test import RequestFactory
from django.http import JsonResponse

from chatbot_app.validacoes import validar_chat_request, validar_intent_cid, validar_request


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_validar_chat_request_valido():
    data = {'text': '123', 'intent': 'CID'}

    resultado = validar_chat_request(data)

    assert resultado.text == '123'
    assert resultado.intent == 'CID'


def test_validar_chat_request_invalido_retorna_jsonresponse():
    data = {'text': '123'}

    resultado = validar_chat_request(data)

    assert isinstance(resultado, JsonResponse)
    assert resultado.status_code == 400
    response_data = json.loads(resultado.content.decode('utf-8'))
    assert response_data['detail'] == 'Dados de entrada inválidos.'


def test_validar_intent_cid_tamanho_minimo_e_maximo():
    assert validar_intent_cid(type('T', (), {'text': '123'})()) is True
    assert validar_intent_cid(type('T', (), {'text': '12345'})()) is True


def test_validar_intent_cid_menor_que_3_false():
    assert validar_intent_cid(type('T', (), {'text': '12'})()) is False


def test_validar_intent_cid_maior_que_5_false():
    assert validar_intent_cid(type('T', (), {'text': '123456'})()) is False


def test_validar_intent_cid_com_espacos_e_case_insensitive():
    assert validar_intent_cid(type('T', (), {'text': '  AbC12  '})()) is True


def test_validar_request_get_retorna_405(request_factory):
    request = request_factory.get('/chat')

    response = validar_request(request, 'conversation')

    assert isinstance(response, JsonResponse)
    assert response.status_code == 405


def test_validar_request_post_valido_retorna_chatrequest(request_factory):
    request = request_factory.post('/chat', data=json.dumps({'text': '123', 'intent': 'CID'}), content_type='application/json')

    resultado = validar_request(request, 'conversation')

    assert resultado.text == '123'
    assert resultado.intent == 'CID'


def test_validar_request_post_payload_invalido_retorna_jsonresponse(request_factory):
    request = request_factory.post('/chat', data=json.dumps({'text': '123'}), content_type='application/json')

    resultado = validar_request(request, 'conversation')

    assert isinstance(resultado, JsonResponse)
    assert resultado.status_code == 400
    response_data = json.loads(resultado.content.decode('utf-8'))
    assert response_data['detail'] == 'Dados de entrada inválidos.'


def test_validar_request_post_json_invalido_levanta_value_error(request_factory):
    request = request_factory.post('/chat', data='{' , content_type='application/json')

    with pytest.raises(ValueError):
        validar_request(request, 'conversation')
