import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agente import classificar_acao

def test_classificacao_trabalhista():
    texto = "O funcionário busca reparação por salário não pago."
    assert classificar_acao(texto) == "trabalhista"

def test_classificacao_trabalhista_demissao():
    texto = "A discussão é sobre a demissão do empregado."
    assert classificar_acao(texto) == "trabalhista"

def test_classificacao_civil():
    texto = "A ação trata de quebra de contrato e pedido de indenização."
    assert classificar_acao(texto) == "civil"

def test_classificacao_civil_heranca():
    texto = "Disputa sobre a partilha de herança."
    assert classificar_acao(texto) == "civil"

def test_classificacao_penal():
    texto = "O réu foi acusado de crime contra a vida."
    assert classificar_acao(texto) == "penal"

def test_classificacao_penal_prisao():
    texto = "O caso envolve a prisão do suspeito."
    assert classificar_acao(texto) == "penal"

def test_classificacao_desconhecida():
    texto = "Pedido genérico sem contexto jurídico claro."
    assert classificar_acao(texto) == "desconhecido"

def test_classificacao_case_insensitive():
    texto = "Análise de um CONTRATO com cláusulas de INDENIZAÇÃO."
    assert classificar_acao(texto) == "civil"

def test_classificacao_multiplas_palavras():
    texto = "O crime de homicídio resultou em prisão."
    assert classificar_acao(texto) == "penal"
