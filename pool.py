import requests
import os
import subprocess
import re
import requests

API_URL = "https://bitcoinflix.replit.app/api/big_block"
POOL_TOKEN = "0a0a8104a4109f1fd2029a33b2c2c2dc5896289e6e3401f9e2044b24ea0e2ae8"
ADDITIONAL_ADDRESS = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"

def clear_screen():
    """Limpa a tela do terminal."""
    os.system("cls" if os.name == "nt" else "clear")

session = requests.Session()

def fetch_block_data():
    headers = {"pool-token": POOL_TOKEN}
    try:
        response = session.get(API_URL, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erro ao fazer a requisição: {e}")
        return None

def save_addresses_to_file(addresses, additional_address, filename="in.txt"):
    try:
        with open(filename, "w") as file:
            for address in addresses:
                file.write(address + "\n")
            file.write(additional_address + "\n")  # Adicionando o endereço adicional
        # print(f"Endereços salvos com sucesso no arquivo '{filename}'.")
    except Exception as e:
        print(f"Erro ao salvar endereços no arquivo: {e}")

def clear_file(filename):
    try:
        with open(filename, "w") as file:
            pass
        # print(f"Arquivo '{filename}' limpo com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar o arquivo '{filename}': {e}")

def run_program(start, end):
    keyspace = f"{start}:{end}"
    command = [
        "./vanitysearch",
        "-t", "0",
        "-gpu",
        "-gpuId", "0,1",
        "-g", "1536",
        "-i", "in.txt",
        "-o", "out.txt",
        "--keyspace", keyspace
    ]
    try:
        # print(f"Executando o programa com keyspace {keyspace}...")
        subprocess.run(command, check=True)
        # print("Programa executado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o programa: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def post_private_keys(private_keys):
    headers = {
        "pool-token": POOL_TOKEN,
        "Content-Type": "application/json"
    }
    data = {"privateKeys": private_keys}
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code != 200:
            # print(f"Chaves privadas enviadas com sucesso.")
        # else:
            print(f"Erro ao enviar chaves privadas: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Erro ao fazer a requisição POST: {e}")

def process_out_file(out_file="out.txt", in_file="in.txt", additional_address=ADDITIONAL_ADDRESS):
    if not os.path.exists(out_file):
        print(f"Arquivo '{out_file}' não encontrado.")
        return False

    if not os.path.exists(in_file):
        print(f"Arquivo '{in_file}' não encontrado.")
        return False

    private_keys = {}
    found_additional_address = False

    try:
        with open(out_file, "r") as file:
            content = file.read()
        
        # Expressão regular para capturar endereço e chave privada
        matches = re.findall(r"Pub Addr:\s+(\S+).*?Priv \(HEX\):\s+(\S+)", content, re.DOTALL)
        private_keys = {addr[-20:]: key for addr, key in matches}
        
        # Verificando se a chave do endereço adicional foi encontrada
        additional_address_short = additional_address[-20:]
        if additional_address_short in private_keys:
            found_additional_address = True

        if found_additional_address:
            print(f"Chave encontrada: {private_keys[additional_address_short]}")
            return True

        # Ordenar as chaves antes de enviar
        with open(in_file, "r") as file:
            addresses = [line.strip()[-20:] for line in file if line.strip()]
        
        ordered_private_keys = [private_keys[addr] for addr in addresses if addr in private_keys]
        
        for i in range(0, len(ordered_private_keys), 10):
            batch = ordered_private_keys[i:i + 10]
            if batch:
                post_private_keys(batch)

    except Exception as e:
        print(f"Erro ao processar os arquivos: {e}")

    # Limpar arquivo ao final
    clear_file(out_file)
    return False

# Loop Principal
if __name__ == "__main__":
    while True:
        clear_screen()
        block_data = fetch_block_data()
        if block_data:
            addresses = block_data.get("checkwork_addresses", [])
            if addresses:
                save_addresses_to_file(addresses, ADDITIONAL_ADDRESS)
                
                # Extraindo start e end do range
                range_data = block_data.get("range", {})
                start = range_data.get("start", "").replace("0x", "")
                end = range_data.get("end", "").replace("0x", "")
                
                if start and end:
                    run_program(start, end)
                    if process_out_file():
                        break
                else:
                    print("Erro: Start ou End não encontrado no range.")
            else:
                print("Nenhum endereço encontrado no bloco.")
        else:
            print("Erro ao buscar dados do bloco.")
