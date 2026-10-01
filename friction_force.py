import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Polygon, Circle

G = 9.81

def calcular_plano_inclinado(m1, m2, theta_deg, mu_s, mu_k, t,
                             g=G, x0=0.0, v0=0.0):
    #  angulo precisa ser convertido para radianos
    #  para os proximos calculos
    th = np.radians(theta_deg)

    # aplicacao do calculo da forca normal
    N = m1 * g * np.cos(th)

    # aplicacao do calculo da forca motriz
    f_motriz = m2 * g - m1 * g * np.sin(th)

    # forca motriz <= fat
    if abs(f_motriz) <= mu_s * N:
        a = 0.0
        estado = "Equilíbrio estático"
    # forca motriz > fat
    else:
        a = (f_motriz - mu_k * N * np.sign(f_motriz)) / (m1 + m2)
        estado = "Em movimento"

    # calculo da posicao e velocidade tendo em maos o valor da aceleracao
    x = x0 + v0 * t + 0.5 * a * t ** 2
    v = v0 + a * t

    T = m2 * (g - a)


    mu_critico = abs(f_motriz) / N if N > 0 else np.inf

    return dict(a=a, T=T, N=N, f_motriz=f_motriz, estado=estado,
                x=x, v=v, mu_critico=mu_critico)


L_PLANO = 8.0        # comprimento do plano, medido a partir da polia
D0_M1 = 5.0          # distância inicial do centro de m1 até a polia (ao longo do plano)
S0_M2 = 2.0          # profundidade inicial do topo de m2 abaixo da polia
CHAO_Y = -8.4        # altura do chão
W1, H1 = 1.2, 0.8    # largura e altura do bloco m1
W2, H2 = 0.7, 0.9    # largura e altura do bloco m2
R_POLIA = 0.4        # raio da polia (= H1/2, para o fio ficar paralelo ao plano)


X_MIN = max(D0_M1 - (L_PLANO - W1 / 2), 0.4 - S0_M2)
X_MAX = min(D0_M1 - (W1 / 2 + 0.15), (-CHAO_Y - H2) - S0_M2)

# recebe angulo e deslocamento atual
def geometria_cena(theta_deg, x):
    """Devolve os pontos (polígonos e fio) do cenário para um deslocamento x."""
    # converte para radianos
    th = np.radians(theta_deg)
    u = np.array([-np.cos(th), -np.sin(th)])   # vetor ao longo do plano, descendo
    n = np.array([-np.sin(th), np.cos(th)])    # vetor normal que sai da superfície

    # plano_inclinado 
    plano_inclinado = np.array([[0, 0],
                      L_PLANO * u,
                      [L_PLANO * u[0], CHAO_Y],
                      [0, CHAO_Y]])

    # m1: retângulo apoiado no plano
    # distancia de m1 ate polia
    d = D0_M1 - x
    # centro do bloco m1
    c = d * u + (H1 / 2) * n

    bloco1 = np.array([c - (W1 / 2) * u - (H1 / 2) * n,
                       c + (W1 / 2) * u - (H1 / 2) * n,
                       c + (W1 / 2) * u + (H1 / 2) * n,
                       c - (W1 / 2) * u + (H1 / 2) * n])

    # profundidade de m2 em relacao a polia
    s2 = S0_M2 + x
    # x do centro de m2
    xc = R_POLIA

    bloco2 = np.array([[xc - W2 / 2, -s2], [xc + W2 / 2, -s2],
                       [xc + W2 / 2, -s2 - H2], [xc - W2 / 2, -s2 - H2]])

    # posicao do fio em m1
    ponto_m1 = c - (W1 / 2) * u

    # angulos do fio
    phi = np.linspace(np.pi / 2 + th, 0, 20)

    # circunferencia da polia
    arco = np.column_stack([R_POLIA * np.cos(phi), R_POLIA * np.sin(phi)])

    fio = np.vstack([ponto_m1, arco, [R_POLIA, -s2]])

    return plano_inclinado, bloco1, bloco2, fio, c


# ----------------------------------------------------------------------
# INTERFACE
# ----------------------------------------------------------------------
def main():
    t = np.linspace(0, 5, 300)
    init = dict(m1=2.0, m2=1.5, theta=30.0, mu=0.2)
    estado = dict(res=None, idx=0, rodando=False)

    fig = plt.figure(figsize=(13, 7.5))

    # cenario (esquerda) e graficos (direita)
    ax_sc = fig.add_axes([0.03, 0.30, 0.45, 0.55])
    ax_x = fig.add_axes([0.57, 0.60, 0.40, 0.25])
    ax_v = fig.add_axes([0.57, 0.31, 0.40, 0.22])
    texto = fig.text(0.5, 0.97, "", ha="center", va="top", fontsize=11)

    ax_sc.set_aspect("equal")
    ax_sc.set_xlim(-L_PLANO - 1, 3)
    ax_sc.set_ylim(CHAO_Y - 0.5, 2.0)
    ax_sc.axis("off")
    ax_sc.plot([-L_PLANO - 1, 3], [CHAO_Y, CHAO_Y], color="black", lw=1.5)
    p_plano_inclinado = Polygon(np.zeros((4, 2)), closed=True, fc="#cccccc", ec="black")
    p_m1 = Polygon(np.zeros((4, 2)), closed=True, fc="tab:blue", ec="black", zorder=3)
    p_m2 = Polygon(np.zeros((4, 2)), closed=True, fc="tab:orange", ec="black", zorder=3)
    for p in (p_plano_inclinado, p_m1, p_m2):
        ax_sc.add_patch(p)
    ax_sc.add_patch(Circle((0, 0), R_POLIA, fc="white", ec="black", zorder=4))
    (linha_fio,) = ax_sc.plot([], [], color="black", lw=1.5, zorder=2)
    rot_m1 = ax_sc.text(0, 0, "", ha="center", va="center", fontsize=9, zorder=5)
    rot_m2 = ax_sc.text(0, 0, "", ha="left", va="center", fontsize=9)
    aviso = ax_sc.text(0.5, 0.0, "", transform=ax_sc.transAxes, ha="center",
                       color="tab:red", fontsize=10)

    # graficos
    (linha_x,) = ax_x.plot(t, np.zeros_like(t), color="tab:blue")
    (linha_v,) = ax_v.plot(t, np.zeros_like(t), color="tab:red")
    marc_x = ax_x.axvline(0, color="gray", ls="--")
    marc_v = ax_v.axvline(0, color="gray", ls="--")
    ax_x.set(title="Posição x(t)", ylabel="x (m)")
    ax_v.set(title="Velocidade v(t)", xlabel="t (s)", ylabel="v (m/s)")
    for ax in (ax_x, ax_v):
        ax.grid(alpha=0.3)

    # sliders e botoes 
    def slider(y, label, vmin, vmax, vinit):
        ax = fig.add_axes([0.15, y, 0.50, 0.03])
        return Slider(ax, label, vmin, vmax, valinit=vinit)

    s_m1 = slider(0.20, "m1 (kg)", 0.1, 10.0, init["m1"])
    s_m2 = slider(0.15, "m2 (kg)", 0.1, 10.0, init["m2"])
    s_th = slider(0.10, "θ (graus)", 0.0, 80.0, init["theta"])
    s_mu = slider(0.05, "μ (μs = μk)", 0.0, 1.0, init["mu"])
    btn_play = Button(fig.add_axes([0.75, 0.15, 0.15, 0.06]), "Animar")
    btn_reset = Button(fig.add_axes([0.75, 0.07, 0.15, 0.06]), "Reiniciar")

    # desenho do cenario no instante atual 
    def desenhar_cena():
        r = estado["res"]
        idx = estado["idx"]
        x_real = r["x"][idx]
        x_vis = float(np.clip(x_real, X_MIN, X_MAX))
        plano_inclinado, b1, b2, fio, c1 = geometria_cena(s_th.val, x_vis)
        p_plano_inclinado.set_xy(plano_inclinado)
        p_m1.set_xy(b1)
        p_m2.set_xy(b2)
        linha_fio.set_data(fio[:, 0], fio[:, 1])
        n_th = np.radians(s_th.val)
        rot_m1.set_position(c1 + 0.8 * np.array([-np.sin(n_th), np.cos(n_th)]))
        rot_m1.set_text(f"m1 = {s_m1.val:.1f} kg")
        rot_m2.set_position((R_POLIA + W2 / 2 + 0.1, b2[:, 1].mean()))
        rot_m2.set_text(f"m2 = {s_m2.val:.1f} kg")
        aviso.set_text("Limite do cenário atingido" if x_real != x_vis else "")
        marc_x.set_xdata([t[idx], t[idx]])
        marc_v.set_xdata([t[idx], t[idx]])
        fig.canvas.draw_idle()

    # recalcula a fisica e atualiza tudo 
    def recalcular():
        r = calcular_plano_inclinado(s_m1.val, s_m2.val, s_th.val,
                                     s_mu.val, s_mu.val, t)
        estado["res"] = r
        linha_x.set_ydata(r["x"])
        linha_v.set_ydata(r["v"])
        for ax in (ax_x, ax_v):
            ax.relim()
            ax.autoscale_view()
        texto.set_text(
            f"{r['estado']}\n"
            f"a = {r['a']:.3f} m/s²   |   T = {r['T']:.3f} N   |   "
            f"N = {r['N']:.3f} N   |   μ crítico (teoria) = {r['mu_critico']:.3f}"
        )
        desenhar_cena()

    # animacao (timer do proprio matplotlib)
    timer = fig.canvas.new_timer(interval=15)

    def tick():
        if estado["idx"] >= len(t) - 1:
            parar()
        else:
            estado["idx"] += 1
            desenhar_cena()

    timer.add_callback(tick)

    def parar():
        timer.stop()
        estado["rodando"] = False
        btn_play.label.set_text("Animar")

    def alternar(_):
        if estado["rodando"]:
            parar()
        else:
            if estado["idx"] >= len(t) - 1:
                estado["idx"] = 0
            estado["rodando"] = True
            btn_play.label.set_text("Pausar")
            timer.start()
        fig.canvas.draw_idle()

    def reiniciar(_):
        parar()
        estado["idx"] = 0
        desenhar_cena()

    def ao_mudar_slider(_):
        parar()
        estado["idx"] = 0
        recalcular()

    for s in (s_m1, s_m2, s_th, s_mu):
        s.on_changed(ao_mudar_slider)
    btn_play.on_clicked(alternar)
    btn_reset.on_clicked(reiniciar)

    recalcular()
    
    return dict(fig=fig, estado=estado, tick=tick, alternar=alternar,
                s_m1=s_m1, s_m2=s_m2, s_th=s_th, s_mu=s_mu,
                btn_play=btn_play, btn_reset=btn_reset)


if __name__ == "__main__":
    ui = main()
    plt.show()
