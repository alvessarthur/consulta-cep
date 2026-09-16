# Exemplo-Consulta-de-Cep
Aplicação de terminal que recebe um CEP informado pelo usuário, consulta a API ViaCEP e apresenta os dados do endereço.
import requests

cep = input("Digite o CEP que deseja consultar: ")

url = f"https://viacep.com.br/ws/{cep}/json/"

resposta = requests.get(url)

dados = resposta.json()

print("\n--- Dados do endereço ---")
print(f"CEP: {dados['cep']}")
print(f"Logradouro: {dados['logradouro']}")
print(f"Bairro: {dados['bairro']}")
print(f"Cidade: {dados['localidade']}")
print(f"Estado: {dados['uf']}")
