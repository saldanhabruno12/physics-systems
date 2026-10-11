import sys
import runpy
import subprocess
from pathlib import Path

if len(sys.argv) >= 3 and sys.argv[1] == "--simulation":
    arquivo = Path(__file__).resolve().parent / sys.argv[2]
    runpy.run_path(str(arquivo), run_name="__main__")
else:
    import main
    from tkinter import messagebox

    original = main.MenuFisica._abrir_simulacao

    def abrir_simulacao(self, nome_arquivo):
        if not getattr(sys, "frozen", False):
            return original(self, nome_arquivo)

        caminho = main.BASE_DIR / nome_arquivo

        if not caminho.is_file():
            messagebox.showerror("Erro", f"Arquivo não encontrado: {nome_arquivo}")
            return

        try:
            self.processo_simulacao = subprocess.Popen(
                [sys.executable, "--simulation", nome_arquivo],
                cwd=str(main.BASE_DIR)
            )
            self.root.withdraw()
            self.root.after(200, self._verificar_simulacao)
        except OSError as erro:
            messagebox.showerror("Erro", str(erro))

    main.MenuFisica._abrir_simulacao = abrir_simulacao
    main.MenuFisica().iniciar()
