import subprocess
import shutil
import random
import string
import docker
import time

Imagem = "gvenzl/oracle-xe"

def gerar_nome_container(prefixo="dbteste"):
    sufixo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefixo}-{sufixo}"

def criar_container_oracle_xe_com_nome_aleatorio(senha="1234", distro="Ubuntu"):
    global Imagem
    nome = gerar_nome_container()

    args = [
        "run", "-d",
        "--name", nome,
        "-p", "1521:1521",
        "-p", "5500:5500",
        "-e", f"ORACLE_PASSWORD={senha}",
        Imagem
    ]

    if docker_disponivel_no_windows():
        print("[INFO] Executando Docker no Windows")
        try:
            result = subprocess.run(["docker"] + args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("[DOCKER OUTPUT - WIN]", result.stdout)
        except subprocess.CalledProcessError as e:
            print("[ERRO - DOCKER WIN]", e.stderr)
    else:
        comando = "docker " + " ".join(args)
        executar_comando_docker(comando, distro)

    return nome

def docker_disponivel_no_windows():
    return shutil.which("docker") is not None

def docker_disponivel_no_wsl(distro="Ubuntu"):
    try:
        cmd = ["wsl", "-d", distro, "--", "docker", "version"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except Exception:
        return False

def executar_comando_docker(comando_docker, distro="Ubuntu"):
    print(f"[INFO] Verificando ambiente Docker...")

    if docker_disponivel_no_windows():
        print("[INFO] Docker disponível no Windows (nativo).")
        try:
            args = comando_docker.strip().split()
            result = subprocess.run(["docker"] + args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("[DOCKER OUTPUT - WINDOWS]\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print("[ERRO - DOCKER WIN]", e.stderr)

    elif docker_disponivel_no_wsl(distro):
        print(f"[INFO] Docker disponível no WSL ({distro}).")
        try:
            cmd = ["wsl", "-d", distro, "--", "sh", "-c", comando_docker]
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("[DOCKER OUTPUT - WSL]\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print("[ERRO - DOCKER WSL]", e.stderr)
    else:
        print("[FALHA] Docker não disponível nem no Windows nem no WSL.")

def remover_containers_dbteste(distro="Ubuntu"):
    comando = (
        "docker ps -a --format '{{.Names}}' | grep '^dbteste-' | xargs -r docker rm -f"
    )
    print("[INFO] Removendo containers com prefixo 'dbteste-'...")
    executar_comando_docker(comando, distro)

def stop_and_create_container():
    executar_comando_docker("pull " + Imagem, distro="Ubuntu")
    subprocess.run("for /f %i in ('docker ps -q') do docker stop %i", shell=True)
    container_name = criar_container_oracle_xe_com_nome_aleatorio()

def aguardar_container_healthy(container_name, timeout=120, intervalo=5):
    client = docker.from_env()
    tempo_total = 0

    print(f"[DOCKER] Aguardando container {container_name} ficar healthy...")

    while tempo_total < timeout:
        try:
            container = client.containers.get(container_name)
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")

            if status == "healthy":
                print(f"[DOCKER] Container {container_name} está healthy!")
                return True
            elif status == "unhealthy":
                print(f"[DOCKER] Container {container_name} está unhealthy.")
                return False
            else:
                print(f"[DOCKER] Status atual: {status or 'N/A'}... aguardando...")
        except Exception as e:
            print(f"[ERRO] Falha ao verificar status do container {container_name}: {e}")
            return False

        time.sleep(intervalo)
        tempo_total += intervalo

    print(f"[TIMEOUT] Container {container_name} não ficou healthy em {timeout} segundos.")
    return False
