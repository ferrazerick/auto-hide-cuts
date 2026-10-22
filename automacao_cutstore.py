import requests
import json
import time

# Configurações
BASE_URL = "http://agent.cutstore.cn"
SESSION_ID = ""
MARCA_DESEJADA = "Apple"
MODELO_DESEJADO = "18 Pro Max"
PLT_CODES = [46510, 46938, 49931]

# Códigos de cores ANSI para o terminal
AMARELO = "\033[33m"
VERDE = "\033[32m"
VERMELHO = "\033[31m"
AZUL = "\033[34m"
LARANJA = "\033[38;5;208m"
RESET = "\033[0m"

HEADERS = {
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/agent/",
    "sessionId": SESSION_ID,
    "Content-Type": "application/json"
}

def requisicao_api(endpoint, payload, descricao):
    """Função genérica para requisições POST na API com tratamento de erros."""
    url = f"{BASE_URL}{endpoint}"
    print(f"{AMARELO}{descricao}{RESET}")
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        data = response.json()
        if data.get("code") != 200:
            print(f"{VERMELHO}Erro ao {descricao.lower()}: {data}{RESET}")
            return None
        return data.get("data", {}).get("bussData", [])
    except Exception as e:
        print(f"{VERMELHO}Exceção ao {descricao.lower()}: {e}{RESET}")
        return None

def normalizar_plt_codes(numeros):
    """Garante que os códigos estejam no formato de lista com prefixo 'L'."""
    if isinstance(numeros, (str, int)):
        numeros = [numeros]
    
    plt_codes = []
    for num in numeros:
        num_str = str(num).strip()
        if num_str.upper().startswith('L'):
            plt_codes.append(num_str.upper())
        else:
            plt_codes.append(f"L{num_str}")
    return plt_codes

def obter_id_marca(marcas, marca_nome):
    """Busca o ID da marca pelo nome em inglês."""
    for m in marcas:
        if m.get("nameEn") == marca_nome:
            return m.get("id")
    return None

def obter_id_modelo(modelos, modelo_nome):
    """Busca o ID do modelo pelo nome em inglês ou chinês."""
    for mod in modelos:
        if mod.get("nameEn") == modelo_nome or mod.get("nameCn") == modelo_nome:
            return mod.get("id")
    return None

def aguardar_proximo_insert():
    """Executa o timer regressivo entre os inserts."""
    print("Tempo para o próximo insert:")
    for i in range(6, 0, -1):
        print(f"{AZUL}{i}...{RESET}", end="\r", flush=True)
        time.sleep(1)
    print(" " * 20, end="\r")
    print()

def processar_cadastros(marca_nome, modelo_nome, numeros, category_one_id, agent_list, agent_id, second_agent_id):
    plt_codes = normalizar_plt_codes(numeros)
    
    # Listas para o log final
    sucessos = []
    erros = [] # Armazenará tuplas: (plt_code, mensagem_de_erro)
        
    # 1. Buscar Marca
    marcas = requisicao_api("/v3/api/sysCategoryTwo/find_list", {"categoryOneId": category_one_id}, "Buscando lista de marcas na API...")
    if not marcas: return

    category_two_id = obter_id_marca(marcas, marca_nome)
    if not category_two_id:
        print(f"{VERMELHO}Marca '{marca_nome}' não foi encontrada exatamente igual. Execução encerrada.{RESET}")
        return
    print(f"{VERDE}Marca '{marca_nome}' encontrada com ID (categoryTwoId): {category_two_id}{RESET}")

    # 2. Buscar Modelo
    modelos = requisicao_api("/v3/api/sysCategoryThree/find_list", {"categoryTwoId": category_two_id}, "Buscando lista de modelos na API...")
    if not modelos: return

    category_three_id = obter_id_modelo(modelos, modelo_nome)
    if not category_three_id:
        print(f"{VERMELHO}Modelo '{modelo_nome}' não foi encontrado exatamente igual na categoria. Execução encerrada.{RESET}")
        return
    print(f"{VERDE}Modelo '{modelo_nome}' encontrada com ID (categoryThreeId): {category_three_id}{RESET}")

    # 3. Buscar Produtos/PLT Codes
    produtos = requisicao_api("/v3/api/sysCategoryProduct/find_list", {"categoryThreeId": category_three_id}, "Buscando produtos e PLT codes do modelo...")
    if not produtos: return

    mapa_produtos = {p["pltCode"]: p for p in produtos if "pltCode" in p}

    # 4. Processar Inserções
    url_insert = f"{BASE_URL}/v3/api/category/custom/product/insert"
    total_itens = len(plt_codes)

    for index, plt_code in enumerate(plt_codes):
        if plt_code not in mapa_produtos:
            err_msg = "PLT Code não encontrado no find_list para este modelo"
            print(f"{VERMELHO}{plt_code} - {err_msg}{RESET}")
            erros.append((plt_code, err_msg))
            continue
        
        prod = mapa_produtos[plt_code]
        
        payload_insert = {
            "id": "",
            "agentList": agent_list,
            "agentId": agent_id,
            "secondAgentId": second_agent_id,
            "threeAgentId": 0,
            "type": "out",
            "categoryOneId": category_one_id,
            "categoryTwoId": category_two_id,
            "categoryThreeId": category_three_id,
            "categoryProductId": prod["id"],  
            "enable": 0,
            "sort": 0,
            "nameCn": prod.get("nameCn", ""),
            "nameEn": prod.get("nameEn", "")
        }
        
        try:
            res = requests.post(url_insert, headers=HEADERS, json=payload_insert).json()
            if res.get("code") == 200:
                print(f"{VERDE}PLT Code '{plt_code}' (ID: {prod['id']}) cadastrado com sucesso para o modelo {modelo_nome}!{RESET}")
                sucessos.append(plt_code)
            else:
                err_msg = res.get("data", {}).get("errMsg") or res.get("message") or str(res)
                print(f"{VERMELHO}Falha ao cadastrar PLT Code '{plt_code}': {err_msg}{RESET}")
                erros.append((plt_code, err_msg))
        except Exception as e:
            err_msg = str(e)
            print(f"{VERMELHO}Exceção ao enviar PLT Code '{plt_code}': {err_msg}{RESET}")
            erros.append((plt_code, err_msg))

        if index < total_itens - 1:
            aguardar_proximo_insert()

    # Exibição do Log Final
    print("\n" + "="*50)
    print("LOG FINAL DE PROCESSAMENTO")
    print("="*50)
    
    print(f"{AZUL}PLT Codes que deram certo:{RESET}")
    if sucessos:
        for codigo in sucessos:
            print(f"{AZUL}- {codigo}{RESET}")
    else:
        print(f"{AZUL}Nenhum código cadastrado com sucesso.{RESET}")

    print(f"\n{LARANJA}PLT Codes que deram errado:{RESET}")
    if erros:
        for codigo, mensagem in erros:
            print(f"{LARANJA}- {codigo} - {mensagem}{RESET}")
    else:
        print(f"{LARANJA}Nenhum erro registrado.{RESET}")
    print("="*50)

if __name__ == "__main__":
    CAT_ONE = 6991998
    AGENT_LIST = [903, 9549]
    AGENT_ID = 903
    SEC_AGENT_ID = 9549
    
    processar_cadastros(
        marca_nome=MARCA_DESEJADA,
        modelo_nome=MODELO_DESEJADO,
        numeros=PLT_CODES,
        category_one_id=CAT_ONE,
        agent_list=AGENT_LIST,
        agent_id=AGENT_ID,
        second_agent_id=SEC_AGENT_ID
    )