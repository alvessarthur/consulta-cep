import requests
import logging
import webbrowser
import time
import json
import os
from datetime import datetime
from typing import Optional, List, Dict

# Configuração
CEP_API_URL = "https://viacep.com.br/ws/{}/json/"
GEOCODE_API_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT = 5
HISTORICO_FILE = "historico_buscas.json"
MAX_RETRIES = 3
RETRY_DELAY = 1  # segundos

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GerenciadorHistorico:
    """Gerencia o histórico de buscas em arquivo JSON."""
    
    def __init__(self, arquivo: str = HISTORICO_FILE):
        self.arquivo = arquivo
        self.dados = self._carregar()
    
    def _carregar(self) -> List[Dict]:
        """Carrega histórico do arquivo."""
        try:
            if os.path.exists(self.arquivo):
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erro ao carregar histórico: {e}")
            return []
    
    def _salvar(self) -> None:
        """Salva histórico no arquivo."""
        try:
            with open(self.arquivo, 'w', encoding='utf-8') as f:
                json.dump(self.dados, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Erro ao salvar histórico: {e}")
    
    def adicionar(self, cep: str, endereco: dict) -> None:
        """Adiciona uma busca ao histórico."""
        entrada = {
            "cep": cep,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "endereco": endereco
        }
        self.dados.append(entrada)
        self._salvar()
    
    def obter_todos(self) -> List[Dict]:
        """Retorna todo o histórico."""
        return self.dados
    
    def obter_ultimos(self, quantidade: int = 5) -> List[Dict]:
        """Retorna os últimos N registros."""
        return self.dados[-quantidade:]
    
    def limpar(self) -> None:
        """Limpa o histórico."""
        self.dados = []
        self._salvar()
    
    def remover_duplicatas(self) -> None:
        """Remove entradas duplicadas mantendo a mais recente."""
        ceps_vistos = {}
        dados_unicos = []
        
        for entrada in reversed(self.dados):
            cep = entrada.get("cep")
            if cep not in ceps_vistos:
                ceps_vistos[cep] = True
                dados_unicos.append(entrada)
        
        self.dados = list(reversed(dados_unicos))
        self._salvar()

historico = GerenciadorHistorico()

def validar_cep(cep: str) -> Optional[str]:
    """Valida e formata o CEP."""
    try:
        cep = cep.replace("-", "").replace(".", "").strip()

        if not cep:
            raise ValueError("CEP não pode estar vazio.")
        
        if len(cep) != 8:
            raise ValueError(f"CEP deve ter 8 dígitos. Recebido: {len(cep)}")
        
        if not cep.isdigit():
            raise ValueError("CEP deve conter apenas dígitos.")

        return cep
    
    except ValueError as e:
        logger.warning(f"Validação falhou: {e}")
        raise

def buscar_endereco(cep: str) -> Optional[dict]:
    """Busca o endereço do CEP na API ViaCEP."""
    try:
        url = CEP_API_URL.format(cep)
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        dados = response.json()

        if dados.get("erro"):
            raise LookupError(f"CEP {cep} não encontrado no sistema.")

        return dados
    
    except requests.Timeout:
        raise requests.RequestException("⏱️  Timeout ao consultar a API. Tente novamente.")
    except requests.HTTPError as e:
        raise requests.RequestException(f"❌ Erro HTTP {e.response.status_code}: {e.response.reason}")
    except requests.ConnectionError:
        raise requests.RequestException("❌ Erro de conexão. Verifique sua internet.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise requests.RequestException(f"❌ Erro inesperado: {e}")

def obter_coordenadas(endereco: dict) -> tuple:
    """Obtém as coordenadas (latitude, longitude) do endereço com retry e validações rigorosas."""
    try:
        logradouro = endereco.get("logradouro", "").strip()
        bairro = endereco.get("bairro", "").strip()
        localidade = endereco.get("localidade", "").strip()
        uf = endereco.get("uf", "").strip()
        
        if not logradouro or not localidade:
            logger.warning("Endereço incompleto para geolocalização")
            return None, None
        
        endereco_completo = f"{logradouro}, {localidade}, {uf}, Brasil"
        
        params = {
            "q": endereco_completo,
            "format": "json",
            "limit": 1,
            "timeout": REQUEST_TIMEOUT,
            "accept-language": "pt-BR"
        }
        
        # Implementar retry com backoff
        for tentativa in range(MAX_RETRIES):
            try:
                response = requests.get(
                    GEOCODE_API_URL, 
                    params=params, 
                    timeout=REQUEST_TIMEOUT,
                    headers={"User-Agent": "Consulta-CEP/1.0"}
                )
                response.raise_for_status()
                
                dados = response.json()
                
                if not dados:
                    logger.warning(f"Coordenadas não encontradas para: {endereco_completo}")
                    return None, None
                
                # Validar estrutura da resposta
                if not isinstance(dados[0], dict):
                    logger.error("Formato inválido na resposta da API")
                    return None, None
                
                try:
                    lat = float(dados[0].get("lat"))
                    lon = float(dados[0].get("lon"))
                except (ValueError, TypeError):
                    logger.error("Não foi possível converter coordenadas para float")
                    return None, None
                
                # Validar range de coordenadas
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    logger.warning(f"Coordenadas inválidas: lat={lat}, lon={lon}")
                    return None, None
                
                logger.info(f"Coordenadas obtidas com sucesso: {lat}, {lon}")
                return lat, lon
            
            except requests.Timeout:
                if tentativa < MAX_RETRIES - 1:
                    logger.warning(f"Timeout na tentativa {tentativa + 1}/{MAX_RETRIES}. Aguardando...")
                    time.sleep(RETRY_DELAY * (tentativa + 1))
                else:
                    logger.error("Timeout após todas as tentativas")
                    return None, None
            
            except requests.ConnectionError:
                if tentativa < MAX_RETRIES - 1:
                    logger.warning(f"Erro de conexão na tentativa {tentativa + 1}/{MAX_RETRIES}. Aguardando...")
                    time.sleep(RETRY_DELAY * (tentativa + 1))
                else:
                    logger.error("Erro de conexão após todas as tentativas")
                    return None, None
            
            except requests.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    if tentativa < MAX_RETRIES - 1:
                        espera = RETRY_DELAY * (2 ** tentativa)
                        logger.warning(f"Limite de requisições atingido. Aguardando {espera}s...")
                        time.sleep(espera)
                    else:
                        logger.error("Limite de requisições atingido após todas as tentativas")
                        return None, None
                else:
                    logger.error(f"Erro HTTP {e.response.status_code}: {e.response.reason}")
                    return None, None
            
            except requests.RequestException as e:
                logger.error(f"Erro na requisição: {e}")
                return None, None
    
    except Exception as e:
        logger.error(f"Erro inesperado ao obter coordenadas: {e}")
        return None, None

def abrir_google_maps(endereco: dict) -> None:
    """Abre o Google Maps no navegador com a localização do CEP."""
    try:
        lat, lon = obter_coordenadas(endereco)
        
        if lat is None or lon is None:
            logger.error("Coordenadas inválidas ou não encontradas")
            print("❌ Não foi possível abrir o mapa. Coordenadas inválidas.\n")
            return
        
        # Construir URL melhorada do Google Maps com label
        endereco_label = endereco.get("logradouro", "Localização").replace(" ", "+")
        url_google_maps = f"https://www.google.com/maps/search/{endereco_label}/@{lat},{lon},18z"
        
        try:
            print(f"🗺️  Abrindo Google Maps em {lat:.4f}, {lon:.4f}...")
            webbrowser.open(url_google_maps)
            logger.info(f"Google Maps aberto para: {lat}, {lon}")
            print("✅ Google Maps aberto no navegador!\n")
        except webbrowser.Error as e:
            logger.error(f"Erro ao abrir navegador: {e}")
            print(f"❌ Não foi possível abrir o navegador automaticamente.\n")
            print(f"Abra manualmente este link:\n{url_google_maps}\n")
    
    except Exception as e:
        logger.error(f"Erro inesperado ao abrir mapa: {e}")
        print(f"❌ Erro ao abrir mapa: {e}\n")

def formatar_endereco(endereco: dict) -> None:
    """Exibe o endereço formatado."""
    campos = [
        ("CEP", "cep"),
        ("Logradouro", "logradouro"),
        ("Bairro", "bairro"),
        ("Cidade", "localidade"),
        ("Estado", "uf"),
    ]

    print("\n✅ --- Dados do Endereço ---")
    for label, chave in campos:
        valor = endereco.get(chave, "").strip()
        if valor:
            print(f"  {label}: {valor}")
    print()

def exibir_menu() -> str:
    """Exibe menu principal."""
    print("\n" + "="*40)
    print("  📍 CONSULTA DE CEP")
    print("="*40)
    print("1️⃣  Buscar CEP")
    print("2️⃣  Buscar múltiplos CEPs")
    print("3️⃣  Ver histórico")
    print("4️⃣  Limpar histórico")
    print("5️⃣  Sair")
    print("="*40)
    
    opcao = input("Escolha uma opção (1-5): ").strip()
    return opcao

def exibir_menu_cep() -> str:
    """Exibe opções após buscar um CEP."""
    print("="*40)
    print("1️⃣  Buscar outro CEP")
    print("2️⃣  Abrir no Google Maps")
    print("3️⃣  Voltar ao menu")
    print("="*40)
    
    opcao = input("Escolha uma opção (1-3): ").strip()
    return opcao

def consultar_cep_unico() -> None:
    """Consulta um único CEP."""
    cep = input("\n📮 Digite o CEP (formato: 12345-678 ou 12345678): ").strip()

    try:
        cep_validado = validar_cep(cep)
        print("⏳ Consultando API...")
        endereco = buscar_endereco(cep_validado)
        historico.adicionar(cep_validado, endereco)
        formatar_endereco(endereco)
        
        while True:
            opcao = exibir_menu_cep()
            
            if opcao == "1":
                consultar_cep_unico()
                return
            elif opcao == "2":
                print("⏳ Gerando coordenadas...")
                time.sleep(0.5)
                abrir_google_maps(endereco)
            elif opcao == "3":
                return
            else:
                print("❌ Opção inválida. Tente novamente.\n")

    except (ValueError, LookupError) as e:
        logger.error(f"Erro: {e}")
        print(f"❌ {e}\n")
    except requests.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        print(f"❌ {e}\n")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        print(f"❌ Erro inesperado: {e}\n")

def consultar_multiplos_ceps() -> None:
    """Consulta múltiplos CEPs."""
    print("\n📮 Digite os CEPs (um por linha, vazio para finalizar):")
    
    ceps = []
    while True:
        cep = input("CEP: ").strip()
        if not cep:
            break
        ceps.append(cep)
    
    if not ceps:
        print("❌ Nenhum CEP digitado.\n")
        return

    print(f"\n⏳ Consultando {len(ceps)} CEP(s)...")
    
    enderecos = []
    for i, cep in enumerate(ceps, 1):
        try:
            cep_validado = validar_cep(cep)
            endereco = buscar_endereco(cep_validado)
            historico.adicionar(cep_validado, endereco)
            print(f"\n🔹 Resultado {i}/{len(ceps)}")
            formatar_endereco(endereco)
            enderecos.append(endereco)
            
            # Delay para evitar rate limiting
            if i < len(ceps):
                time.sleep(0.5)

        except (ValueError, LookupError) as e:
            logger.error(f"Erro: {e}")
            print(f"❌ CEP {cep}: {e}\n")
        except requests.RequestException as e:
            logger.error(f"Erro na requisição: {e}")
            print(f"❌ CEP {cep}: Erro na requisição\n")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            print(f"❌ CEP {cep}: {e}\n")
    
    if enderecos and input("\n🗺️  Deseja abrir os mapas no Google Maps? (s/n): ").strip().lower() == "s":
        for endereco in enderecos:
            abrir_google_maps(endereco)
            time.sleep(0.5)

def exibir_historico() -> None:
    """Exibe o histórico de buscas."""
    dados = historico.obter_todos()
    
    if not dados:
        print("\n📭 Histórico vazio.\n")
        return
    
    print(f"\n📋 --- Histórico de Buscas ({len(dados)} registros) ---")
    print("="*60)
    
    for i, entrada in enumerate(dados[-20:], 1):  # Mostra últimos 20
        cep = entrada.get("cep")
        data = entrada.get("data")
        endereco = entrada.get("endereco", {})
        logradouro = endereco.get("logradouro", "N/A")
        cidade = endereco.get("localidade", "N/A")
        
        print(f"{i}. CEP: {cep} | {logradouro}, {cidade}")
        print(f"   Data: {data}")
        print()
    
    if len(dados) > 20:
        print(f"... e mais {len(dados) - 20} registros")
    
    print("="*60)
    
    # Menu do histórico
    opcao = input("\n1️⃣  Ver detalhes | 2️⃣  Remover duplicatas | 3️⃣  Voltar: ").strip()
    
    if opcao == "1":
        tentar_cep = input("Digite um CEP para ver detalhes: ").strip()
        for entrada in dados:
            if entrada.get("cep") == tentar_cep:
                print("\n" + "="*60)
                formatar_endereco(entrada.get("endereco", {}))
                print(f"Data da busca: {entrada.get('data')}")
                print("="*60 + "\n")
                return
        print("❌ CEP não encontrado no histórico.\n")
    
    elif opcao == "2":
        historico.remover_duplicatas()
        print("✅ Duplicatas removidas com sucesso!\n")

def main():
    """Função principal com menu interativo."""
    print("\n" + "="*40)
    print("  Bem-vindo ao Consulta CEP!")
    print("="*40)
    
    while True:
        try:
            opcao = exibir_menu()

            if opcao == "1":
                consultar_cep_unico()
            elif opcao == "2":
                consultar_multiplos_ceps()
            elif opcao == "3":
                exibir_historico()
            elif opcao == "4":
                confirmacao = input("⚠️  Deseja limpar todo o histórico? (s/n): ").strip().lower()
                if confirmacao == "s":
                    historico.limpar()
                    print("✅ Histórico limpo!\n")
                else:
                    print("❌ Operação cancelada.\n")
            elif opcao == "5":
                print("\n👋 Até logo!\n")
                break
            else:
                print("❌ Opção inválida. Tente novamente.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Programa interrompido. Até logo!\n")
            break
        except Exception as e:
            logger.error(f"Erro na função principal: {e}")
            print(f"❌ Erro: {e}. Tente novamente.\n")

if __name__ == "__main__":
    main()
