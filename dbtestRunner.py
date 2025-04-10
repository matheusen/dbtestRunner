import json
import os
import time
import subprocess
from random import randint
import re
from utils import converter_html_para_pdf
from connectOracle import run_oracle_update
from execDockerCommands import stop_and_create_container, aguardar_container_healthy

def carregar_config(caminho="repos_config.json"):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def rodar_comando_maven_cmd(caminho_projeto, comandos):
    for comando in comandos:
        linha_cmd = f"mvn {' '.join(comando)}"
        print(f"[CMD] Executando: {linha_cmd} em {caminho_projeto}")

        try:
            resultado = subprocess.run(linha_cmd, cwd=caminho_projeto, shell=True, capture_output=True, text=True)
            print("[OUTPUT]", resultado.stdout)
            if resultado.returncode != 0:
                print("[ERRO]", resultado.stderr)

            # Após o comando, verificar se HTML existe e converter
            report_path = os.path.join(caminho_projeto, "target", "surefire-reports", "index.html")
            if os.path.exists(report_path):
                safe_name = '_'.join(comando).replace("=", "-").replace(" ", "_")
                status = analisar_html_teste(report_path)
                pdf_path = os.path.join("relatorios_pdf", f"{safe_name}_{status}.pdf")
                converter_html_para_pdf(report_path, pdf_path)
                print(f"📄 Relatório convertido para PDF: {pdf_path} ({status})")
            else:
                print("⚠️ Relatório HTML não encontrado após comando Maven.")

        except Exception as e:
            print(f"[ERRO EXECUCAO CMD] {e}")
            return False

    return True

def analisar_html_teste(caminho_html):
    try:
        with open(caminho_html, encoding="utf-8") as f:
            conteudo = f.read()
            if re.search(r"Tests run: \d+, Failures: 0, Errors: 0", conteudo):
                return "SUCESSO"
            return "FALHA"
    except Exception as e:
        print(f"[ERRO] Ao analisar HTML: {e}")
        return "ERRO"

def preparar_ambiente(repo):
    nome = repo["nome"]
    imagem = repo["imagem"]
    container_name = f"dbteste-{nome}-{randint(1000, 9999)}"

    print(f"\n🔄 Criando novo container para {nome}: {container_name}")
    stop_and_create_container(container_name, imagem, ports={"1521": "1521", "5500": "5500"})
    print("⏳ Aguardando container ficar healthy...")
    if aguardar_container_healthy(container_name):
        print("✅ Container pronto. Aplicando alterações no Oracle...")
        run_oracle_update()
        return container_name
    else:
        print(f"❌ Container {container_name} não ficou healthy a tempo.")
        return None

def executar_grupos_de_testes(repo, caminho_local, comandos_para_rodar):
    return rodar_comando_maven_cmd(caminho_local, comandos_para_rodar)

def executar_teste_por_repositorio(repo, log_fn=print):
    nome = repo["nome"]
    caminho_local = repo["caminho"]
    grupos = repo["grupos_de_testes"]
    max_por_container = repo.get("docker_por_grupo", 5)

    print(f"\n🚀 Iniciando testes para {nome}")

    if not os.path.exists(os.path.join(caminho_local, "pom.xml")):
        print(f"[ERRO] Projeto {nome} não possui pom.xml em {caminho_local}. Pulando...")
        return

    grupos_rodados = 0
    comandos_para_rodar = []

    for grupo in grupos:
        comandos_para_rodar.append(["test", f"-P{grupo}"])
        grupos_rodados += 1

        if grupos_rodados % max_por_container == 0 or grupo == grupos[-1]:
            container = preparar_ambiente(repo)
            if not container:
                print(f"❌ Ambiente falhou para {nome}. Pulando repositório.")
                break
            sucesso = executar_grupos_de_testes(repo, caminho_local, comandos_para_rodar)
            comandos_para_rodar.clear()
            if not sucesso:
                print(f"❌ Falha ao rodar testes em {nome}. Encerrando execução para esse repositório.\n")
                break

