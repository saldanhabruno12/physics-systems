"""Simulação interativa de força centrípeta — ADO 2 de Física.

Execute diretamente com `python centripetal_force.py` ou pelo menu `main.py`.
O movimento usa tempo real, independentemente da taxa de atualização do Matplotlib.
"""

import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Circle, FancyArrowPatch


# ----------------------------------------------------------------------
# FÍSICA — MOVIMENTO CIRCULAR UNIFORME
# ----------------------------------------------------------------------
def calcular_forca_centripeta(m, R, v, t, fase_inicial=0.0):
    """Calcula as grandezas do MCU com equações fechadas (sem integração).

    Pela 2ª Lei de Newton na direção radial:
        F_c = m * a_c = m * v**2 / R

    Cinemática do MCU:
        omega = v / R
        x(t) = R * cos(omega*t + fase_inicial)
        y(t) = R * sin(omega*t + fase_inicial)

    A fase_inicial é zero no início; se o usuário alterar um slider durante
    a execução, ela preserva a posição angular atual, evitando "teleporte".
    """
    if m <= 0 or R <= 0 or v < 0:
        raise ValueError("Use massa e raio positivos e velocidade não negativa.")

    t = np.asarray(t, dtype=float)
    omega = v / R                     # velocidade angular (rad/s)
    a_c = v ** 2 / R                  # aceleração centrípeta (m/s²)
    F_c = m * a_c                     # força centrípeta (N)
    phi = fase_inicial + omega * t    # ângulo em função do tempo
    x = R * np.cos(phi)
    y = R * np.sin(phi)
    periodo = (2 * np.pi / omega) if omega > 0 else np.inf

    return dict(x=x, y=y, omega=omega, a_c=a_c, F_c=F_c,
                periodo=periodo, phi=phi)


# ----------------------------------------------------------------------
# INTERFACE
# ----------------------------------------------------------------------
def main():
    t = np.linspace(0, 10, 600)
    tempo_final = float(t[-1])
    init = dict(m=2.0, R=2.5, v=3.0)
    estado = dict(res=None, tempo_atual=0.0, ultimo_relogio=None,
                  fase_inicial=0.0, rodando=False)

    fig = plt.figure(figsize=(13, 7.5))

    # Cenário à esquerda e gráficos à direita: mesmo estilo do plano inclinado
    ax_sc = fig.add_axes([0.03, 0.30, 0.45, 0.55])
    ax_x = fig.add_axes([0.57, 0.60, 0.40, 0.25])
    ax_y = fig.add_axes([0.57, 0.31, 0.40, 0.22])
    texto = fig.text(0.5, 0.97, "", ha="center", va="top", fontsize=11)

    ax_sc.set_aspect("equal")
    ax_sc.set_xlim(-5.8, 5.8)
    ax_sc.set_ylim(-5.8, 5.8)
    ax_sc.axis("off")

    (linha_trajetoria,) = ax_sc.plot([], [], "--", color="gray", lw=1.5)
    (linha_raio,) = ax_sc.plot([], [], color="black", lw=1.5)
    ponto_centro = Circle((0, 0), 0.09, fc="black", ec="black", zorder=4)
    p_massa = Circle((0, 0), 0.24, fc="tab:blue", ec="black", zorder=5)
    ax_sc.add_patch(ponto_centro)
    ax_sc.add_patch(p_massa)

    # Setas: vermelho para o centro (força) e laranja tangente (velocidade)
    seta_forca = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>",
                                 mutation_scale=16, lw=2, color="tab:red", zorder=6)
    seta_velocidade = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>",
                                      mutation_scale=16, lw=2, color="tab:orange", zorder=6)
    ax_sc.add_patch(seta_forca)
    ax_sc.add_patch(seta_velocidade)

    rot_massa = ax_sc.text(0, 0, "", ha="left", va="center", fontsize=9, zorder=7)
    ax_sc.text(0.03, 0.03, "Azul: massa    Vermelho: força    Laranja: velocidade",
               transform=ax_sc.transAxes, fontsize=9, color="dimgray")

    (linha_x,) = ax_x.plot(t, np.zeros_like(t), color="tab:blue")
    (linha_y,) = ax_y.plot(t, np.zeros_like(t), color="tab:red")
    marc_x = ax_x.axvline(0, color="gray", ls="--")
    marc_y = ax_y.axvline(0, color="gray", ls="--")
    ax_x.set(title="Posição x(t)", ylabel="x (m)")
    ax_y.set(title="Posição y(t)", xlabel="t (s)", ylabel="y (m)")
    for ax in (ax_x, ax_y):
        ax.grid(alpha=0.3)

    def slider(y, label, vmin, vmax, vinit):
        ax = fig.add_axes([0.15, y, 0.50, 0.03])
        return Slider(ax, label, vmin, vmax, valinit=vinit)

    s_m = slider(0.20, "m (kg)", 0.1, 10.0, init["m"])
    s_R = slider(0.15, "R (m)", 0.5, 5.0, init["R"])
    s_v = slider(0.10, "v (m/s)", 0.0, 10.0, init["v"])
    btn_play = Button(fig.add_axes([0.75, 0.15, 0.15, 0.06]), "Animar")
    btn_reset = Button(fig.add_axes([0.75, 0.07, 0.15, 0.06]), "Reiniciar")

    # O relógio real evita que atrasos do Matplotlib deixem a física lenta.
    # Avançamos pelo tempo transcorrido, não "um índice por frame".
    def atualizar_relogio():
        if not estado["rodando"]:
            return
        agora = time.perf_counter()
        if estado["ultimo_relogio"] is not None:
            dt = max(0.0, agora - estado["ultimo_relogio"])
            estado["tempo_atual"] = min(tempo_final, estado["tempo_atual"] + dt)
        estado["ultimo_relogio"] = agora

    def desenhar_cena():
        r = estado["res"]
        instante = estado["tempo_atual"]
        angulo = estado["fase_inicial"] + r["omega"] * instante
        raio = s_R.val
        x_atual = raio * np.cos(angulo)
        y_atual = raio * np.sin(angulo)

        linha_raio.set_data([0, x_atual], [0, y_atual])
        p_massa.center = (x_atual, y_atual)
        rot_massa.set_position((x_atual + 0.35, y_atual + 0.35))
        rot_massa.set_text(f"m = {s_m.val:.1f} kg")

        radial = np.array([np.cos(angulo), np.sin(angulo)])
        tangente = np.array([-np.sin(angulo), np.cos(angulo)])
        centro_massa = np.array([x_atual, y_atual])

        # O tamanho das setas é ilustrativo e aumenta com v / F_c.
        comprimento_forca = min(raio * 0.75, 0.45 + 0.08 * np.sqrt(r["F_c"]))
        comprimento_vel = min(raio * 0.75, 0.20 + 0.13 * s_v.val)
        seta_forca.set_positions(centro_massa,
                                 centro_massa - comprimento_forca * radial)
        seta_velocidade.set_positions(centro_massa,
                                      centro_massa + comprimento_vel * tangente)
        seta_forca.set_visible(r["F_c"] > 0)
        seta_velocidade.set_visible(s_v.val > 0)

        marc_x.set_xdata([instante, instante])
        marc_y.set_xdata([instante, instante])
        fig.canvas.draw_idle()

    def recalcular():
        r = calcular_forca_centripeta(s_m.val, s_R.val, s_v.val, t,
                                      fase_inicial=estado["fase_inicial"])
        estado["res"] = r
        linha_x.set_ydata(r["x"])
        linha_y.set_ydata(r["y"])

        # A trajetória geométrica depende apenas do raio: não redesenhar a
        # circunferência inteira a cada atualização de animação.
        phi_circulo = np.linspace(0, 2 * np.pi, 250)
        linha_trajetoria.set_data(s_R.val * np.cos(phi_circulo),
                                  s_R.val * np.sin(phi_circulo))

        for ax in (ax_x, ax_y):
            ax.relim()
            ax.autoscale_view()

        periodo_txt = f"{r['periodo']:.2f} s" if np.isfinite(r["periodo"]) else "sem movimento"
        texto.set_text(
            "Movimento circular uniforme (MCU)\n"
            f"v = {s_v.val:.2f} m/s   |   tempo por volta = {periodo_txt}   |   "
            f"ω = {r['omega']:.2f} rad/s\n"
            f"F centrípeta = {r['F_c']:.2f} N   |   "
            f"a centrípeta = {r['a_c']:.2f} m/s²"
        )
        desenhar_cena()

    # 30 quadros por segundo é suficiente para ver o movimento claramente.
    # A velocidade física não depende dessa taxa: é determinada pelo relógio.
    timer = fig.canvas.new_timer(interval=33)

    def parar():
        timer.stop()
        estado["rodando"] = False
        estado["ultimo_relogio"] = None
        btn_play.label.set_text("Animar")

    def tick():
        if not estado["rodando"]:
            return
        atualizar_relogio()
        desenhar_cena()
        if estado["tempo_atual"] >= tempo_final:
            parar()

    timer.add_callback(tick)

    def alternar(_):
        if estado["rodando"]:
            atualizar_relogio()
            parar()
        else:
            if estado["tempo_atual"] >= tempo_final:
                estado["tempo_atual"] = 0.0
                estado["fase_inicial"] = 0.0
                recalcular()
            estado["rodando"] = True
            estado["ultimo_relogio"] = time.perf_counter()
            btn_play.label.set_text("Pausar")
            timer.start()
        fig.canvas.draw_idle()

    def reiniciar(_):
        parar()
        estado["tempo_atual"] = 0.0
        estado["fase_inicial"] = 0.0
        recalcular()

    def ao_mudar_slider(_):
        # Mudar o parâmetro não pausa mais a simulação.
        # Conserva o ângulo atual para alterar a velocidade sem dar saltos.
        atualizar_relogio()
        r_anterior = estado["res"]
        angulo_atual = (estado["fase_inicial"] + r_anterior["omega"] *
                        estado["tempo_atual"])
        nova_omega = s_v.val / s_R.val
        estado["fase_inicial"] = angulo_atual - nova_omega * estado["tempo_atual"]
        recalcular()

    for s in (s_m, s_R, s_v):
        s.on_changed(ao_mudar_slider)
    btn_play.on_clicked(alternar)
    btn_reset.on_clicked(reiniciar)

    recalcular()
    return dict(fig=fig, estado=estado, tick=tick, alternar=alternar,
                s_m=s_m, s_R=s_R, s_v=s_v,
                btn_play=btn_play, btn_reset=btn_reset)


if __name__ == "__main__":
    ui = main()
    plt.show()
