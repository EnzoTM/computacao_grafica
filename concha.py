import math
import numpy as np

# =============================================================
# Geometria da concha com perola (importavel por cena.py)
# =============================================================

def build_concha(vl):
    """
    Adiciona os vertices da concha em vl.
    Retorna (partes_base, partes_tampa, RZ).
      - partes_base : base + perola (matriz fixa de cena)
      - partes_tampa: tampa rotacionavel (matriz com angulo da dobradura)
      - RZ          : profundidade da concha (posicao do hinge)
    """
    partes_base  = {}
    partes_tampa = {}

    RX, RY, RZ = 0.22, 0.13, 0.22
    N_SET = 20;  N_PIL = 10;  MEIO = N_PIL // 2

    def F_concha(u, v):
        return (RX*math.sin(v)*math.cos(u),
                RY*math.cos(v),
                RZ*math.sin(v)*math.sin(u))

    def meia_concha(p_ini, p_fim):
        PI = math.pi
        ss = (2*PI)/N_SET;  sp = PI/N_PIL
        verts = []
        for i in range(N_SET):
            for j in range(p_ini, p_fim):
                u  = i*ss;  un = (2*PI) if i+1==N_SET else (i+1)*ss
                v  = j*sp;  vn = PI     if j+1==N_PIL  else (j+1)*sp
                p0,p1,p2,p3 = F_concha(u,v),F_concha(u,vn),F_concha(un,v),F_concha(un,vn)
                verts += [p0,p2,p1, p3,p1,p2]
        return verts

    # Base (tigela): pilhas MEIO..N, y de 0 a -RY
    s = len(vl)
    vl += meia_concha(MEIO, N_PIL)
    partes_base['base'] = (s, len(vl)-s, (0.95, 0.75, 0.65, 1.0))

    # Perola: esfera pequena no centro da base
    R_P = 0.055;  N_SP = 12;  N_PP = 8;  MEIO_P = N_PP // 2
    OY  = -RY * 0.35

    def F_perola(u, v):
        return (R_P*math.sin(v)*math.cos(u),
                R_P*math.cos(v) + OY,
                R_P*math.sin(v)*math.sin(u))

    def meia_perola(p_ini, p_fim):
        PI = math.pi
        ss = (2*PI)/N_SP;  sp = PI/N_PP
        verts = []
        for i in range(N_SP):
            for j in range(p_ini, p_fim):
                u  = i*ss;  un = (2*PI) if i+1==N_SP else (i+1)*ss
                v  = j*sp;  vn = PI     if j+1==N_PP  else (j+1)*sp
                p0,p1,p2,p3 = F_perola(u,v),F_perola(u,vn),F_perola(un,v),F_perola(un,vn)
                verts += [p0,p2,p1, p3,p1,p2]
        return verts

    s = len(vl);  vl += meia_perola(0, MEIO_P)
    partes_base['perola_top'] = (s, len(vl)-s, (0.97, 0.97, 1.00, 1.0))
    s = len(vl);  vl += meia_perola(MEIO_P, N_PP)
    partes_base['perola_bot'] = (s, len(vl)-s, (0.88, 0.88, 0.95, 1.0))

    # Tampa (domo): pilhas 0..MEIO, y de +RY a 0
    s = len(vl)
    vl += meia_concha(0, MEIO)
    partes_tampa['tampa'] = (s, len(vl)-s, (0.92, 0.70, 0.60, 1.0))

    return partes_base, partes_tampa, RZ


# =============================================================
# Execucao standalone (visualizacao individual)
# =============================================================
if __name__ == '__main__':
    import glfw
    from OpenGL.GL import *
    import ctypes

    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(800, 600, "Concha com Perola - Fundo do Mar", None, None)
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

    def mat_rotacao_x(ang):
        c, s = math.cos(ang), math.sin(ang)
        return np.array([1,0,0,0, 0,c,-s,0, 0,s,c,0, 0,0,0,1], np.float32)

    vertices_list = []
    partes_base, partes_tampa, HINGE_Z = build_concha(vertices_list)

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

    POS_X, POS_Y, POS_Z = 0.1, -0.50, 0.0
    TILT = math.radians(-50)
    angle_lid = 0.0
    wireframe  = False

    def key_event(window, key, scancode, action, mods):
        global angle_lid, wireframe
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_A: angle_lid = min(angle_lid + 0.05, math.pi/2)
            if key == glfw.KEY_S: angle_lid = max(angle_lid - 0.05, 0.0)
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

        mat_base = multiplica_matriz(mat_translacao(POS_X, POS_Y, POS_Z), mat_rotacao_x(TILT))
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat_base)
        for nome, (start, count, cor) in partes_base.items():
            glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
            glDrawArrays(GL_TRIANGLES, start, count)

        mat_lid = multiplica_matriz(
            mat_translacao(POS_X, POS_Y, POS_Z),
            multiplica_matriz(
                mat_rotacao_x(TILT),
                multiplica_matriz(
                    mat_translacao(0.0, 0.0, HINGE_Z),
                    multiplica_matriz(mat_rotacao_x(angle_lid), mat_translacao(0.0, 0.0, -HINGE_Z))
                )
            )
        )
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat_lid)
        for nome, (start, count, cor) in partes_tampa.items():
            glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
            glDrawArrays(GL_TRIANGLES, start, count)

        glfw.swap_buffers(window)

    glfw.terminate()
