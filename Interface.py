import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from dbtestRunner import executar_teste_por_repositorio, preparar_ambiente, carregar_config

CONFIG_PATH = "repos_config.json"

class DBTestRunnerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("DBTest Runner")
        self.master.geometry("640x480")  # Aumenta o tamanho da janela principal
        self.frame = ttk.Frame(master, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.repos = carregar_config(CONFIG_PATH)
        self.repo_frames = []

        save_button = ttk.Button(self.frame, text="💾 Salvar Configurações", command=self.salvar_configuracoes)
        save_button.pack(side=tk.TOP, pady=10)

        self.scroll_canvas = tk.Canvas(self.frame)
        self.scroll_y = ttk.Scrollbar(self.frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scroll_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox("all")
            )
        )

        self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=self.scroll_y.set)

        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")

        self.carregar_interfaces_por_repo()

    def carregar_interfaces_por_repo(self):
        def criar_adicionar_container(container_entries, frame):
            def remover(container_frame, cmd_var):
                container_frame.destroy()
                container_entries.remove(cmd_var)
            def adicionar():
                container_frame = ttk.LabelFrame(frame, text=f"Container {len(container_entries) + 1}", padding=5)
                container_frame.pack(fill=tk.X, pady=2)
                cmd_var = tk.StringVar()
                cmd_entry = ttk.Entry(container_frame, textvariable=cmd_var, width=100)
                cmd_entry.pack(anchor="w")
                remove_button = ttk.Button(container_frame, text="🗑 Remover", command=lambda: remover(container_frame, cmd_var))
                remove_button.pack(anchor="e")
                container_entries.append(cmd_var)
            return adicionar
        self.repo_frames.clear()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for repo in self.repos:
            frame = ttk.LabelFrame(self.scrollable_frame, text=repo["nome"], padding=10)
            frame.pack(fill=tk.X, pady=5)

            caminho_var = tk.StringVar(value=repo.get("caminho", ""))
            ttk.Label(frame, text="📁 Caminho local:").pack(anchor="w")
            caminho_entry = ttk.Entry(frame, textvariable=caminho_var, width=80)
            caminho_entry.pack(anchor="w")

            ttk.Label(frame, text="🐳 Imagem Docker:").pack(anchor="w")
            imagem_var = tk.StringVar(value=repo.get("imagem", ""))
            imagem_entry = ttk.Entry(frame, textvariable=imagem_var, width=40)
            imagem_entry.pack(anchor="w")

            ttk.Label(frame, text="🧪 Comandos Maven por Container:").pack(anchor="w")
            container_cmds = repo.get("comandos_por_container", [])
            container_entries = []

            for idx, grupo in enumerate(container_cmds):
                container_frame = ttk.LabelFrame(frame, text=f"Container {idx + 1}", padding=5)
                container_frame.pack(fill=tk.X, pady=2)
                cmd_var = tk.StringVar(value=";".join(grupo))
                cmd_entry = ttk.Entry(container_frame, textvariable=cmd_var, width=100)
                cmd_entry.pack(anchor="w")
                remove_button = ttk.Button(container_frame, text="🗑 Remover", command=lambda f=container_frame, v=cmd_var: (f.destroy(), container_entries.remove(v)))
                remove_button.pack(anchor="e")
                container_entries.append(cmd_var)

            def adicionar_container():
                container_frame = ttk.LabelFrame(frame, text=f"Container {len(container_entries) + 1}", padding=5)
                container_frame.pack(fill=tk.X, pady=2)
                cmd_var = tk.StringVar()
                cmd_entry = ttk.Entry(container_frame, textvariable=cmd_var, width=100)
                cmd_entry.pack(anchor="w")
                container_entries.append(cmd_var)

            ttk.Button(frame, text="➕ Adicionar Container", command=criar_adicionar_container(container_entries, frame)).pack(pady=5)

            run_button = ttk.Button(frame, text="▶️ Rodar DBTestes", command=lambda r=repo: self.executar_testes_thread(r))
            run_button.pack(pady=5)

            self.repo_frames.append({
                "repo": repo,
                "caminho_var": caminho_var,
                "imagem_var": imagem_var,
                "cmd_vars": container_entries
            })

    def salvar_configuracoes(self):
        novos_dados = []
        for frame in self.repo_frames:
            repo = frame["repo"]
            repo["caminho"] = frame["caminho_var"].get()
            repo["imagem"] = frame["imagem_var"].get()
            repo["comandos_por_container"] = [v.get().split(";") for v in frame["cmd_vars"]]
            novos_dados.append(repo)

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(novos_dados, f, indent=2)
        messagebox.showinfo("Configurações", "Configurações salvas com sucesso!")

    def executar_testes_thread(self, repo):
        threading.Thread(target=self.executar_teste, args=(repo,), daemon=True).start()

    def executar_teste(self, repo):
        nome = repo["nome"]
        print(f"\n🚀 Iniciando testes para {nome}")
        try:
            executar_teste_por_repositorio(repo)
            print(f"✅ Testes finalizados para {nome}")
        except Exception as e:
            print(f"❌ Erro ao executar testes para {nome}: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DBTestRunnerUI(root)
    root.mainloop()
