# Relatório — ADO 2: Leis de Newton e Aplicações

**Disciplina:** Mecânica e Física Moderna — Ciência da Computação  
**Integrantes:** William Silva Guimarães · Henry Sant Anna Meneses · Bruno Oliveira Alves · Bruno Saldanha

## Introdução

O grupo implementou os três sistemas propostos — **plano inclinado com atrito e tração**, **força centrípeta** e **força de arrasto** — como simulações interativas em Python. Todas as grandezas são calculadas com fórmulas fechadas avaliadas sobre um vetor de tempo com NumPy, **sem nenhum método de integração numérica**.

O programa é organizado em quatro arquivos:

| Arquivo | Função |
|---|---|
| `main.py` | Menu em tkinter para escolher o sistema; cada simulação abre em um processo próprio e o menu reaparece quando a janela é fechada. |
| `friction_force.py` | Plano inclinado: sliders de $m_1$, $m_2$, $\theta$ e $\mu$ ($\mu_s = \mu_k$); mostra aceleração, tração, normal, estado do sistema e $\mu$ crítico. |
| `centripetal_force.py` | Movimento circular uniforme (MCU): sliders de $m$, $R$ e $v$; mostra $\omega$, período, aceleração e força centrípeta. |
| `drag_force.py` | Queda com arrasto: sliders de $m$, $b$ ou $c$, $g$ e tempo total; seletor linear/quadrático; compara com a queda livre e mostra a velocidade terminal. |

Em todas as simulações, mover um slider recalcula os gráficos automaticamente, e os botões **Animar** e **Reiniciar** controlam a animação do cenário.

## 1. Equações utilizadas

### 1.1 Plano inclinado com atrito e tração — derivação de $a$

**Diagrama de corpo livre.** Sobre $m_1$ atuam o peso $m_1g$, a normal $N$, a tração $T$ (para cima do plano, em direção à polia) e o atrito $f$ (oposto à tendência de movimento). Sobre $m_2$ atuam o peso $m_2g$ (para baixo) e a tração $T$ (para cima). Adotamos como positivo $m_1$ subindo o plano e $m_2$ descendo; como o fio é inextensível, os dois blocos têm a mesma aceleração $a$.

Na direção perpendicular ao plano não há movimento; ao longo do plano ($m_1$) e na vertical ($m_2$) aplicamos a **2ª Lei de Newton**:

$$
N - m_1g\cos\theta = 0
\quad\Rightarrow\quad
N = m_1g\cos\theta
$$

$$
T - m_1g\sin\theta - f = m_1a
$$

$$
m_2g - T = m_2a
$$

Somando as duas últimas equações, a tração se cancela e aparece a força motriz:

$$
F_{\text{motriz}} - f = (m_1+m_2)a,
\qquad
F_{\text{motriz}}=m_2g-m_1g\sin\theta
$$

O atrito estático se ajusta até o limite $\mu_sN$. Por isso, se $|F_{\text{motriz}}|\leq\mu_sN$, o sistema fica em **equilíbrio estático** e $a=0$. Caso contrário, o atrito é cinético, $f=\mu_kN\operatorname{sinal}(F_{\text{motriz}})$, sempre contra o movimento, e o sistema está em movimento com:

$$
a=\frac{F_{\text{motriz}}-\mu_kN\operatorname{sinal}(F_{\text{motriz}})}{m_1+m_2}
\qquad
T=m_2(g-a)
$$

Como $a$ é constante, a cinemática é a do **MRUV**, avaliada diretamente sobre `t = np.linspace(0, 5, 300)` na função `calcular_plano_inclinado`. O valor de $a$ positivo significa $m_2$ descendo; negativo, $m_1$ escorregando plano abaixo.

$$
x(t)=x_0+v_0t+\frac12 at^2
\qquad
v(t)=v_0+at
$$

### 1.2 Força centrípeta (MCU)

No movimento circular uniforme a força resultante aponta para o centro e, pela 2ª Lei na direção radial, vale $mv^2/R$. A posição vem das equações paramétricas do círculo:

$$
\omega=\frac{v}{R}
\qquad
x(t)=R\cos(\omega t)
\qquad
y(t)=R\sin(\omega t)
$$

$$
F_c=\frac{mv^2}{R}=m\omega^2R
\qquad
T_{\text{volta}}=\frac{2\pi}{\omega}
$$

O código acrescenta uma fase inicial ao ângulo ($\omega t+\varphi_0$) apenas para que, ao mudar um slider durante a animação, a massa continue da posição em que estava, sem saltos.

### 1.3 Força de arrasto

Com o eixo positivo para baixo, a 2ª Lei fica $m\,dv/dt=mg-F_{\text{arrasto}}$. As soluções fechadas (com $v(0)=0$ e $y(0)=0$) são:

**Arrasto linear ($F=bv$):**

$$
v_t=\frac{mg}{b}
\qquad
\tau=\frac{m}{b}
$$

$$
v(t)=v_t\left(1-e^{-t/\tau}\right)
\qquad
y(t)=v_tt-v_t\tau\left(1-e^{-t/\tau}\right)
$$

**Arrasto quadrático ($F=cv^2$):**

$$
v_t=\sqrt{\frac{mg}{c}}
$$

$$
v(t)=v_t\tanh\left(\frac{gt}{v_t}\right)
\qquad
y(t)=\frac{v_t^2}{g}\ln\left[\cosh\left(\frac{gt}{v_t}\right)\right]
$$

A referência sem arrasto é a queda livre: $v(t)=gt$ e $y(t)=gt^2/2$. A aceleração instantânea é $a=g-F_{\text{arrasto}}/m$.

Para evitar estouro numérico de `np.cosh` em tempos longos, o código calcula $\ln(\cosh x)$ como `np.logaddexp(x, -x) - np.log(2)`, que é a mesma expressão algebricamente.

## 2. Coeficiente de atrito crítico no plano inclinado

Com $m_1=2,0\ \text{kg}$, $m_2=1,5\ \text{kg}$ e $\theta=30^\circ$ (valores iniciais da simulação), o sistema deixa de se mover entre $\mu=0,28$ e $\mu=0,29$; a teoria prevê $\mu_{\text{crítico}}=0,289$, em concordância com o experimento.

**Procedimento.** Partimos de $\mu=0,20$, em que o sistema está em movimento com $a=0,430\ \text{m/s}^2$ e $T=14,07\ \text{N}$, e aumentamos $\mu$ no slider (com $\mu_s=\mu_k$) observando o estado exibido no topo da tela:

| $\mu$ | Estado exibido | $a$ (m/s²) | $T$ (N) |
|---:|---|---:|---:|
| 0,20 | Em movimento | 0,430 | 14,07 |
| 0,25 | Em movimento | 0,188 | 14,43 |
| 0,27 | Em movimento | 0,091 | 14,58 |
| 0,28 | Em movimento | 0,042 | 14,65 |
| 0,29 | Equilíbrio estático | 0 | 14,72 |
| 0,30 | Equilíbrio estático | 0 | 14,72 |

**Previsão teórica.** A transição ocorre quando $|F_{\text{motriz}}|=\mu_sN$:

$$
N=2,0\cdot 9,81\cos 30^\circ=16,99\ \text{N}
$$

$$
F_{\text{motriz}}=1,5\cdot9,81-2,0\cdot9,81\sin30^\circ=4,905\ \text{N}
$$

$$
\mu_{\text{crit}}=\frac{|F_{\text{motriz}}|}{N}
=\frac{|m_2-m_1\sin\theta|}{m_1\cos\theta}
=\frac{4,905}{16,99}\approx 0,289
$$

**Comparação.** O intervalo encontrado no slider (entre 0,28 e 0,29) contém o valor teórico de 0,2887, com diferença menor que a resolução de 0,01 usada na varredura. A aceleração cai linearmente com $\mu$ (cerca de 0,049 m/s² a cada 0,01), chegando a zero exatamente no $\mu$ crítico, e no equilíbrio a tração se iguala ao peso de $m_2$ (14,72 N). O $\mu$ crítico não depende de $g$: ele é uma razão entre forças, e $g$ se cancela.

## 3. Arrasto linear vs. quadrático: tempo para 95% de $v_{\text{terminal}}$

Com $m=2,0\ \text{kg}$ e coeficiente 0,5 ($b=0,5\ \text{kg/s}$ no linear, $c=0,5\ \text{kg/m}$ no quadrático) e $g=9,81\ \text{m/s}^2$, a queda quadrática atinge **95% da velocidade terminal em 1,17 s**, contra **11,98 s na linear**. Os tempos vêm da inversão de $v(t)=0,95v_t$ e são os mesmos que a simulação exibe no topo da tela e marca com um ponto vermelho no gráfico $v(t)$:

| Modelo | $v_{\text{terminal}}$ (m/s) | Escala de tempo (s) | $t$ para 95% (s) | $v$ em $t=20$ s |
|---|---:|---|---:|---|
| Linear ($b=0,5$ kg/s) | 39,24 | $\tau=m/b=4,00$ | 11,98 | 38,98 m/s (99,3% de $v_t$) |
| Quadrático ($c=0,5$ kg/m) | 6,26 | $v_t/g=0,64$ | 1,17 | 6,26 m/s (100% de $v_t$) |

Em ambos os casos a curva $v(t)$ satura exatamente no valor de $v_{\text{terminal}}$ calculado pela fórmula (linha verde pontilhada no gráfico), o que indica que a implementação está correta. Já a queda livre, $v=gt$, continua crescendo, e a diferença em relação à curva com arrasto aumenta com o tempo.

Como $b$ e $c$ têm unidades diferentes, “mesmo coeficiente” não significa “mesma resistência”: aqui a velocidade terminal quadrática é seis vezes menor, o que explica boa parte da diferença. Uma comparação mais justa é com a mesma $v_t=39,24\ \text{m/s}$, o que exige $c\approx0,0127\ \text{kg/m}$ (abaixo do mínimo do slider, por isso calculado à parte). Nesse caso o quadrático leva 7,33 s, ainda menos que os 11,98 s do linear: com a mesma $v_t$, a razão entre os tempos é sempre $\ln 20/\operatorname{arctanh}(0,95)\approx1,64$.

**Por que as curvas têm formas diferentes.** No modelo linear a aceleração é proporcional ao que falta para atingir a velocidade terminal, $a=(g/v_t)(v_t-v)$; uma taxa de variação proporcional à própria diferença é exatamente o que produz uma exponencial, então a aceleração começa a cair desde o primeiro instante e a curva se dobra de forma suave e uniforme. No modelo quadrático, $a=g(1-v^2/v_t^2)$: como $v^2$ é muito pequeno no início, o arrasto quase não atua e o objeto cai praticamente em queda livre (a curva acompanha a reta $gt$); só perto de $v_t$ o freio aparece com força, gerando o formato da tangente hiperbólica, que se dobra de forma mais abrupta. Na fase final, a diferença entre $v$ e $v_t$ decai com taxa $2g/v_t$ no quadrático contra $g/v_t$ no linear, por isso o quadrático chega aos 95% mais cedo para a mesma $v_t$.

## 4. Aplicações reais

O plano inclinado com polia descreve situações como elevadores de carga em rampas, teleféricos de obra e guinchos que puxam um carro para cima de um caminhão-cegonha: o $\mu$ crítico indica se a carga fica parada sozinha ou precisa de freio, e a tração calculada ajuda a dimensionar o cabo.

A força centrípeta aparece em carros fazendo curvas (onde o atrito entre pneu e pista fornece a força para o centro), centrífugas de laboratório, máquinas de lavar na centrifugação e satélites em órbita, onde a gravidade faz esse papel; com os valores iniciais da simulação ($m=2$ kg, $R=2,5$ m, $v=3$ m/s) obtemos $\omega=1,2$ rad/s, uma volta a cada 5,24 s e $F_c=7,2$ N.

A força de arrasto é essencial no projeto de paraquedas e na queda de paraquedistas (arrasto quadrático, já que o ar em alta velocidade se comporta assim), em gotas de chuva e no movimento de partículas pequenas em líquidos viscosos, como sedimentos na água ou esferas em óleo, onde o regime lento torna o arrasto linear o modelo mais adequado.

## Conclusão

As simulações reproduzem as previsões teóricas: o $\mu$ crítico medido no slider coincide com $|F_{\text{motriz}}|/N\approx0,289$, e as curvas de velocidade com arrasto saturam exatamente na $v_{\text{terminal}}$ calculada pela fórmula. Todos os resultados vêm da 2ª Lei de Newton aplicada a cada diagrama de corpo livre, seguida de fórmulas fechadas avaliadas com NumPy, **sem integração numérica**.
