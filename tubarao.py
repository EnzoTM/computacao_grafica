import math
import numpy as np

# =============================================================
# Geometria do tubarao fofo (importavel por cena.py)
# =============================================================

def build_tubarao(vl):
    """
    Adiciona os vertices do tubarao em vl e retorna o dict de partes.
    Orientacao: frente = +x, cima = +y. Centrado na origem.
    """
    partes = {}
    RX, RY, RZ = 0.28, 0.13, 0.16
    N_SET = 16;  N_PIL = 10;  MEIO = N_SET // 2
    PI = math.pi

    # Corpo: elipsoide parametrico com eixo longo em x
    def F_corpo(u, v):
        return (RX*math.cos(v),
                RY*math.sin(v)*math.sin(u),
                RZ*math.sin(v)*math.cos(u))

    def faixa(s_ini, s_fim):
        ss = (2*PI)/N_SET;  sp = PI/N_PIL
        verts = []
        for i in range(s_ini, s_fim):
            for j in range(N_PIL):
                u  = i*ss;  un = (2*PI) if i+1==N_SET else (i+1)*ss
                v  = j*sp;  vn = PI     if j+1==N_PIL  else (j+1)*sp
                p0,p1,p2,p3 = F_corpo(u,v),F_corpo(u,vn),F_corpo(un,v),F_corpo(un,vn)
                verts += [p0,p2,p1, p3,p1,p2]
        return verts

    # Dorso (azul-cinza, u in [0,pi]) e barriga (branco, u in [pi,2pi])
    s = len(vl);  vl += faixa(0, MEIO)
    partes['dorso'] = (s, len(vl)-s, (0.38, 0.50, 0.65, 1.0))
    s = len(vl);  vl += faixa(MEIO, N_SET)
    partes['barriga'] = (s, len(vl)-s, (0.88, 0.92, 0.97, 1.0))

    # Nadadeira dorsal: piramide de base retangular no topo do corpo
    bfl = ( 0.07, RY,  0.04);  bfr = ( 0.07, RY, -0.04)
    bbl = (-0.07, RY,  0.04);  bbr = (-0.07, RY, -0.04)
    apex_d = (0.00, RY + 0.13, 0.0)
    s = len(vl)
    vl += [bfl,bfr,apex_d, bfr,bbr,apex_d, bbr,bbl,apex_d, bbl,bfl,apex_d,
           bfl,bfr,bbr,    bfl,bbr,bbl]
    partes['nad_dorsal'] = (s, len(vl)-s, (0.28, 0.38, 0.55, 1.0))

    # Nadadeiras peitorais: triangulos laterais
    for lado, suf in [(+1,'esq'), (-1,'dir')]:
        rf  = ( 0.06,  0.00, lado*RZ)
        rb  = (-0.06, -0.02, lado*RZ)
        tip = (-0.02, -0.06, lado*(RZ + 0.16))
        s = len(vl);  vl += [rf, rb, tip]
        partes[f'peitoral_{suf}'] = (s, len(vl)-s, (0.28, 0.38, 0.55, 1.0))

    # Nadadeira caudal: dois lobos em V
    raiz  = (-RX,       0.0,    0.0)
    mid_t = (-RX-0.04,  RY*0.4, 0.0)
    mid_b = (-RX-0.04, -RY*0.4, 0.0)
    tip_t = (-RX-0.17,  RY*1.1, 0.0)
    tip_b = (-RX-0.17, -RY*1.1, 0.0)
    s = len(vl)
    vl += [raiz, mid_t, tip_t,
           raiz, tip_b, mid_b]
    partes['cauda'] = (s, len(vl)-s, (0.28, 0.38, 0.55, 1.0))

    # Olhos: esferas 3D
    def esfera_pos(cx, cy, cz, r, ns=9, np_=7):
        ss_ = (2*PI)/ns;  sp_ = PI/np_
        def F(u, v):
            return (cx+r*math.sin(v)*math.cos(u),
                    cy+r*math.sin(v)*math.sin(u),
                    cz+r*math.cos(v))
        verts = []
        for i in range(ns):
            for j in range(np_):
                u  = i*ss_;  un = (2*PI) if i+1==ns  else (i+1)*ss_
                v  = j*sp_;  vn = PI     if j+1==np_ else (j+1)*sp_
                p0,p1,p2,p3 = F(u,v),F(u,vn),F(un,v),F(un,vn)
                verts += [p0,p2,p1, p3,p1,p2]
        return verts

    EX = RX*0.62;  EY = RY*0.35;  EZ = RZ*0.80
    for lado, suf in [(+EZ,'esq'), (-EZ,'dir')]:
        s = len(vl);  vl += esfera_pos(EX, EY, lado, 0.040)
        partes[f'iris_{suf}'] = (s, len(vl)-s, (1.0, 1.0, 1.0, 1.0))
        # Pupila deslocada em +x (direcao da face do tubarao)
        s = len(vl);  vl += esfera_pos(EX+0.032, EY, lado, 0.022, 7, 6)
        partes[f'pupila_{suf}'] = (s, len(vl)-s, (0.05, 0.05, 0.05, 1.0))

    # Boca: sorriso — arco descendente na frente do focinho
    BX = RX+0.01;  BCY = -RY*0.35;  BRZ = 0.055;  BRY = 0.025
    center_b = (BX, BCY, 0.0)
    s = len(vl)
    for i in range(8):
        t0 = PI*i/8;  t1 = PI*(i+1)/8
        p0 = (BX, BCY - BRY*math.sin(t0), BRZ*math.cos(t0))
        p1 = (BX, BCY - BRY*math.sin(t1), BRZ*math.cos(t1))
        vl += [center_b, p0, p1]
    partes['boca'] = (s, len(vl)-s, (0.95, 0.60, 0.65, 1.0))

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
    window = glfw.create_window(800, 600, "Tubarao Fofo - Fundo do Mar", None, None)
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

    def mat_rotacao_y(ang):
        c, s = math.cos(ang), math.sin(ang)
        return np.array([c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1], np.float32)

    vertices_list = []
    partes = build_tubarao(vertices_list)

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

    # Estado: setas movem, R/T giram Y, F/G giram X, P wireframe
    pos_x = 0.0;  pos_y = 0.0
    pos_x_inc = 0.0;  pos_y_inc = 0.0
    rot_y = 0.0;  rot_x = 0.0
    wireframe = False
    MOV_STEP = 0.015;  MOV_LIMIT = 0.72;  ROT_STEP = math.radians(3)

    def key_event(window, key, scancode, action, mods):
        global pos_x_inc, pos_y_inc, rot_y, rot_x, wireframe
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_R: rot_y += ROT_STEP
            if key == glfw.KEY_T: rot_y -= ROT_STEP
            if key == glfw.KEY_F: rot_x += ROT_STEP
            if key == glfw.KEY_G: rot_x -= ROT_STEP
        if action == glfw.PRESS:
            if key == glfw.KEY_RIGHT: pos_x_inc =  MOV_STEP
            if key == glfw.KEY_LEFT:  pos_x_inc = -MOV_STEP
            if key == glfw.KEY_UP:    pos_y_inc =  MOV_STEP
            if key == glfw.KEY_DOWN:  pos_y_inc = -MOV_STEP
        if action == glfw.RELEASE:
            if key in (glfw.KEY_RIGHT, glfw.KEY_LEFT): pos_x_inc = 0.0
            if key in (glfw.KEY_UP,    glfw.KEY_DOWN): pos_y_inc = 0.0
        if key == glfw.KEY_P and action == glfw.PRESS:
            wireframe = not wireframe

    glfw.set_key_callback(window, key_event)
    glfw.show_window(window)
    glEnable(GL_DEPTH_TEST)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        pos_x = max(-MOV_LIMIT, min(MOV_LIMIT, pos_x + pos_x_inc))
        pos_y = max(-MOV_LIMIT, min(MOV_LIMIT, pos_y + pos_y_inc))

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.0, 0.15, 0.35, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

        mat = multiplica_matriz(
            mat_translacao(pos_x, pos_y, 0.0),
            multiplica_matriz(mat_rotacao_y(rot_y), mat_rotacao_x(rot_x))
        )
        glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)
        for nome, (start, count, cor) in partes.items():
            glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
            glDrawArrays(GL_TRIANGLES, start, count)

        glfw.swap_buffers(window)

    glfw.terminate()
