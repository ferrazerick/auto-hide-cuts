import requests
import json
import time

# Códigos de cores ANSI para o terminal
AMARELO = "\033[33m"
VERDE = "\033[32m"
VERMELHO = "\033[31m"
AZUL = "\033[34m"
RESET = "\033[0m"

# Configurações de Acesso
BASE_URL = "http://agent.cutstore.cn"
SESSION_ID = ""

# ==========================================
# 1. DEFINIÇÕES NO TOPO
# ==========================================
MARCA_DESEJADA = "Apple"         # Nome exato da marca
MODELO_DESEJADO = "18 Pro Max"   # Nome exato do modelo
PLT_CODES = [46510, 46938]       # Número(s) do PLT Code (pode ser um único ou lista)

HEADERS = {
    "Origin": "http://agent.cutstore.cn",
    "Referer": "http://agent.cutstore.cn/agent/",
    "sessionId": SESSION_ID,
    "Content-Type": "application/json"
}

def processar_cadastros(marca_nome, modelo_nome, numeros, category_one_id, agent_list, agent_id, second_agent_id):
    # Converte PLT codes para lista se for passado apenas um
    if isinstance(numeros, (str, int)):
        numeros = [numeros]
        
    # Formata cada número para o padrão 'L' + números
    plt_codes = []
    for num in numeros:
        num_str = str(num).strip()
        if num_str.upper().startswith('L'):
            plt_codes.append(num_str.upper())
        else:
            plt_codes.append(f"L{num_str}")
        
    # -------------------------------------------------------------
    # PASSO 1: Buscar a Marca (sysCategoryTwo)
    # -------------------------------------------------------------
    url_marcas = f"{BASE_URL}/v3/api/sysCategoryTwo/find_list"
    payload_marcas = {"categoryOneId": category_one_id}
    
    print(f"{AMARELO}Buscando lista de marcas na API...{RESET}")
    try:
        response = requests.post(url_marcas, headers=HEADERS, json=payload_marcas)
        data = response.json()
        if data.get("code") != 200:
            print(f"{VERMELHO}Falha ao buscar marcas: {data}{RESET}")
            return
        marcas = data.get("data", {}).get("bussData", [])
    except Exception as e:
        print(f"{VERMELHO}Exceção ao buscar marcas: {e}{RESET}")
        return

    category_two_id = None
    for m in marcas:
        if m.get("nameEn") == marca_nome:
            category_two_id = m.get("id")
            break
            
    if not category_two_id:
        print(f"{VERMELHO}Marca '{marca_nome}' não foi encontrada exatamente igual. Execução encerrada.{RESET}")
        return
        
    print(f"{VERDE}Marca '{marca_nome}' encontrada com ID (categoryTwoId): {category_two_id}{RESET}")

    # -------------------------------------------------------------
    # PASSO 2: Buscar o Modelo (sysCategoryThree) usando o ID da marca
    # -------------------------------------------------------------
    url_modelos = f"{BASE_URL}/v3/api/sysCategoryThree/find_list"
    payload_modelos = {"categoryTwoId": category_two_id}
    
    print(f"{AMARELO}Buscando lista de modelos na API...{RESET}")
    try:
        response = requests.post(url_modelos, headers=HEADERS, json=payload_modelos)
        data = response.json()
        if data.get("code") != 200:
            print(f"{VERMELHO}Falha ao buscar modelos: {data}{RESET}")
            return
        modelos = data.get("data", {}).get("bussData", [])
    except Exception as e:
        print(f"{VERMELHO}Exceção ao buscar modelos: {e}{RESET}")
        return

    category_three_id = None
    for mod in modelos:
        if mod.get("nameEn") == modelo_nome or mod.get("nameCn") == modelo_nome:
            category_three_id = mod.get("id")
            break

    if not category_three_id:
        print(f"{VERMELHO}Modelo '{modelo_nome}' não foi encontrado exatamente igual na categoria. Execução encerrada.{RESET}")
        return

    print(f"{VERDE}Modelo '{modelo_nome}' encontrado com ID (categoryThreeId): {category_three_id}{RESET}")

    # -------------------------------------------------------------
    # PASSO 3: Buscar a lista de produtos finais (sysCategoryProduct) para obter os IDs dos PLT Codes
    # -------------------------------------------------------------
    url_produtos = f"{BASE_URL}/v3/api/sysCategoryProduct/find_list"
    payload_produtos = {"categoryThreeId": category_three_id}
    
    print(f"{AMARELO}Buscando produtos e PLT codes do modelo...{RESET}")
    try:
        response = requests.post(url_produtos, headers=HEADERS, json=payload_produtos)
        data = response.json()
        if data.get("code") != 200:
            print(f"{VERMELHO}Falha ao buscar produtos do modelo: {data}{RESET}")
            return
        produtos = data.get("data", {}).get("bussData", [])
    except Exception as e:
        print(f"{VERMELHO}Exceção ao buscar produtos: {e}{RESET}")
        return

    # Mapear produtos por pltCode para busca rápida
    mapa_produtos = {p["pltCode"]: p for p in produtos if "pltCode" in p}

    # -------------------------------------------------------------
    # PASSO 4: Realizar o insert dos PLT Codes com Timer dinâmico na mesma linha
    # -------------------------------------------------------------
    url_insert = f"{BASE_URL}/v3/api/category/custom/product/insert"
    total_itens = len(plt_codes)

    for index, plt_code in enumerate(plt_codes):
        if plt_code not in mapa_produtos:
            print(f"{VERMELHO}PLT Code '{plt_code}' não encontrado no find_list para este modelo.{RESET}")
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
            res_insert = requests.post(url_insert, headers=HEADERS, json=payload_insert)
            res_data = res_insert.json()
            
            if res_data.get("code") == 200:
                print(f"{VERDE}PLT Code '{plt_code}' (ID: {prod['id']}) cadastrado com sucesso para o modelo {modelo_nome}!{RESET}")
            else:
                err_msg = res_data.get("data", {}).get("errMsg") or res_data.get("message") or str(res_data)
                print(f"{VERMELHO}Falha ao cadastrar PLT Code '{plt_code}': {err_msg}{RESET}")
        except Exception as e:
            print(f"{VERMELHO}Exceção ao enviar PLT Code '{plt_code}': {e}{RESET}")

        # Se não for o último item, exibe a contagem regressiva na linha de baixo substituindo o número
        if index < total_itens - 1:
            print("Tempo para o próximo insert:")
            for i in range(7, 0, -1):
                print(f"{AZUL}{i}...{RESET}", end="\r", flush=True)
                time.sleep(1)
            print(" " * 20, end="\r")  # Limpa a linha ao finalizar a contagem
            print() # Pula para a próxima linha para o próximo insert

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