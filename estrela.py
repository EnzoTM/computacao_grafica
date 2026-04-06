import math
import numpy as np

# =============================================================
# Geometria da estrela-do-mar (importavel por cena.py)
# =============================================================

def _gerar_elipse(cx, cy, cz, ax, ay, angulo_rot, n):
    """Elipse centrada em (cx,cy,cz), semi-eixos ax/ay, rotacionada em z."""
    center = (cx, cy, cz)
    pts = []
    for i in range(n + 1):
        theta = 2 * math.pi * i / n
        lx = ax * math.cos(theta)
        ly = ay * math.sin(theta)
        rx = lx * math.cos(angulo_rot) - ly * math.sin(angulo_rot)
        ry = lx * math.sin(angulo_rot) + ly * math.cos(angulo_rot)
        pts.append((cx + rx, cy + ry, cz))
    verts = []
    for i in range(n):
        verts += [center, pts[i], pts[i+1]]
    return verts

def _gerar_circulo(cx, cy, cz, r, n):
    """Circulo no plano z=cz."""
    center = (cx, cy, cz)
    pts = [(cx + r*math.cos(2*math.pi*i/n), cy + r*math.sin(2*math.pi*i/n), cz)
           for i in range(n + 1)]
    verts = []
    for i in range(n):
        verts += [center, pts[i], pts[i+1]]
    return verts

def build_estrela(vl):
    """
    Adiciona os vertices da estrela-do-mar em vl e retorna o dict de partes.
    Centrada na origem, no plano z=0.
    """
    partes = {}
    PONTAS = 5;  R_EXT = 0.22;  R_INT = 0.09
    N_STAR = PONTAS * 2
    ang_base = math.pi / 2

    # Contorno alternando r_ext (pontas) e r_int (vales)
    contorno = []
    for i in range(N_STAR):
        theta = ang_base + (2 * math.pi * i) / N_STAR
        r = R_EXT if (i % 2 == 0) else R_INT
        contorno.append((r * math.cos(theta), r * math.sin(theta), 0.0))
    contorno.append(contorno[0])

    # Corpo: 10 triangulos do centro ao contorno
    center = (0.0, 0.0, 0.0)
    s = len(vl)
    for i in range(N_STAR):
        vl += [center, contorno[i], contorno[i+1]]
    partes['corpo'] = (s, len(vl)-s, (0.92, 0.30, 0.15, 1.0))

    # Elipses decorativas sobre cada ponta
    for i in range(PONTAS):
        theta = ang_base + (2 * math.pi * (i * 2)) / N_STAR
        dist = R_EXT * 0.62
        cx = dist * math.cos(theta)
        cy = dist * math.sin(theta)
        s = len(vl)
        vl += _gerar_elipse(cx, cy, -0.001, 0.05, 0.025, theta, 10)
        partes[f'det_{i}'] = (s, len(vl)-s, (0.75, 0.20, 0.10, 1.0))

    # Circulo central de destaque
    s = len(vl)
    vl += _gerar_circulo(0.0, 0.0, -0.002, 0.055, 14)
    partes['centro'] = (s, len(vl)-s, (0.98, 0.55, 0.30, 1.0))

    return partes


# =============================================================
# Execucao standalone (visualizacao individual)
# =============================================================
if __name__ == '__main__':
    import glfw
    from OpenGL.GL import *
    import ctypes

    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(800, 600, "Estrela-do-Mar - Fundo do Mar", None, None)
    glfw.make_context_current(window)

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
    glCompileShader(fragment)
    glAttachShader(program, vertex)
    glAttachShader(program, fragment)
    glLinkProgram(program)
    glUseProgram(program)

    def multiplica_matriz(a, b):
        return np.dot(a.reshape(4,4), b.reshape(4,4)).reshape(1,16)

    def mat_translacao(tx, ty, tz):
        return np.array([1,0,0,tx, 0,1,0,ty, 0,0,1,tz, 0,0,0,1], np.float32)

    def mat_rotacao_z(ang):
        c, s = math.cos(ang), math.sin(ang)
        return np.array([c,-s,0,0, s,c,0,0, 0,0,1,0, 0,0,0,1], np.float32)

    vertices_list = []
    partes = build_estrela(vertices_list)

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

    POS_X, POS_Y = 0.65, 0.60
    angle_star = 0.0
    wireframe  = False
    STEP_ANG = math.radians(3)

    def key_event(window, key, scancode, action, mods):
        global angle_star, wireframe
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_Q: angle_star += STEP_ANG
            if key == glfw.KEY_E: angle_star -= STEP_ANG
        if key == glfw.KEY_P and action == glfw.PRESS:
            wireframe = not wireframe

    glfw.set_key_callback(window, key_event)
    glfw.show_window(window)
    glEnable(GL_DEPTH_TEST)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.0, 0.15, 0.35, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

        mat = multiplica_matriz(mat_translacao(POS_X, POS_Y, 0.0), mat_rotacao_z(angle_star))
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)
        for nome, (start, count, cor) in partes.items():
            glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
            glDrawArrays(GL_TRIANGLES, start, count)

        glfw.swap_buffers(window)

    glfw.terminate()
