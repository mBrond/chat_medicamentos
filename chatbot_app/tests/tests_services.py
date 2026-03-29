import pandas as pd
import numpy as np
import pytest

#from chatbot_app.services 
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


def test_procura_palavra_exata_coluna_diferente(): #!! ?
    df = pd.DataFrame({
        'coluna1': ['palavra1', 'palavra2'],
        'coluna2': ['outro1', 'outro2']
    })

    resultado = svc.procura_palavra_exata(df, 'palavra', 'coluna1')

    assert len(resultado) == 2


def test_procura_palavra_exata_dataframe_vazio():
    df = pd.DataFrame({'coluna': []})

    resultado = svc.procura_palavra_exata(df, 'qualquer', 'coluna')

    assert len(resultado) == 0


#----------------

def test_procura_palavra_semelhante_case_insensitive():
    df = pd.DataFrame({
        'coluna': ['aciclovir', 'PALAVRA2', 'palavra3']
    })

    resultado = svc.procura_palavra_semelhante(df, 'acicloviril', 'coluna') #nome do medicamento escrito errado

    assert resultado.iloc[0]['coluna'] == 'aciclovir'


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

    assert len(resultado) == 2  # Deve ignorar NaN


#----------------

def test_retorna_palavra_mais_semelhante_case_insensitive():
    df = pd.DataFrame({
        'coluna': ['Palavra1', 'PALAVRA2', 'palavra3']
    })

    resultado = svc.retorna_palavra_mais_semelhante(df, 'palavra2', 'coluna')

    assert len(resultado) == 1
    assert resultado.iloc[0]['coluna'] == 'PALAVRA2'


#----------------


def test_buscar_csv():
    resultado = svc.buscar_csv('acicloviril', 'Nome do medicamento')
    assert len(resultado) > 0
    assert 'aciclovir' in resultado.iloc[0]['Nome do medicamento'].lower()


def test_buscar_csv_nao_encontra():
    resultado = svc.buscar_csv('inexistente', 'Nome do medicamento')
    assert len(resultado) == 0


#----------------
