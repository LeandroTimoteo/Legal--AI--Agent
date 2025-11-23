from agente import classificar_acao

def test_classificacao_trabalhista():
    texto = "O funcionário busca reparação por salário não pago."
    assert classificar_acao(texto) == "trabalhista"

def test_classificacao_civil():
    texto = "A ação trata de quebra de contrato e pedido de indenização."
    assert classificar_acao(texto) == "civil"

def test_classificacao_penal():
    texto = "O réu foi acusado de crime contra a vida."
    assert classificar_acao(texto) == "penal"

def test_classificacao_desconhecida():
    texto = "Pedido genérico sem contexto jurídico claro."
    assert classificar_acao(texto) == "desconhecido"

