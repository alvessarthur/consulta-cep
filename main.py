import requests

cep = input("Digite o CEP: ").replace("-", "").strip()

if len(cep) != 8 or not cep.isdigit():
    print("CEP inválido.")
    exit()

url = f"https://viacep.com.br/ws/{cep}/json/"

try:
    resposta = requests.get(url, timeout=5)
    resposta.raise_for_status()

    dados = resposta.json()

    if dados.get("erro"):
        print("CEP não encontrado.")
    else:
        print("\n--- Dados do endereço ---")
        print(f"CEP: {dados.get('cep')}")
        print(f"Logradouro: {dados.get('logradouro')}")
        print(f"Bairro: {dados.get('bairro')}")
        print(f"Cidade: {dados.get('localidade')}")
        print(f"Estado: {dados.get('uf')}")

except requests.RequestException:
    print("Não foi possível consultar o CEP.")
