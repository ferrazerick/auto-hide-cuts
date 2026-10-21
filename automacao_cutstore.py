import requests
import json

# Configurações de Acesso
BASE_URL = "http://agent.cutstore.cn"
SESSION_ID = ""

# ==========================================
# DEFINA OS PLT CODES AQUI (Apenas os números)
# - Para testar apenas um: PLT_CODES = 46938 (ou "46938")
# - Para testar vários:    PLT_CODES = [46938, 47963, 48386]
# ==========================================
PLT_CODES = 46510

HEADERS = {
    "Origin": "http://agent.cutstore.cn",
    "Referer": "http://agent.cutstore.cn/agent/",
    "sessionId": SESSION_ID,
    "Content-Type": "application/json"
}

def processar_plt_codes(numeros, category_three_id, agent_list, agent_id, second_agent_id, category_one_id, category_two_id):
    # Converte para lista caso seja passado apenas um valor isolado
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
        
    # 1. Buscar a lista de produtos (find_list)
    url_find = f"{BASE_URL}/v3/api/sysCategoryProduct/find_list"
    payload_find = {
        "categoryThreeId": category_three_id
    }
    
    print("Buscando lista de produtos na API...")
    try:
        response = requests.post(url_find, headers=HEADERS, json=payload_find)
        data = response.json()
        
        if data.get("code") != 200:
            print(f"Erro ao buscar lista de produtos: {data}")
            return
        
        produtos = data.get("data", {}).get("bussData", [])
        mapa_produtos = {p["pltCode"]: p for p in produtos}
        
    except Exception as e:
        print(f"Erro de conexão ao buscar produtos: {e}")
        return

    # URL de inserção
    url_insert = f"{BASE_URL}/v3/api/category/custom/product/insert"

    # 2. Processar os códigos formatados
    for plt_code in plt_codes:
        if plt_code not in mapa_produtos:
            print(f"[-] PLT Code '{plt_code}' não encontrado no find_list para esta categoria.")
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
                print(f"[SUCESSO] PLT Code '{plt_code}' (ID: {prod['id']}) cadastrado com sucesso!")
            else:
                err_msg = res_data.get("data", {}).get("errMsg") or res_data.get("message") or str(res_data)
                print(f"[ERRO] Falha ao cadastrar PLT Code '{plt_code}': {err_msg}")
        except Exception as e:
            print(f"[ERRO] Exceção ao enviar PLT Code '{plt_code}': {e}")

if __name__ == "__main__":
    CAT_ONE = 6991998
    CAT_TWO = 6249260
    CAT_THREE = 33100112323
    AGENT_LIST = [903, 9549]
    AGENT_ID = 903
    SEC_AGENT_ID = 9549
    
    # Chama a função passando a variável do topo
    processar_plt_codes(
        numeros=PLT_CODES,
        category_three_id=CAT_THREE,
        agent_list=AGENT_LIST,
        agent_id=AGENT_ID,
        second_agent_id=SEC_AGENT_ID,
        category_one_id=CAT_ONE,
        category_two_id=CAT_TWO
    )