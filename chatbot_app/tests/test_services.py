import pandas as pd
import numpy as np
import pytest

import chatbot_app.services as svc


@pytest.fixture
def df_exemplo():
    return pd.DataFrame({
        'coluna': ['palavra1', 'palavra2', 'palavra3']
    })


def test_procura_palavra_exata(df_exemplo):
    resultado = svc.procura_palavra_exata(df_exemplo, 'palavra2', 'coluna')
    assert len(resultado) == 1
    assert resultado.iloc[0]['coluna'] == 'palavra2'


def test_procura_palavra_exata_case_insensitive():
    df = pd.DataFrame({
        'coluna': ['Palavra1', 'PALAVRA2', 'palavra3']
    })

    resultado = svc.procura_palavra_exata(df, 'palavra2', 'coluna')

    assert len(resultado) == 1
    assert resultado.iloc[0]['coluna'] == 'PALAVRA2'


def test_procura_palavra_exata_multiplas_ocorrencias():
    df = pd.DataFrame({
        'coluna': ['palavra', 'outra palavra', 'mais palavra']
    })

    resultado = svc.procura_palavra_exata(df, 'palavra', 'coluna')

    assert len(resultado) == 3


def test_procura_palavra_exata_nao_encontra():
    df = pd.DataFrame({
        'coluna': ['palavra1', 'palavra2', 'palavra3']
    })

    resultado = svc.procura_palavra_exata(df, 'inexistente', 'coluna')

    assert len(resultado) == 0


def test_procura_palavra_exata_com_na():
    df = pd.DataFrame({
        'coluna': ['palavra1', np.nan, 'palavra3']
    })

    resultado = svc.procura_palavra_exata(df, 'palavra', 'coluna')

    assert len(resultado) == 2


def test_procura_palavra_exata_dataframe_vazio():
    df = pd.DataFrame({'coluna': []})

    resultado = svc.procura_palavra_exata(df, 'qualquer', 'coluna')

    assert len(resultado) == 0


def test_procura_palavra_semelhante_case_insensitive():
    df = pd.DataFrame({
        'coluna': ['aciclovir', 'PALAVRA2', 'palavra3']
    })

    resultado = svc.procura_palavra_semelhante(df, 'acicloviril', 'coluna')

    assert len(resultado) == 1
    assert resultado.iloc[0]['coluna'] == 'aciclovir'


def test_procura_palavra_semelhante_exclui_termo_exato():
    df = pd.DataFrame({
        'coluna': ['palavra', 'palavra']
    })

    resultado = svc.procura_palavra_semelhante(df, 'palavra', 'coluna')

    assert resultado.empty


def test_procura_palavra_semelhante_multiplas_ocorrencias():
    df = pd.DataFrame({
        'coluna': ['palavra', 'outra palavra', 'mais palavra']
    })

    resultado = svc.procura_palavra_semelhante(df, 'palavra', 'coluna')

    assert len(resultado) == 2


def test_procura_palavra_semelhante_nao_encontra():
    df = pd.DataFrame({
        'coluna': ['palavra1', 'palavra2', 'palavra3']
    })

    resultado = svc.procura_palavra_semelhante(df, 'inexistente', 'coluna')

    assert len(resultado) == 0


def test_procura_palavra_semelhante_com_na():
    df = pd.DataFrame({
        'coluna': ['palavra1', np.nan, 'palavra3']
    })

    resultado = svc.procura_palavra_semelhante(df, 'palavra', 'coluna')

    assert len(resultado) == 2


def test_retorna_palavra_mais_semelhante_case_insensitive():
    df = pd.DataFrame({
        'coluna': ['Palavra1', 'PALAVRA2', 'palavra3']
    })

    resultado = svc.retorna_palavra_mais_semelhante(df, 'palavra2', 'coluna')

    assert len(resultado) == 1
    assert resultado.iloc[0]['coluna'] == 'PALAVRA2'


def test_retorna_palavra_mais_semelhante_sem_resultado():
    df = pd.DataFrame({
        'coluna': ['x', 'y']
    })

    resultado = svc.retorna_palavra_mais_semelhante(df, 'palavra', 'coluna', threshold=100)

    assert resultado.empty


def test_tradutor_csv_enderecos_retorna_conjuntos_esperados():
    resultado = svc.tradutor_csv_enderecos(['DISTRITAIS', 'MUNICIPAL', 'ESPECIAIS'])

    assert 'FARMÁCIA DISTRITAL CAMOBI' in resultado
    assert 'FARMÁCIA DISTRITAL SÃO FRANCISCO' in resultado
    assert 'FARMÁCIA MUNICIPAL CENTRAL' in resultado
    assert 'FARMÁCIA DE MEDICAMENTOS ESPECIAIS' in resultado
    assert len(resultado) == 8


def test_tradutor_csv_enderecos_lista_vazia():
    assert svc.tradutor_csv_enderecos([]) == set()


def test_formata_resposta_cid_com_valores():
    df = pd.DataFrame({
        'MEDICAMENTO': ['Medicamento X'],
        'INFORMAÇÕES ADICIONAIS': ['Uso diário']
    })

    texto = svc.formata_resposta_cid(df)

    assert 'Medicamento X' in texto
    assert 'Uso diário' in texto
    assert texto.startswith('Encontrei as seguintes informações:')


def test_formata_resposta_medicamento_substitui_na():
    df = pd.DataFrame({
        'CID': [np.nan],
        'INFORMAÇÕES ADICIONAIS': [np.nan]
    })

    texto = svc.formata_resposta_medicamento(df)

    assert 'Sem CID cadastrado para o medicamento.' in texto
    assert 'Sem informação extra cadastrada para o medicamento.' in texto


def test_buscar_csv_retorna_dicionario_com_resultados(monkeypatch):
    df = pd.DataFrame({
        'Nome do medicamento': ['aciclovir', 'acicloviril']
    })

    monkeypatch.setattr(svc.pd, 'read_csv', lambda *args, **kwargs: df)

    resultado = svc.buscar_csv('aciclovir', 'Nome do medicamento')

    assert isinstance(resultado, dict)
    assert 'resultados_exatos' in resultado
    assert 'resultados_semelhantes' in resultado
    assert len(resultado['resultados_exatos']) == 2
    assert len(resultado['resultados_semelhantes']) >= 1
    assert 'aciclovir' in resultado['resultados_semelhantes']['Nome do medicamento'].str.lower().tolist()


def test_buscar_csv_nao_encontra(monkeypatch):
    df = pd.DataFrame({'Nome do medicamento': ['outra']})

    monkeypatch.setattr(svc.pd, 'read_csv', lambda *args, **kwargs: df)

    resultado = svc.buscar_csv('inexistente', 'Nome do medicamento')

    assert len(resultado['resultados_exatos']) == 0
    assert len(resultado['resultados_semelhantes']) == 0


def test_buscando_com_cid_remove_duplicatas(monkeypatch):
    df = pd.DataFrame({
        'CID': ['123', '123'],
        'MEDICAMENTO': ['Azitromicina', 'Azitromicina']
    })

    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': df, 'resultados_semelhantes': pd.DataFrame()})

    resultado = svc.buscando_com_cid('123')

    assert len(resultado) == 1
    assert resultado.iloc[0]['CID'] == '123'


def test_buscando_com_cid_sem_resultado(monkeypatch):
    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': pd.DataFrame(), 'resultados_semelhantes': pd.DataFrame()})

    resultado = svc.buscando_com_cid('999')

    assert resultado.empty


def test_buscando_com_nome_medicamento_exato(monkeypatch):
    df = pd.DataFrame({
        'MEDICAMENTO': ['Medicamento A', 'Medicamento B'],
        'CID': ['001', '001'],
        'INFORMAÇÕES ADICIONAIS': ['Info A', 'Info B']
    })

    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': df, 'resultados_semelhantes': pd.DataFrame()})

    resultado = svc.buscando_com_nome_medicamento('Medicamento A')

    assert resultado['match_type'] == 'exato'
    assert resultado['nome_encontrado'] == 'Medicamento A'
    assert len(resultado['df']) == 1


def test_buscando_com_nome_medicamento_semelhante(monkeypatch):
    df = pd.DataFrame({
        'MEDICAMENTO': ['Medicamento C'],
        'CID': ['002'],
        'INFORMAÇÕES ADICIONAIS': ['Info C']
    })

    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': pd.DataFrame(), 'resultados_semelhantes': df})

    resultado = svc.buscando_com_nome_medicamento('Medicamento C')

    assert resultado['match_type'] == 'semelhante'
    assert resultado['nome_encontrado'] == 'Medicamento C'
    assert len(resultado['df']) == 1


def test_buscando_com_nome_medicamento_nao_encontra(monkeypatch):
    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': pd.DataFrame(), 'resultados_semelhantes': pd.DataFrame()})

    resultado = svc.buscando_com_nome_medicamento('Nenhum')

    assert resultado == {'erro': 'Desculpe, não consegui encontrar informações sobre esse medicamento.'}


def test_buscando_endereco_exato_com_locais_especiais(monkeypatch):
    df = pd.DataFrame({
        'MEDICAMENTO': ['Medicamento X'],
        'CID': ['003'],
        'LOCAL_DE_DISPENSACAO': [np.nan]
    })

    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': df, 'resultados_semelhantes': pd.DataFrame()})

    resultado = svc.buscando_endereco('Medicamento X')

    assert resultado['medicamento'] == 'Medicamento X'
    assert resultado['match_type'] == 'exato'
    assert resultado['locais'] == {'FARMÁCIA DE MEDICAMENTOS ESPECIAIS'}


def test_buscando_endereco_semelhante(monkeypatch):
    df = pd.DataFrame({
        'MEDICAMENTO': ['Medicamento Y'],
        'CID': ['004'],
        'LOCAL_DE_DISPENSACAO': [np.nan]
    })

    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': pd.DataFrame(), 'resultados_semelhantes': df})

    resultado = svc.buscando_endereco('Medicamento Y')

    assert resultado['medicamento'] == 'Medicamento Y'
    assert resultado['match_type'] == 'semelhante'
    assert resultado['locais'] == {'FARMÁCIA DE MEDICAMENTOS ESPECIAIS'}


def test_buscando_endereco_nao_encontra(monkeypatch):
    monkeypatch.setattr(svc, 'buscar_csv', lambda text, coluna: {'resultados_exatos': pd.DataFrame(), 'resultados_semelhantes': pd.DataFrame()})

    resultado = svc.buscando_endereco('Nada')

    assert resultado == {'erro': 'Desculpe, não consegui encontrar informações sobre esse medicamento.'}
