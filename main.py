import requests

def validar_cep(cep: str) -> str:
    cep = cep.replace("-", "").replace(".", "").strip()

    if len(cep) != 8 or not cep.isdigit():
        raise ValueError("CEP inválido.")

    return cep

def buscar_endereco(cep: str) -> dict:
    url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url, timeout=5)
    response.raise_for_status()

    dados = response.json()

    if dados.get("erro"):
        raise LookupError("CEP não encontrado.")

    return dados

def main():
    cep = input("Digite o CEP: ")

    try:
        cep_validado = validar_cep(cep)
        endereco = buscar_endereco(cep_validado)

        print("\n--- Dados do endereço ---")
        print(f"CEP: {endereco.get('cep')}")
        print(f"Logradouro: {endereco.get('logradouro')}")
        print(f"Bairro: {endereco.get('bairro')}")
        print(f"Cidade: {endereco.get('localidade')}")
        print(f"Estado: {endereco.get('uf')}")

    except ValueError as e:
        print(e)
    except LookupError as e:
        print(e)
    except requests.RequestException:
        print("Não foi possível consultar o CEP.")

if __name__ == "__main__":
    main()
