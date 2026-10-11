"""Menu principal das simulações da ADO 2 de Física.

Execute com: python main.py

Cada simulação é iniciada em seu próprio processo. Assim, os módulos
mantêm seu próprio código e, quando a janela da simulação fecha, o menu
principal volta a aparecer.
"""

from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText


BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_RELATORIO = BASE_DIR / "report.md"

SIMULACOES = (
    {
        "numero": "01",
        "titulo": "Plano inclinado",
        "descricao": "Atrito, tração e movimento dos blocos",
        "arquivo": "friction_force.py",
    },
    {
        "numero": "02",
        "titulo": "Força centrípeta",
        "descricao": "Movimento circular uniforme",
        "arquivo": "centripetal_force.py",
    },
    {
        "numero": "03",
        "titulo": "Força de arrasto",
        "descricao": "Queda com resistência do ar",
        "arquivo": "drag_force.py",
    },
)

CORES = {
    "fundo": "#0C1424",
    "superficie": "#15233A",
    "superficie_hover": "#1C3050",
    "borda": "#293E5C",
    "texto": "#F0F6FF",
    "secundario": "#A5BAD3",
    "azul": "#64B5F6",
    "verde": "#78DBB4",
    "amarelo": "#F4C979",
}


class MenuFisica:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ADO 2 | Simulador de Física")
        self.root.configure(bg=CORES["fundo"])
        self.root.geometry("870x690")
        self.root.minsize(700, 650)
        self.processo_simulacao = None

        self._centralizar(self.root, 870, 690)
        self._montar_interface()

    @staticmethod
    def _centralizar(janela, largura, altura):
        tela_largura = janela.winfo_screenwidth()
        tela_altura = janela.winfo_screenheight()
        x = max(0, (tela_largura - largura) // 2)
        y = max(0, (tela_altura - altura) // 2)
        janela.geometry(f"{largura}x{altura}+{x}+{y}")

    def _montar_interface(self):
        principal = tk.Frame(self.root, bg=CORES["fundo"])
        principal.pack(fill="both", expand=True, padx=46, pady=(35, 25))

        tk.Label(
            principal,
            text="ADO 02  /  MECÂNICA E FÍSICA MODERNA",
            bg=CORES["fundo"],
            fg=CORES["azul"],
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            principal,
            text="Simulador de Física",
            bg=CORES["fundo"],
            fg=CORES["texto"],
            font=("Segoe UI", 27, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(12, 5))

        tk.Label(
            principal,
            text="Selecione um sistema para abrir sua simulação interativa.",
            bg=CORES["fundo"],
            fg=CORES["secundario"],
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(fill="x", pady=(0, 23))

        for item in SIMULACOES:
            self._criar_cartao(principal, item)

        tk.Frame(principal, height=1, bg=CORES["borda"]).pack(
            fill="x", pady=(15, 16)
        )

        botao_relatorio = tk.Button(
            principal,
            text="Ler relatório       →",
            command=self._abrir_relatorio,
            bg=CORES["azul"],
            fg=CORES["fundo"],
            activebackground="#8DCAFA",
            activeforeground=CORES["fundo"],
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=12,
        )
        botao_relatorio.pack(fill="x")

        tk.Label(
            principal,
            text="Ao fechar a janela de uma simulação, você retorna a este menu.",
            bg=CORES["fundo"],
            fg=CORES["secundario"],
            font=("Segoe UI", 10),
            anchor="center",
        ).pack(fill="x", pady=(16, 0))

    def _criar_cartao(self, pai, item):
        arquivo = BASE_DIR / item["arquivo"]
        disponivel = arquivo.is_file()
        cor_status = CORES["verde"] if disponivel else CORES["amarelo"]
        status = "DISPONÍVEL" if disponivel else "EM DESENVOLVIMENTO"

        cartao = tk.Frame(
            pai,
            bg=CORES["superficie"],
            highlightbackground=CORES["borda"],
            highlightthickness=1,
            cursor="hand2",
        )
        cartao.pack(fill="x", pady=(0, 11), ipady=14)

        numero = tk.Label(
            cartao,
            text=item["numero"],
            bg=CORES["superficie"],
            fg=CORES["azul"],
            font=("Segoe UI", 19, "bold"),
            width=5,
        )
        numero.pack(side="left", padx=(9, 1))

        coluna = tk.Frame(cartao, bg=CORES["superficie"])
        coluna.pack(side="left", fill="both", expand=True)

        titulo = tk.Label(
            coluna,
            text=item["titulo"],
            bg=CORES["superficie"],
            fg=CORES["texto"],
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        titulo.pack(fill="x")

        descricao = tk.Label(
            coluna,
            text=item["descricao"],
            bg=CORES["superficie"],
            fg=CORES["secundario"],
            font=("Segoe UI", 10),
            anchor="w",
        )
        descricao.pack(fill="x", pady=(3, 0))

        lateral = tk.Frame(cartao, bg=CORES["superficie"])
        lateral.pack(side="right", padx=(10, 22))

        etiqueta = tk.Label(
            lateral,
            text=status,
            bg=CORES["superficie"],
            fg=cor_status,
            font=("Segoe UI", 8, "bold"),
        )
        etiqueta.pack(anchor="e")
        seta = tk.Label(
            lateral,
            text="→",
            bg=CORES["superficie"],
            fg=CORES["azul"],
            font=("Segoe UI", 18),
        )
        seta.pack(anchor="e", pady=(3, 0))

        elementos = (cartao, numero, coluna, titulo, descricao, lateral, etiqueta, seta)

        def alterar_cor(cor):
            for elemento in elementos:
                elemento.configure(bg=cor)

        for elemento in elementos:
            elemento.bind("<Enter>", lambda _, cor=CORES["superficie_hover"]: alterar_cor(cor))
            elemento.bind("<Leave>", lambda _, cor=CORES["superficie"]: alterar_cor(cor))
            elemento.bind(
                "<Button-1>",
                lambda _, nome_arquivo=item["arquivo"]: self._abrir_simulacao(nome_arquivo),
            )

    def _abrir_simulacao(self, nome_arquivo):
        caminho = BASE_DIR / nome_arquivo
        if not caminho.is_file():
            messagebox.showinfo(
                "Simulação em desenvolvimento",
                f"O arquivo '{nome_arquivo}' ainda não existe.\n\n"
                "Crie esse arquivo na mesma pasta de main.py e o botão "
                "já estará pronto para abri-lo.",
                parent=self.root,
            )
            return

        try:
            self.processo_simulacao = subprocess.Popen(
                [sys.executable, str(caminho)], cwd=str(BASE_DIR)
            )
        except OSError as erro:
            messagebox.showerror(
                "Erro ao abrir a simulação",
                f"Não foi possível iniciar '{nome_arquivo}'.\n\n{erro}",
                parent=self.root,
            )
            return

        self.root.withdraw()  # Esconde o menu, sem encerrar o programa.
        self.root.after(200, self._verificar_simulacao)

    def _verificar_simulacao(self):
        if self.processo_simulacao is None:
            return

        resultado = self.processo_simulacao.poll()
        if resultado is None:
            self.root.after(200, self._verificar_simulacao)
            return

        self.processo_simulacao = None
        self.root.deiconify()  # A simulação fechou: mostra o menu novamente.
        self.root.lift()
        self.root.focus_force()

        if resultado != 0:
            messagebox.showwarning(
                "Simulação encerrada com erro",
                "A simulação não terminou normalmente. Verifique a mensagem "
                "de erro no terminal onde executou main.py.",
                parent=self.root,
            )

    def _abrir_relatorio(self):
        if not ARQUIVO_RELATORIO.is_file():
            messagebox.showinfo(
                "Relatório não encontrado",
                "Crie um arquivo chamado 'report.md' na mesma pasta de main.py.\n\n"
                "Depois, clique novamente neste botão para ler o conteúdo.",
                parent=self.root,
            )
            return

        try:
            conteudo = ARQUIVO_RELATORIO.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as erro:
            messagebox.showerror("Erro ao ler o relatório", str(erro), parent=self.root)
            return

        janela = tk.Toplevel(self.root)
        janela.title("ADO 2 | Relatório")
        janela.configure(bg=CORES["fundo"])
        janela.geometry("830x650")
        janela.minsize(500, 400)
        self._centralizar(janela, 830, 650)

        cabecalho = tk.Frame(janela, bg=CORES["fundo"])
        cabecalho.pack(fill="x", padx=25, pady=(20, 12))
        tk.Label(
            cabecalho,
            text="Relatório da atividade",
            bg=CORES["fundo"],
            fg=CORES["texto"],
            font=("Segoe UI", 19, "bold"),
        ).pack(side="left")

        tk.Label(
            cabecalho,
            text="report.md",
            bg=CORES["fundo"],
            fg=CORES["azul"],
            font=("Consolas", 10),
        ).pack(side="right")

        visualizador = ScrolledText(
            janela,
            wrap="word",
            bg=CORES["superficie"],
            fg=CORES["texto"],
            insertbackground=CORES["texto"],
            selectbackground=CORES["superficie_hover"],
            font=("Consolas", 11),
            relief="flat",
            padx=18,
            pady=15,
        )
        visualizador.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        visualizador.insert("1.0", conteudo)
        visualizador.configure(state="disabled")

        tk.Button(
            janela,
            text="Voltar ao menu",
            command=janela.destroy,
            bg=CORES["azul"],
            fg=CORES["fundo"],
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=9,
        ).pack(pady=(0, 20))

    def iniciar(self):
        self.root.mainloop()


if __name__ == "__main__":
    MenuFisica().iniciar()
