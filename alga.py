import math
import numpy as np

# =============================================================
# Geometria da alga marinha (importavel por cena.py)
# =============================================================

def _quad_faixa(p0, p1, w):
    """Gera 2 triangulos formando uma faixa de largura 2w entre p0 e p1."""
    dx = p1[0] - p0[0];  dy = p1[1] - p0[1]
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1e-9:
        return []
    nx = -dy / length;  ny = dx / length
    a = (p0[0]+nx*w, p0[1]+ny*w, 0.0)
    b = (p0[0]-nx*w, p0[1]-ny*w, 0.0)
    c = (p1[0]+nx*w, p1[1]+ny*w, 0.0)
    d = (p1[0]-nx*w, p1[1]-ny*w, 0.0)
    return [a, b, c,   b, d, c]

def _gerar_elipse(cx, cy, ax, ay, angulo_rot, n, z=0.0):
    """Elipse centrada em (cx,cy), semi-eixos ax/ay, rotacionada em z."""
    center = (cx, cy, z)
    pts = []
    for i in range(n + 1):
        theta = 2 * math.pi * i / n
        lx = ax * math.cos(theta)
        ly = ay * math.sin(theta)
        rx = lx * math.cos(angulo_rot) - ly * math.sin(angulo_rot)
        ry = lx * math.sin(angulo_rot) + ly * math.cos(angulo_rot)
        pts.append((cx + rx, cy + ry, z))
    verts = []
    for i in range(n):
        verts += [center, pts[i], pts[i+1]]
    return verts

def build_alga(vl):
    """
    Adiciona os vertices de uma alga em vl e retorna o dict de partes.
    Base em y=0, topo em y~0.88. Centrada em x=0, no plano z=0.
    """
    partes = {}
    CAULE_W = 0.025
    SEG = 7

    # Pontos centrais do caule em zig-zag
    caule_pts = []
    for i in range(SEG + 1):
        t = i / SEG
        y = t * 0.88
        amp = 0.04 * (1.0 - 0.3 * t)
        x = amp * math.sin(math.pi * i)
        caule_pts.append((x, y))

    # Caule: faixa em zig-zag
    s = len(vl)
    for i in range(SEG):
        vl += _quad_faixa(caule_pts[i], caule_pts[i+1], CAULE_W)
    partes['caule'] = (s, len(vl)-s, (0.10, 0.55, 0.10, 1.0))

    # Folhas: 4 elipses inclinadas ao longo do caule
    folha_cfg = [(1, +1), (2, -1), (4, +1), (5, -1)]
    for idx, (seg_i, lado) in enumerate(folha_cfg):
        px, py = caule_pts[seg_i]
        ang = lado * math.radians(35)
        cx = px + lado * 0.06
        cy = py + 0.03
        s = len(vl)
        vl += _gerar_elipse(cx, cy, 0.11, 0.035, ang, 14)
        partes[f'folha_{idx}'] = (s, len(vl)-s, (0.15, 0.70, 0.15, 1.0))

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
    window = glfw.create_window(800, 600, "Alga Marinha - Fundo do Mar", None, None)
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

    vertices_list = []
    partes = build_alga(vertices_list)

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

    # A alga e decoracao estatica — sem controles de transformacao
    POS_X, POS_Y = -0.75, -0.90
    wireframe = False

    def key_event(window, key, scancode, action, mods):
        global wireframe
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

        mat = mat_translacao(POS_X, POS_Y, 0.0)
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)
        for nome, (start, count, cor) in partes.items():
            glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
            glDrawArrays(GL_TRIANGLES, start, count)

        glfw.swap_buffers(window)

    glfw.terminate()
