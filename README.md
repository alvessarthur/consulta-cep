#### Opção 1: CEP Único
```
1. Escolha "Buscar CEP"
2. Digite o CEP (ex: 01310-100)
3. Escolha "Abrir no Google Maps"
4. O mapa abre automaticamente no navegador
```

#### Opção 2: Múltiplos CEPs
```
1. Escolha "Buscar múltiplos CEPs"
2. Digite os CEPs (um por linha)
3. Ao final, escolha abrir mapas
4. Todos os mapas serão abertos com delay automático
```

### 🔗 Formato da URL

A URL gerada segue este padrão:
```
https://www.google.com/maps/search/{logradouro}/@{latitude},{longitude},18z
```

**Exemplo:**
```
https://www.google.com/maps/search/Avenida+Paulista/@-23.5614,-46.6561,18z
```

---

## �📋 Requisitos

- Python 3.8+
- pip (gerenciador de pacotes)
- Conexão com internet

---

## 📁 Estrutura do Projeto

```
consulta-cep/
├── main.py                      # Aplicação CLI principal
├── requirements.txt             # Dependências do frontend
├── historico_buscas.json        # Histórico persistente (gerado automaticamente)
├── README.md                    # Este arquivo
│
└── backend/
    ├── main.py                  # Aplicação FastAPI
    ├── config.py                # Configurações da API
    ├── requirements.txt         # Dependências do backend
    ├── .gitignore               # Arquivos ignorados pelo git
    ├── historico_backend.json   # Histórico da API (gerado automaticamente)
    │
    └── templates/
        └── index.html           # Interface web interativa da API
```

---

## � Como Usar o Backend

### Instalação

```bash
# 1. Acesse a pasta backend
cd backend

# 2. Instale as dependências
pip install -r requirements.txt
```

### Iniciar o Servidor

```bash
# Opção 1: Com uvicorn direto
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opção 2: Executar o script Python
python main.py
```

### Acessar a Aplicação

Abra seu navegador e acesse:

- **Interface Web:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Features da Interface Web

✨ **Abas da Aplicação:**
1. 🔍 **Buscar CEP** - Buscar um CEP individual com botões de Google Maps e Uber
2. 📋 **Múltiplos CEPs** - Buscar vários CEPs de uma vez com resultados formatados
3. 📚 **Histórico** - Visualizar últimas buscas e limpar histórico
4. 📖 **Documentação** - Links para Swagger UI e ReDoc

---

## �🔌 Endpoints da API

### Documentação Interativa
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Endpoints Disponíveis

#### 1. **Consultar CEP**
```
GET /cep/{cep}
```

**Exemplo:**
```bash
curl "http://localhost:8000/cep/01310100"
```

**Resposta:**
```json
{
  "cep": "01310-100",
  "logradouro": "Avenida Paulista",
  "bairro": "Bela Vista",
  "localidade": "São Paulo",
  "uf": "SP",
  "complemento": ""
}
```

#### 2. **Consultar CEP com Coordenadas (Google Maps)**
```
GET /cep/{cep}/mapa
```

**Exemplo:**
```bash
curl "http://localhost:8000/cep/01310100/mapa"
```

**Resposta:**
```json
{
  "cep": "01310-100",
  "logradouro": "Avenida Paulista",
  "bairro": "Bela Vista",
  "localidade": "São Paulo",
  "uf": "SP",
  "latitude": -23.5614,
  "longitude": -46.6561,
  "url_google_maps": "https://www.google.com/maps/search/-23.5614,-46.6561"
}
```

#### 3. **Consultar Múltiplos CEPs**
```
GET /cep/multiplo?ceps=01310100&ceps=20040020&ceps=70040902
```

**Resposta:**
```json
{
  "total": 3,
  "sucesso": 3,
  "falhas": 0,
  "resultados": [...],
  "erros": []
}
```

#### 4. **Obter Histórico**
```
GET /historico?limite=10
```

**Parâmetros:**
- `limite` (opcional): Número de registros (padrão: 10, máximo: 100)

**Resposta:**
```json
{
  "total": 2,
  "itens": [
    {
      "cep": "01310-100",
      "data": "23/09/2026 14:30:45",
      "endereco": {...}
    }
  ]
}
```

#### 5. **Limpar Histórico**
```
DELETE /historico
```

**Resposta:**
```json
{
  "mensagem": "Histórico limpo com sucesso"
}
```

#### 6. **Verificar Saúde da API**
```
GET /saude
```

**Resposta:**
```json
{
  "status": "online",
  "timestamp": "23/09/2026 14:30:45"
}
```

---

## 📊 Arquivos de Histórico

### Frontend
- **Arquivo:** `historico_buscas.json`
- **Formato:** JSON
- **Conteúdo:** Histórico de todas as buscas realizadas

### Backend
- **Arquivo:** `backend/historico_backend.json`
- **Formato:** JSON
- **Conteúdo:** Histórico de buscas via API

---

## 🛠️ Tecnologias Utilizadas

### Frontend
- **Python 3.8+**
- **requests** - Requisições HTTP
- **webbrowser** - Integração com navegador
- **json** - Persistência de dados
- **logging** - Rastreamento de erros

### Backend
- **FastAPI** - Framework web
- **Uvicorn** - Servidor ASGI
- **Pydantic** - Validação de dados
- **requests** - Requisições HTTP
- **CORS** - Compartilhamento de recursos

### APIs Externas
- **ViaCEP** - Consulta de CEPs brasileiros
- **Nominatim (OpenStreetMap)** - Geolocalização com retry e validações
- **Google Maps** - Visualização de mapas com zoom automático

---

## 🧪 Tratamento de Erros

A aplicação trata os seguintes erros:

| Erro | Mensagem | Código HTTP |
|------|----------|-------------|
| CEP inválido | "CEP deve ter 8 dígitos" | 400 |
| CEP não encontrado | "CEP não encontrado" | 404 |
| Timeout da API | "Timeout ao consultar a API" | 503 |
| Erro de conexão | "Erro de conexão" | 503 |
| Erro interno | "Erro interno do servidor" | 500 |

---

## 📝 Exemplos de Uso

### Backend - Requisição Python

```python
import requests

# Consultar um CEP
response = requests.get("http://localhost:8000/cep/01310100")
print(response.json())

# Consultar CEP com mapa
response = requests.get("http://localhost:8000/cep/01310100/mapa")
print(response.json())

# Obter histórico
response = requests.get("http://localhost:8000/historico?limite=5")
print(response.json())
```

---

## 🔐 Validações

### CEP
- Deve ter exatamente 8 dígitos
- Suporta formatos: `12345-678` ou `12345678`
- Não pode estar vazio

### Coordenadas
- Latitude: -90 a 90
- Longitude: -180 a 180

### Requisições da API
- Timeout: 5 segundos
- CORS: Habilitado para todas as origens
- Documentação: Automática via Swagger

---

## 📈 Performance

- **Requisições simultâneas:** Suportadas
- **Cache:** Histórico local para referência rápida
- **Timeout:** 5 segundos por requisição
- **Limite de histórico:** 100 últimos registros
- **Retry automático:** Até 3 tentativas com backoff exponencial
- **Delay entre requisições:** 0.5 segundos (evita rate limiting)
- **Validação de coordenadas:** Rigorosa com tratamento de exceções

---

## 📄 Licença

Este projeto é de código aberto e pode ser usado livremente.

---

## 👨‍💻 Autor

Desenvolvido como uma solução completa para consulta de CEPs brasileiros.

---

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas!

---

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação da API em:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

**Versão:** 1.3.0 (Backend Web)  
**Última atualização:** 23 de Setembro de 2026  
**Status:** ✅ Pronto para produção
