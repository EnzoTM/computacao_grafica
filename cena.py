""""
Turma 2
Enzo Tonon Morente - 14568476
Cauê Paiva Lira - 14675416
"""

import glfw
from OpenGL.GL import *
import numpy as np
import math
import ctypes
import random

from tubarao import build_tubarao
from concha  import build_concha
from estrela import build_estrela
from alga    import build_alga
from bolha   import build_bolha

# =============================================================
# Controles
# =============================================================
# Setas  ←→↑↓  : move o tubarao
# Z / X         : aumenta / diminui as bolhas de agua
# A / S         : abre / fecha a tampa da concha
# Q / E         : gira a estrela-do-mar esquerda / direita
# P             : alterna wireframe (malha poligonal) - global

print("=" * 50)
print("Fundo do Mar — SCC0250 Projeto 1")
print("=" * 50)
print("Setas ←→↑↓ : move o tubarao")
print("Z / X       : aumenta / diminui as bolhas de agua")
print("R / T       : gira tubarao no eixo Y")
print("F / G       : gira tubarao no eixo X")
print("A / S       : abre / fecha concha")
print("Q / E       : gira estrela-do-mar")
print("P           : toggle wireframe")
print("=" * 50)

# =============================================================
# Janela e contexto OpenGL
# =============================================================
glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
window = glfw.create_window(900, 700, "Fundo do Mar - SCC0250", None, None)
glfw.make_context_current(window)

# =============================================================
# Shaders
# =============================================================
vertex_code = """
    attribute vec3 position;
    uniform mat4 mat_transformation;
    void main(){
        gl_Position = mat_transformation * vec4(position, 1.0);
    }
"""

fragment_code = """
    uniform vec4 color;
    void main(){
        gl_FragColor = color;
    }
"""

program  = glCreateProgram()
vertex   = glCreateShader(GL_VERTEX_SHADER)
fragment = glCreateShader(GL_FRAGMENT_SHADER)

glShaderSource(vertex, vertex_code)
glShaderSource(fragment, fragment_code)

glCompileShader(vertex)
if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
    print(glGetShaderInfoLog(vertex).decode())
    raise RuntimeError("Erro no Vertex Shader")

glCompileShader(fragment)
if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
    print(glGetShaderInfoLog(fragment).decode())
    raise RuntimeError("Erro no Fragment Shader")

glAttachShader(program, vertex)
glAttachShader(program, fragment)
glLinkProgram(program)
if not glGetProgramiv(program, GL_LINK_STATUS):
    print(glGetProgramInfoLog(program))
    raise RuntimeError("Erro no link do programa")
glUseProgram(program)

# =============================================================
# Algebra e matrizes
# =============================================================

def normalizar(v):
    n = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if n < 1e-8:
        return (1.0, 0.0, 0.0)
    return (v[0]/n, v[1]/n, v[2]/n)

def produto_vetorial(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def multiplica_matriz(a, b):
    m_a = a.reshape(4, 4)
    m_b = b.reshape(4, 4)
    return np.dot(m_a, m_b).reshape(1, 16)

def mat_translacao(tx, ty, tz):
    return np.array([
        1.0, 0.0, 0.0, tx,
        0.0, 1.0, 0.0, ty,
        0.0, 0.0, 1.0, tz,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

def mat_escala(sx, sy, sz):
    return np.array([
        sx,  0.0, 0.0, 0.0,
        0.0, sy,  0.0, 0.0,
        0.0, 0.0, sz,  0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

def mat_rotacao_x(ang):
    c, s = math.cos(ang), math.sin(ang)
    return np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0,  c,  -s,  0.0,
        0.0,  s,   c,  0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

def mat_rotacao_y(ang):
    c, s = math.cos(ang), math.sin(ang)
    return np.array([
         c,  0.0,  s,  0.0,
        0.0, 1.0, 0.0, 0.0,
        -s,  0.0,  c,  0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

def mat_rotacao_z(ang):
    c, s = math.cos(ang), math.sin(ang)
    return np.array([
         c,  -s,  0.0, 0.0,
         s,   c,  0.0, 0.0,
        0.0, 0.0,  1.0, 0.0,
        0.0, 0.0,  0.0, 1.0
    ], np.float32)

# =============================================================
# Construcao da geometria — VBO unico
# =============================================================
vertices_list = []

# -------------------------------------------------------
# OBJETO 1: AGUA-VIVA (3D)
# -------------------------------------------------------
# Geometria centrada na origem: domo em cima (y>0), tentaculos abaixo (y<0).
# Eixo y-up: a agua-viva "olha" para cima.
def build_agua_viva(vl):
    partes = {}
    RX, RY, RZ = 0.13, 0.10, 0.13
    N_SET_A = 16;  N_PIL_A = 8;  MEIO_A = N_PIL_A // 2  # MEIO = 4 -> v = pi/2

    PI = math.pi
    ss = (2*PI)/N_SET_A;  sp = PI/N_PIL_A

    def F_bell(u, v):
        return (RX*math.sin(v)*math.cos(u),
                RY*math.cos(v),
                RZ*math.sin(v)*math.sin(u))

    # Domo principal (v: 0 -> pi/2, y: RY -> 0) — roxo claro
    verts_domo = []
    for i in range(N_SET_A):
        for j in range(0, MEIO_A):
            u  = i*ss;  un = (2*PI) if i+1==N_SET_A else (i+1)*ss
            v  = j*sp;  vn = (j+1)*sp
            p0,p1,p2,p3 = F_bell(u,v),F_bell(u,vn),F_bell(un,v),F_bell(un,vn)
            verts_domo += [p0,p2,p1, p3,p1,p2]
    s = len(vl);  vl += verts_domo
    partes['domo'] = (s, len(vl)-s, (0.88, 0.60, 0.95, 1.0))

    # Anel/saia: uma faixa extra abaixo do domo — roxa mais escura
    verts_anel = []
    for i in range(N_SET_A):
        u  = i*ss;  un = (2*PI) if i+1==N_SET_A else (i+1)*ss
        v  = MEIO_A*sp;  vn = (MEIO_A+1)*sp
        p0,p1,p2,p3 = F_bell(u,v),F_bell(u,vn),F_bell(un,v),F_bell(un,vn)
        verts_anel += [p0,p2,p1, p3,p1,p2]
    s = len(vl);  vl += verts_anel
    partes['anel'] = (s, len(vl)-s, (0.70, 0.40, 0.85, 1.0))

    # Tentaculos: 8 fitas finas penduradas na borda do domo
    N_TENT   = 8
    TENT_LEN = 0.30
    TENT_W   = 0.010
    verts_tent = []
    for i in range(N_TENT):
        u  = 2*PI*i/N_TENT
        bx = RX*math.cos(u);  bz = RZ*math.sin(u)
        # vetor perpendicular no plano xz para dar largura ao tentaculo
        nx = -math.sin(u);  nz = math.cos(u)
        tl = (bx+nx*TENT_W,  0.0,       bz+nz*TENT_W)
        tr = (bx-nx*TENT_W,  0.0,       bz-nz*TENT_W)
        bl = (bx+nx*TENT_W, -TENT_LEN,  bz+nz*TENT_W)
        br = (bx-nx*TENT_W, -TENT_LEN,  bz-nz*TENT_W)
        verts_tent += [tl, tr, bl,  tr, br, bl]
    s = len(vl);  vl += verts_tent
    partes['tentaculos'] = (s, len(vl)-s, (0.65, 0.30, 0.75, 1.0))

    return partes

partes_aviva = build_agua_viva(vertices_list)

partes_concha_base, partes_concha_tampa, CONCHA_HINGE_Z = build_concha(vertices_list)

partes_tubarao = build_tubarao(vertices_list)

partes_alga = build_alga(vertices_list)

partes_estrela = build_estrela(vertices_list)

bolha_geo_start, bolha_geo_count, reflexo_geo_start, reflexo_geo_count = build_bolha(vertices_list)

# =============================================================
# Upload para a GPU (unico VBO com todos os vertices)
# =============================================================
total = len(vertices_list)
vertices = np.zeros(total, [("position", np.float32, 3)])
vertices['position'] = np.array(vertices_list)

buffer_VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)

stride = vertices.strides[0]
offset = ctypes.c_void_p(0)
loc_pos = glGetAttribLocation(program, "position")
glEnableVertexAttribArray(loc_pos)
glVertexAttribPointer(loc_pos, 3, GL_FLOAT, False, stride, offset)

loc_color = glGetUniformLocation(program, "color")
loc_trans = glGetUniformLocation(program, "mat_transformation")

# =============================================================
# Posicoes fixas de cena
# =============================================================
# Aguas-vivas: 3 instancias oscilando verticalmente em lanes diferentes
# Cada entrada: bx (x fixo), by (y central), amp (amplitude), freq, phase
AVIVAS = [
    {'bx': -0.55, 'by':  0.15, 'amp': 0.32, 'freq': 0.8, 'phase': 0.0, 'rot': 0.0, 'rot_speed': 0.018},
    {'bx':  0.02, 'by':  0.05, 'amp': 0.38, 'freq': 0.55,'phase': 2.1, 'rot': 2.1, 'rot_speed': 0.013},
    {'bx':  0.58, 'by':  0.20, 'amp': 0.28, 'freq': 1.0, 'phase': 4.2, 'rot': 4.2, 'rot_speed': 0.022},
]
aviva_t = 0.0   # contador de tempo para oscilacao e pulso
# Concha: gap entre as algas, encostada no chao
# O ponto mais baixo da concha inclinada (TILT=-50) fica ~0.19 abaixo de POS_Y.
# POS_Y = -0.80 -> borda inferior ~ -0.99, rente ao limite da tela.
CONCHA_POS = ( 0.52, -0.80, 0.0)
CONCHA_TILT = math.radians(-50)
# Algas: varias instancias decorativas na base da tela
# Cada entrada: (x_pos, escala, angulo_inclinacao)
ALGA_BASE_Y = -0.98
ALGAS = [
    (-0.88, 0.30, math.radians(-8)),
    (-0.65, 0.38, math.radians( 5)),
    (-0.42, 0.33, math.radians(-4)),
    (-0.18, 0.36, math.radians( 7)),
    ( 0.08, 0.28, math.radians(-6)),
    ( 0.22, 0.40, math.radians( 3)),
    ( 0.82, 0.34, math.radians(-5)),
    ( 0.92, 0.32, math.radians( 6)),
]
# Estrela: canto inferior direito
ESTRELA_POS = (0.65,  0.60, 0.0)

# =============================================================
# Estado de cada objeto
# =============================================================
# Concha
concha_lid     = 0.0

# Tubarao (jogador)
tubarao_x        = 0.0
tubarao_y        = 0.0
tubarao_x_inc    = 0.0
tubarao_y_inc    = 0.0
tubarao_rot_y    = 0.0
tubarao_rot_x    = 0.0
TUBARAO_STEP     = 0.015
TUBARAO_ROT_STEP = math.radians(3)
TUBARAO_LIMITE   = 0.72   # margem para o raio do balao (0.25)

# Bolhas
bolha_escala   = 1.0
BOLHA_ESC_MIN  = 0.3
BOLHA_ESC_MAX  = 3.0

# Estrela
estrela_ang    = 0.0
ESTRELA_STEP   = math.radians(3)

# Bolhas: lista de dicts {x, y, speed, r}
# y inicial espalhado por toda a tela para que nao surjam todas de uma vez
random.seed(7)
N_BOLHAS = 12
bolhas = [
    {
        'x':     random.uniform(-0.90, 0.90),
        'y':     random.uniform(-1.10, 1.05),   # espalhadas verticalmente
        'speed': random.uniform(0.004, 0.010),
        'r':     random.uniform(0.018, 0.038),
    }
    for _ in range(N_BOLHAS)
]

# Global
wireframe      = False

# =============================================================
# Callback do teclado (todos os objetos)
# =============================================================
def key_event(window, key, scancode, action, mods):
    global concha_lid
    global tubarao_x_inc, tubarao_y_inc, tubarao_rot_y, tubarao_rot_x
    global bolha_escala
    global estrela_ang
    global wireframe

    press_repeat = (action == glfw.PRESS or action == glfw.REPEAT)

    if press_repeat:
        # --- Tubarao: movimento ---
        if key == glfw.KEY_RIGHT: tubarao_x_inc = +TUBARAO_STEP
        if key == glfw.KEY_LEFT:  tubarao_x_inc = -TUBARAO_STEP
        if key == glfw.KEY_UP:    tubarao_y_inc = +TUBARAO_STEP
        if key == glfw.KEY_DOWN:  tubarao_y_inc = -TUBARAO_STEP

        # --- Bolhas: escala global ---
        if key == glfw.KEY_Z:
            bolha_escala = min(bolha_escala + 0.05, BOLHA_ESC_MAX)
        if key == glfw.KEY_X:
            bolha_escala = max(bolha_escala - 0.05, BOLHA_ESC_MIN)

        # --- Tubarao: rotacao Y e X ---
        if key == glfw.KEY_R: tubarao_rot_y += TUBARAO_ROT_STEP
        if key == glfw.KEY_T: tubarao_rot_y -= TUBARAO_ROT_STEP
        if key == glfw.KEY_F: tubarao_rot_x += TUBARAO_ROT_STEP
        if key == glfw.KEY_G: tubarao_rot_x -= TUBARAO_ROT_STEP

        # --- Concha ---
        if key == glfw.KEY_A:
            concha_lid = min(concha_lid + 0.05, math.pi/2)
        if key == glfw.KEY_S:
            concha_lid = max(concha_lid - 0.05, 0.0)

        # --- Estrela ---
        if key == glfw.KEY_Q:
            estrela_ang += ESTRELA_STEP
        if key == glfw.KEY_E:
            estrela_ang -= ESTRELA_STEP

    # Tubarao para ao soltar a tecla
    if action == glfw.RELEASE:
        if key in (glfw.KEY_RIGHT, glfw.KEY_LEFT): tubarao_x_inc = 0.0
        if key in (glfw.KEY_UP,    glfw.KEY_DOWN): tubarao_y_inc = 0.0

    # Wireframe global
    if key == glfw.KEY_P and action == glfw.PRESS:
        wireframe = not wireframe

glfw.set_key_callback(window, key_event)

# =============================================================
# Loop principal de renderizacao
# =============================================================
glfw.show_window(window)
glEnable(GL_DEPTH_TEST)

def desenha(partes_dict, mat):
    """Aplica a matriz e desenha todas as partes de um dicionario."""
    glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)
    for nome, (start, count, cor) in partes_dict.items():
        glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
        glDrawArrays(GL_TRIANGLES, start, count)

while not glfw.window_should_close(window):
    glfw.poll_events()

    # Atualiza tubarao e tempo das aguas-vivas
    tubarao_x  = max(-TUBARAO_LIMITE, min(TUBARAO_LIMITE, tubarao_x + tubarao_x_inc))
    tubarao_y  = max(-TUBARAO_LIMITE, min(TUBARAO_LIMITE, tubarao_y + tubarao_y_inc))
    aviva_t += 0.022

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.0, 0.15, 0.35, 1.0)   # azul-escuro do fundo do mar

    if wireframe:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # ---- 1. Aguas-vivas: oscilam verticalmente, pulsam e rotacionam em Y ----
    for av in AVIVAS:
        av['rot'] += av['rot_speed']
        ay    = av['by'] + av['amp'] * math.sin(aviva_t * av['freq'] + av['phase'])
        pulso = 0.88 + 0.12 * math.sin(aviva_t * av['freq'] * 2 + av['phase'])
        mat_av = multiplica_matriz(
            mat_translacao(av['bx'], ay, 0.0),
            multiplica_matriz(
                mat_rotacao_y(av['rot']),
                mat_escala(1.0, pulso, 1.0)
            )
        )
        desenha(partes_aviva, mat_av)

    # ---- 2. Concha base + perola: T x Rx(tilt) ----
    mat_concha_base = multiplica_matriz(
        mat_translacao(*CONCHA_POS),
        mat_rotacao_x(CONCHA_TILT)
    )
    desenha(partes_concha_base, mat_concha_base)

    # ---- 3. Concha tampa: T x Rx(tilt) x T(hinge) x Rx(lid) x T(-hinge) ----
    mat_concha_lid = multiplica_matriz(
        mat_translacao(*CONCHA_POS),
        multiplica_matriz(
            mat_rotacao_x(CONCHA_TILT),
            multiplica_matriz(
                mat_translacao(0.0, 0.0, CONCHA_HINGE_Z),
                multiplica_matriz(
                    mat_rotacao_x(concha_lid),
                    mat_translacao(0.0, 0.0, -CONCHA_HINGE_Z)
                )
            )
        )
    )
    desenha(partes_concha_tampa, mat_concha_lid)

    # ---- 4. Tubarão: T x Ry x Rx ----
    mat_tubarao = multiplica_matriz(
        mat_translacao(tubarao_x, tubarao_y, 0.0),
        multiplica_matriz(
            mat_rotacao_y(tubarao_rot_y),
            mat_rotacao_x(tubarao_rot_x)
        )
    )
    desenha(partes_tubarao, mat_tubarao)

    # ---- 5. Algas decorativas: T(x, base_y) x Rz(ang) x S ----
    for (ax, aesc, aang) in ALGAS:
        mat_alga = multiplica_matriz(
            mat_translacao(ax, ALGA_BASE_Y, 0.0),
            multiplica_matriz(
                mat_rotacao_z(aang),
                mat_escala(aesc, aesc, 1.0)
            )
        )
        desenha(partes_alga, mat_alga)

    # ---- 6. Estrela: T(pos) x Rz(ang) ----
    mat_estrela = multiplica_matriz(
        mat_translacao(*ESTRELA_POS),
        mat_rotacao_z(estrela_ang)
    )
    desenha(partes_estrela, mat_estrela)

    # ---- 7. Bolhas: esfera + disco de reflexo, reusados com T x S por bolha ----
    for b in bolhas:
        b['y'] += b['speed']
        if b['y'] > 1.12:
            b['y'] = -1.12
            b['x'] = random.uniform(-0.90, 0.90)
        r = b['r'] * bolha_escala
        mat_bolha = multiplica_matriz(
            mat_translacao(b['x'], b['y'], 0.0),
            mat_escala(r, r, r)
        )
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat_bolha)
        glUniform4f(loc_color, 0.72, 0.90, 1.0, 1.0)
        glDrawArrays(GL_TRIANGLES, bolha_geo_start, bolha_geo_count)
        glUniform4f(loc_color, 1.0, 1.0, 1.0, 1.0)     # meia-elipse de reflexo
        glDrawArrays(GL_TRIANGLES, reflexo_geo_start, reflexo_geo_count)

    glfw.swap_buffers(window)

glfw.terminate()
