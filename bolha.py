import math
import numpy as np

# =============================================================
# Geometria da bolha de agua (importavel por cena.py)
# =============================================================

def build_bolha(vl):
    """
    Adiciona os vertices da bolha (template unitario) em vl.
    Retorna (esfera_start, esfera_count, reflexo_start, reflexo_count).
    A bolha e desenhada N vezes com matrizes T x S diferentes — uma por instancia.
    """
    # Esfera unitaria 3D (corpo da bolha)
    def _esfera_unit(n_set=10, n_pil=8):
        PI = math.pi
        ss = (2*PI)/n_set;  sp = PI/n_pil
        def F(u, v):
            return (math.sin(v)*math.cos(u), math.sin(v)*math.sin(u), math.cos(v))
        verts = []
        for i in range(n_set):
            for j in range(n_pil):
                u  = i*ss;  un = (2*PI) if i+1==n_set else (i+1)*ss
                v  = j*sp;  vn = PI     if j+1==n_pil  else (j+1)*sp
                p0,p1,p2,p3 = F(u,v),F(u,vn),F(un,v),F(un,vn)
                verts += [p0,p2,p1, p3,p1,p2]
        return verts

    esfera_start = len(vl)
    vl += _esfera_unit()
    esfera_count = len(vl) - esfera_start

    # Meia-elipse branca no canto superior direito (reflexo de luz)
    # Posicionada em z negativo para aparecer na face frontal da esfera
    def _meia_elipse(cx, cy, cz, ax, ay, n=14):
        center = (cx, cy, cz)
        pts = []
        for i in range(n + 1):
            t = math.pi * i / n   # arco superior
            pts.append((cx + ax * math.cos(t), cy + ay * math.sin(t), cz))
        verts = []
        for i in range(n):
            verts += [center, pts[i], pts[i+1]]
        return verts

    reflexo_start = len(vl)
    vl += _meia_elipse(cx=0.38, cy=0.55, cz=-0.82, ax=0.28, ay=0.13)
    reflexo_count = len(vl) - reflexo_start

    return esfera_start, esfera_count, reflexo_start, reflexo_count


# =============================================================
# Execucao standalone (visualizacao individual)
# =============================================================
if __name__ == '__main__':
    import glfw
    from OpenGL.GL import *
    import ctypes

    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(800, 600, "Bolha de Agua - Fundo do Mar", None, None)
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

    def mat_escala(sx, sy, sz):
        return np.array([sx,0,0,0, 0,sy,0,0, 0,0,sz,0, 0,0,0,1], np.float32)

    vertices_list = []
    esfera_start, esfera_count, reflexo_start, reflexo_count = build_bolha(vertices_list)

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

    # Z: infla, X: desinfla, P: wireframe
    escala    = 0.25
    ESC_MIN   = 0.05
    ESC_MAX   = 0.80
    ESC_STEP  = 0.02
    wireframe = False

    def key_event(window, key, scancode, action, mods):
        global escala, wireframe
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_Z: escala = min(escala + ESC_STEP, ESC_MAX)
            if key == glfw.KEY_X: escala = max(escala - ESC_STEP, ESC_MIN)
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

        mat = multiplica_matriz(mat_translacao(0.0, 0.0, 0.0), mat_escala(escala, escala, escala))
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)

        glUniform4f(loc_color, 0.72, 0.90, 1.0, 1.0)
        glDrawArrays(GL_TRIANGLES, esfera_start, esfera_count)
        glUniform4f(loc_color, 1.0, 1.0, 1.0, 1.0)
        glDrawArrays(GL_TRIANGLES, reflexo_start, reflexo_count)

        glfw.swap_buffers(window)

    glfw.terminate()
