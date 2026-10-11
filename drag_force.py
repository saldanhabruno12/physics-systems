"""Simulação interativa de força de arrasto — ADO 2 de Física.

Execute diretamente com `python drag_force.py` ou pelo menu `main.py`.

Um objeto de massa m cai verticalmente sob a ação do peso (P = m*g) e de uma
força de arrasto que se opõe ao movimento. Dois modelos de arrasto são
oferecidos e comparados com a queda livre (sem arrasto):

    Linear:      F_arrasto = b * v      (b em kg/s)
    Quadrático:  F_arrasto = c * v**2   (c em kg/m)

Nenhuma integração numérica é usada: todas as grandezas vêm de fórmulas
fechadas avaliadas diretamente sobre um vetor de tempo (NumPy).
O movimento usa tempo real, independentemente da taxa de atualização do
Matplotlib.
"""

import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.transforms import offset_copy

G = 9.81

MODO_LINEAR = "linear"
MODO_QUADRATICO = "quadratico"


# ----------------------------------------------------------------------
# FÍSICA — QUEDA COM ARRASTO (fórmulas fechadas, sem integração numérica)
# ----------------------------------------------------------------------
def velocidade_terminal(m, coef, modo, g=G):
    """Velocidade terminal: quando o arrasto iguala o peso (a = 0).

    2ª Lei de Newton (eixo para baixo):  m*a = m*g - F_arrasto
    Em a = 0 temos F_arrasto = m*g, logo:
        linear:      b * v_t    = m*g  ->  v_t = m*g / b
        quadrático:  c * v_t**2 = m*g  ->  v_t = sqrt(m*g / c)
    """
    if modo == MODO_LINEAR:
        return m * g / coef
    return np.sqrt(m * g / coef)


def tempo_para_fracao(m, coef, modo, fracao=0.95, g=G):
    """Instante em que v(t) atinge `fracao` de v_terminal (ex.: 95%).

    Basta inverter v(t) = fracao * v_terminal:
        linear:      1 - exp(-t/tau) = fracao  ->  t = -tau * ln(1 - fracao)
        quadrático:  tanh(g*t/v_t)   = fracao  ->  t = (v_t/g) * arctanh(fracao)
    """
    if not 0.0 < fracao < 1.0:
        raise ValueError("A fração da velocidade terminal deve estar entre 0 e 1.")
    if modo == MODO_LINEAR:
        tau = m / coef
        return -tau * np.log(1.0 - fracao)
    v_term = velocidade_terminal(m, coef, modo, g)
    return (v_term / g) * np.arctanh(fracao)


def calcular_arrasto(m, coef, modo, t, g=G):
    """Calcula v(t), y(t) e as forças da queda com arrasto (equações fechadas).

    y(t) é a distância percorrida para baixo (y(0) = 0) e v(0) = 0.

    ARRASTO LINEAR  (m*dv/dt = m*g - b*v, solução da EDO):
        v_t = m*g / b           (velocidade terminal)
        tau = m / b             (constante de tempo)
        v(t) = v_t * (1 - exp(-t/tau))
        y(t) = v_t*t - v_t*tau*(1 - exp(-t/tau))      [integral exata de v]

    ARRASTO QUADRÁTICO  (m*dv/dt = m*g - c*v**2, solução da EDO):
        v_t = sqrt(m*g / c)
        v(t) = v_t * tanh(g*t / v_t)
        y(t) = (v_t**2 / g) * ln(cosh(g*t / v_t))     [integral exata de v]

    QUEDA LIVRE (sem arrasto, MRUV com a = g), usada como referência:
        v(t) = g*t        y(t) = g*t**2 / 2

    A aceleração instantânea sai direto da 2ª Lei:
        a = g - F_arrasto/m
    """
    if m <= 0 or coef <= 0 or g <= 0:
        raise ValueError("Use massa, coeficiente de arrasto e g positivos.")
    if modo not in (MODO_LINEAR, MODO_QUADRATICO):
        raise ValueError(f"Modo de arrasto desconhecido: {modo!r}")

    t = np.asarray(t, dtype=float)
    v_term = velocidade_terminal(m, coef, modo, g)

    if modo == MODO_LINEAR:
        tau = m / coef                          # constante de tempo (s)
        decaimento = np.exp(-t / tau)
        v = v_term * (1.0 - decaimento)
        y = v_term * t - v_term * tau * (1.0 - decaimento)
        F_arrasto = coef * v                    # |F| = b*v
    else:
        tau = v_term / g                        # escala de tempo (s)
        x = g * t / v_term
        v = v_term * np.tanh(x)
        # ln(cosh(x)) = ln(e^x + e^-x) - ln 2. O np.logaddexp calcula
        # exatamente isso sem estourar (np.cosh overflow para x > ~710).
        y = (v_term ** 2 / g) * (np.logaddexp(x, -x) - np.log(2.0))
        F_arrasto = coef * v ** 2               # |F| = c*v²

    a = g - F_arrasto / m                       # 2ª Lei de Newton

    # Referência: queda livre (sem arrasto)
    v_livre = g * t
    y_livre = 0.5 * g * t ** 2

    return dict(v=v, y=y, a=a, F_arrasto=F_arrasto, peso=m * g,
                v_term=v_term, tau=tau,
                v_livre=v_livre, y_livre=y_livre,
                t95=tempo_para_fracao(m, coef, modo, 0.95, g),
                t95_linear=tempo_para_fracao(m, coef, MODO_LINEAR, 0.95, g),
                t95_quad=tempo_para_fracao(m, coef, MODO_QUADRATICO, 0.95, g))


# ----------------------------------------------------------------------
# INTERFACE
# ----------------------------------------------------------------------
def main():
    init = dict(m=2.0, coef=0.5, g=G, T=20.0)
    estado = dict(res=None, t=None, tempo_atual=0.0, ultimo_relogio=None,
                  rodando=False, modo=MODO_LINEAR)

    fig = plt.figure(figsize=(13, 7.5))

    # cenário (esquerda) e gráficos (direita): mesmo estilo dos outros sistemas
    ax_sc = fig.add_axes([0.07, 0.36, 0.41, 0.49])
    ax_v = fig.add_axes([0.57, 0.60, 0.40, 0.25])
    ax_y = fig.add_axes([0.57, 0.31, 0.40, 0.22])
    texto = fig.text(0.5, 0.97, "", ha="center", va="top", fontsize=11)
    texto_agora = fig.text(0.07, 0.315, "", ha="left", va="top", fontsize=9.5,
                           family="monospace")

    # ---- cenário: duas colunas de queda (sem arrasto | com arrasto) ----
    ax_sc.set_xlim(-0.8, 1.8)
    ax_sc.xaxis.tick_top()
    ax_sc.set_xticks([0, 1])
    ax_sc.set_xticklabels(["Sem arrasto", "Com arrasto"])
    ax_sc.set_ylabel("distância de queda (m)")
    for lado in ("right", "bottom"):
        ax_sc.spines[lado].set_visible(False)
    ax_sc.grid(axis="y", alpha=0.3)

    (trilha_livre,) = ax_sc.plot([], [], color="gray", lw=1.5, ls="--")
    (trilha_arr,) = ax_sc.plot([], [], color="tab:blue", lw=1.5, ls="--")
    (bola_livre,) = ax_sc.plot([0], [0], "o", color="gray", mec="black", zorder=5)
    (bola_arr,) = ax_sc.plot([1], [0], "o", color="tab:blue", mec="black", zorder=5)

    # Setas de força na bola com arrasto. O comprimento é ilustrativo:
    # peso tem tamanho fixo e a seta de arrasto é proporcional a F_arrasto/P.
    # Quando atingem o mesmo tamanho, a = 0 (velocidade terminal).
    tr_peso = offset_copy(ax_sc.transData, fig=fig, x=16, units="points")
    tr_arrasto = offset_copy(ax_sc.transData, fig=fig, x=-16, units="points")

    def criar_seta(transformacao, cor):
        return ax_sc.annotate(
            "", xy=(1, 0), xycoords=transformacao,
            xytext=(0, 0), textcoords="offset points",
            arrowprops=dict(arrowstyle="<|-", color=cor, lw=2.2,
                            shrinkA=0, shrinkB=0),
            zorder=6)

    seta_peso = criar_seta(tr_peso, "tab:red")
    seta_arrasto = criar_seta(tr_arrasto, "tab:green")
    COMP_SETA = 48.0  # pontos (tamanho da seta do peso)
    ax_sc.text(0.02, 0.02, "Vermelho: peso    Verde: arrasto",
               transform=ax_sc.transAxes, fontsize=9, color="dimgray")

    # ---- gráficos ----
    linha_v_arr, = ax_v.plot([], [], color="tab:blue", lw=2, label="com arrasto")
    linha_v_livre, = ax_v.plot([], [], color="gray", ls="--", label="queda livre (g·t)")
    linha_vterm = ax_v.axhline(0, color="tab:green", ls=":", lw=1.8, label="v_terminal")
    ponto_95, = ax_v.plot([], [], "o", color="tab:red", zorder=5, label="95% de v_term")
    linha_y_arr, = ax_y.plot([], [], color="tab:blue", lw=2, label="com arrasto")
    linha_y_livre, = ax_y.plot([], [], color="gray", ls="--", label="queda livre")
    marc_v = ax_v.axvline(0, color="gray", ls="--")
    marc_y = ax_y.axvline(0, color="gray", ls="--")
    ax_v.set(title="Velocidade v(t)", ylabel="v (m/s)")
    ax_y.set(title="Distância percorrida y(t)", xlabel="t (s)", ylabel="y (m)")
    for ax in (ax_v, ax_y):
        ax.grid(alpha=0.3)

    # ---- controles ----
    def slider(y, label, vmin, vmax, vinit):
        ax = fig.add_axes([0.15, y, 0.50, 0.03])
        return Slider(ax, label, vmin, vmax, valinit=vinit)

    s_m = slider(0.20, "m (kg)", 0.1, 50.0, init["m"])
    s_coef = slider(0.15, "b (kg/s)", 0.05, 5.0, init["coef"])
    s_g = slider(0.10, "g (m/s²)", 1.0, 25.0, init["g"])
    s_T = slider(0.05, "T total (s)", 5.0, 40.0, init["T"])

    ax_radio = fig.add_axes([0.72, 0.105, 0.23, 0.10])
    ax_radio.set_title("Modelo de arrasto", fontsize=9, loc="left")
    radio = RadioButtons(ax_radio, ("Linear  (−b·v)", "Quadrático  (−c·v|v|)"),
                         active=0)
    MODOS = {"Linear  (−b·v)": MODO_LINEAR,
             "Quadrático  (−c·v|v|)": MODO_QUADRATICO}
    btn_play = Button(fig.add_axes([0.72, 0.03, 0.10, 0.055]), "Animar")
    btn_reset = Button(fig.add_axes([0.84, 0.03, 0.10, 0.055]), "Reiniciar")

    # O relógio real evita que atrasos do Matplotlib deixem a física lenta.
    def atualizar_relogio():
        if not estado["rodando"]:
            return
        agora = time.perf_counter()
        if estado["ultimo_relogio"] is not None:
            dt = max(0.0, agora - estado["ultimo_relogio"])
            estado["tempo_atual"] = min(s_T.val, estado["tempo_atual"] + dt)
        estado["ultimo_relogio"] = agora

    # desenho do cenário no instante atual
    def desenhar_cena():
        instante = estado["tempo_atual"]
        modo = estado["modo"]
        # Fórmula fechada avaliada diretamente no instante atual (sem passos).
        r = calcular_arrasto(s_m.val, s_coef.val, modo, np.array([instante]), s_g.val)
        y_arr = float(r["y"][0])
        y_livre = float(r["y_livre"][0])

        bola_livre.set_data([0], [y_livre])
        bola_arr.set_data([1], [y_arr])
        trilha_livre.set_data([0, 0], [0, y_livre])
        trilha_arr.set_data([1, 1], [0, y_arr])

        seta_peso.xy = (1, y_arr)
        seta_peso.xyann = (0, -COMP_SETA)
        proporcao = float(r["F_arrasto"][0] / r["peso"])
        seta_arrasto.xy = (1, y_arr)
        seta_arrasto.xyann = (0, max(proporcao, 0.02) * COMP_SETA)

        marc_v.set_xdata([instante, instante])
        marc_y.set_xdata([instante, instante])

        texto_agora.set_text(
            f"t = {instante:5.2f} s   v(arrasto) = {r['v'][0]:7.2f} m/s   "
            f"v(livre) = {r['v_livre'][0]:7.2f} m/s\n"
            f"a = {r['a'][0]:5.2f} m/s²   F_arrasto = {r['F_arrasto'][0]:8.2f} N   "
            f"P = {r['peso']:.2f} N")
        fig.canvas.draw_idle()

    # recalcula a física para todo o intervalo e atualiza tudo
    def recalcular():
        m, coef, g, T = s_m.val, s_coef.val, s_g.val, s_T.val
        modo = estado["modo"]
        t = np.linspace(0, T, 600)
        r = calcular_arrasto(m, coef, modo, t, g)
        estado["res"], estado["t"] = r, t

        linha_v_arr.set_data(t, r["v"])
        linha_v_livre.set_data(t, r["v_livre"])
        linha_vterm.set_ydata([r["v_term"], r["v_term"]])
        linha_y_arr.set_data(t, r["y"])
        linha_y_livre.set_data(t, r["y_livre"])
        ax_v.set_xlim(0, T)
        ax_y.set_xlim(0, T)

        # Ponto onde a curva atinge 95% de v_terminal (se couber em T)
        if r["t95"] <= T:
            ponto_95.set_data([r["t95"]], [0.95 * r["v_term"]])
        else:
            ponto_95.set_data([], [])
        ponto_95.set_label(f"95% de v_term (t = {r['t95']:.2f} s)")

        for ax in (ax_v, ax_y):
            ax.relim()
            ax.autoscale_view(scalex=False)
        ax_v.legend(loc="center right", fontsize=8)
        ax_y.legend(loc="upper left", fontsize=8)

        # Cenário: o eixo vai até onde a queda livre chega no instante T.
        ymax = r["y_livre"][-1]
        ax_sc.set_ylim(ymax * 1.05, -0.08 * ymax)  # folga no topo para as setas

        # Tamanho da bola cresce de leve com a massa (apenas ilustrativo).
        tamanho = 8 + 3.0 * m ** (1 / 3)
        bola_livre.set_markersize(tamanho)
        bola_arr.set_markersize(tamanho)

        if modo == MODO_LINEAR:
            rotulo_modelo = "Arrasto linear: F = b·v"
            formula_vt = "v_terminal = m·g/b"
        else:
            rotulo_modelo = "Arrasto quadrático: F = c·v²"
            formula_vt = "v_terminal = √(m·g/c)"
        pct = 100.0 * r["v"][-1] / r["v_term"]
        texto.set_text(
            f"{rotulo_modelo}   |   {formula_vt} = {r['v_term']:.2f} m/s   |   "
            f"v(T) = {r['v'][-1]:.2f} m/s ({pct:.1f}% de v_term)\n"
            f"Tempo para 95% de v_term (mesmos m e coeficiente):   "
            f"linear = {r['t95_linear']:.2f} s   |   "
            f"quadrático = {r['t95_quad']:.2f} s"
        )
        desenhar_cena()

    # animação (timer do próprio matplotlib)
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
        if estado["tempo_atual"] >= s_T.val:
            parar()

    timer.add_callback(tick)

    def alternar(_):
        if estado["rodando"]:
            atualizar_relogio()
            parar()
        else:
            if estado["tempo_atual"] >= s_T.val:
                estado["tempo_atual"] = 0.0
            estado["rodando"] = True
            estado["ultimo_relogio"] = time.perf_counter()
            btn_play.label.set_text("Pausar")
            timer.start()
        fig.canvas.draw_idle()

    def reiniciar(_):
        parar()
        estado["tempo_atual"] = 0.0
        desenhar_cena()

    def ao_mudar_slider(_):
        # As fórmulas fechadas partem de t = 0 (v0 = 0). Mudar um parâmetro
        # no meio da queda geraria um "salto", então reiniciamos a queda.
        parar()
        estado["tempo_atual"] = 0.0
        recalcular()

    def ao_mudar_modo(rotulo):
        estado["modo"] = MODOS[rotulo]
        s_coef.label.set_text("b (kg/s)" if estado["modo"] == MODO_LINEAR
                              else "c (kg/m)")
        ao_mudar_slider(None)

    for s in (s_m, s_coef, s_g, s_T):
        s.on_changed(ao_mudar_slider)
    radio.on_clicked(ao_mudar_modo)
    btn_play.on_clicked(alternar)
    btn_reset.on_clicked(reiniciar)

    recalcular()
    return dict(fig=fig, estado=estado, tick=tick, alternar=alternar,
                s_m=s_m, s_coef=s_coef, s_g=s_g, s_T=s_T, radio=radio,
                ao_mudar_modo=ao_mudar_modo,
                btn_play=btn_play, btn_reset=btn_reset)


if __name__ == "__main__":
    ui = main()
    plt.show()