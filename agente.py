def classificar_acao(texto: str) -> str:
    texto = texto.lower()

    # Dicionário expandido de palavras-chave para maior precisão local
    categorias = {
        "trabalhista": [
            "relação de trabalho", "salário", "emprego", "demissão", "fgts",
            "clt", "horas extras", "verbas rescisórias", "carteira de trabalho",
            "estabilidade", "aviso prévio", "insalubridade", "periculosidade"
        ],
        "civil": [
            "contrato", "indenização", "dívida", "aluguel", "herança",
            "danos morais", "família", "divórcio", "posse", "propriedade",
            "consumidor", "obrigação", "espólio", "inventário"
        ],
        "penal": [
            "crime", "pena", "acusado", "prisão", "homicídio",
            "furto", "roubo", "estelionato", "processo penal", "inquérito",
            "denúncia", "réu", "sentença condenatória"
        ]
    }

    for categoria, palavras in categorias.items():
        if any(palavra in texto for palavra in palavras):
            return categoria

    return "desconhecido"

