# Projeto 1 — Fundo do Mar | SCC0250 Computação Gráfica ICMC-USP

> **Aviso:** Este README é documentação interna para entendimento do código. Não entregar junto com o projeto.

---

## Índice

1. [O que é o trabalho](#1-o-que-é-o-trabalho)
2. [Requisitos e como os atendemos](#2-requisitos-e-como-os-atendemos)
3. [Como rodar](#3-como-rodar)
4. [Conceitos fundamentais de OpenGL usados](#4-conceitos-fundamentais-de-opengl-usados)
5. [Arquitetura do código](#5-arquitetura-do-código)
6. [Como as transformações geométricas funcionam](#6-como-as-transformações-geométricas-funcionam)
7. [Como cada objeto foi implementado](#7-como-cada-objeto-foi-implementado)
8. [O loop de renderização](#8-o-loop-de-renderização)
9. [Controles do teclado](#9-controles-do-teclado)
10. [Problemas encontrados e como foram resolvidos](#10-problemas-encontrados-e-como-foram-resolvidos)

---

## 1. O que é o trabalho

O objetivo é criar um programa em Python usando OpenGL que exiba uma janela com uma **cena animada e interativa**. O tema escolhido foi **fundo do mar**.

A cena contém 6 objetos distintos:
- 🦈 **Tubarão fofo** (controlado pelo jogador)
- 🐚 **Concha com pérola** (tampa que abre e fecha)
- 🪼 **Água-viva** (oscila e rotaciona automaticamente — 3 instâncias)
- ⭐ **Estrela-do-mar** (gira com o teclado)
- 🌿 **Alga marinha** (decoração estática — 8 instâncias)
- 🫧 **Bolhas de água** (sobem pela tela, escala controlável)

O programa usa **exclusivamente o pipeline moderno do OpenGL** — sem funções antigas como `glRotate`, `glTranslate`, `glColor`, etc. Tudo é feito via shaders e matrizes de transformação calculadas manualmente.

---

## 2. Requisitos e como os atendemos

### Requisito 1 — 5+ objetos distintos, pelo menos 2 em 3D
> ⚠️ Repetições do mesmo objeto (ex: 3 água-vivas iguais) contam como **um** objeto.

| Objeto | Tipo | Instâncias na cena |
|--------|------|-------------------|
| Tubarão | **3D** | 1 |
| Concha + Pérola | **3D** | 1 |
| Água-viva | **3D** | 3 (conta como 1) |
| Bolhas | **3D** | 12 (conta como 1) |
| Estrela-do-mar | 2D | 1 |
| Alga | 2D | 8 (conta como 1) |

**Total: 6 objetos distintos, 4 em 3D. ✅**

---

### Requisito 2 — Objetos devem ser composições de primitivas, não apenas esfera/cubo/triângulo

Cada objeto é composto de múltiplas peças geradas matematicamente:

- **Tubarão**: elipsoide paramétrico + pirâmide (nadadeira dorsal) + triângulos (peitorais) + V duplo (cauda) + esferas (olhos) + arco de sorriso
- **Concha**: dois meios-elipsoides (base + tampa) + esfera (pérola)
- **Água-viva**: meio-elipsoide (domo) + faixa paramétrica (anel/saia) + 8 fitas retangulares (tentáculos)
- **Estrela-do-mar**: polígono estrela de 10 vértices + 5 elipses decorativas + círculo central
- **Alga**: 7 faixas em zig-zag (caule) + 4 elipses inclinadas (folhas)
- **Bolha**: esfera 3D + meia-elipse branca (reflexo de luz)

**✅**

---

### Requisito 3 — Cada objeto com sua própria matriz de transformação

No loop de renderização, antes de desenhar cada objeto, calculamos uma matriz 4×4 específica para ele. Essa matriz é enviada para a GPU via `glUniformMatrix4fv`. **✅**

---

### Requisito 4 — Escala, rotação e translação em **objetos diferentes**

| Transformação | Objeto | Tecla |
|---|---|---|
| **Translação** | Tubarão | Setas ←→↑↓ |
| **Rotação** | Estrela-do-mar | Q / E |
| **Escala** | Bolhas | Z / X |

**✅ Três objetos diferentes, três transformações diferentes.**

---

### Requisitos 5, 6, 7 — Teclado para translação, escala e rotação
Atendidos pelos controles acima. **✅**

---

### Requisito 8 — Cena com objetivo bem definido
Tema coerente: fundo do mar com animações que fazem sentido (água-vivas flutuando, bolhas subindo, concha na areia). **✅**

---

### Requisito 9 — Tecla P alterna wireframe
A tecla `P` chama `glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)` para mostrar a malha de triângulos, ou `GL_FILL` para voltar ao modo normal. **✅**

---

### Requisito 10 — Sem textura, câmera ou iluminação
O programa usa apenas cores sólidas por objeto (uniform `color`). Sem projeção de câmera, sem luz, sem textura. **✅**

---

## 3. Como rodar

### Dependências
```bash
pip install pyopengl glfw numpy
```

### Rodar a cena completa
```bash
python cena.py
```

### Rodar um objeto isolado (para debug/visualização)
```bash
python tubarao.py
python concha.py
python estrela.py
python alga.py
python bolha.py
```

---

## 4. Conceitos fundamentais de OpenGL usados

### 4.1 Pipeline moderno vs. pipeline antigo

O OpenGL tem dois modos: o antigo (deprecated) e o moderno. O antigo tinha funções como `glRotate()`, `glColor()`, `glBegin()`/`glEnd()` que faziam tudo automaticamente. O moderno exige que você faça tudo manualmente, mas é o que roda em hardware real.

Neste projeto usamos **apenas o pipeline moderno**.

### 4.2 Shaders

Shaders são programas escritos em GLSL (uma linguagem parecida com C) que rodam **dentro da placa de vídeo**. Usamos dois:

#### Vertex Shader
```glsl
attribute vec3 position;        // recebe a posicao de cada vertice (x, y, z)
uniform mat4 mat_transformation; // recebe a matriz de transformacao

void main(){
    gl_Position = mat_transformation * vec4(position, 1.0);
}
```
- `attribute`: dado que muda a cada vértice (a posição de cada ponto)
- `uniform`: dado que é igual para todos os vértices do mesmo draw call (a matriz)
- Multiplica a posição pela matriz → calcula onde na tela o vértice vai aparecer

#### Fragment Shader
```glsl
uniform vec4 color;  // cor (R, G, B, A) — igual para todos os fragmentos

void main(){
    gl_FragColor = color;
}
```
- Roda uma vez para cada pixel que o triângulo cobre
- Simplesmente pinta o pixel com a cor informada

### 4.3 VBO — Vertex Buffer Object

O VBO é um bloco de memória **na placa de vídeo** que armazena todos os vértices. Criamos um único VBO com os vértices de **todos os objetos** concatenados:

```
VBO: [vertices_agua_viva | vertices_concha | vertices_tubarao | vertices_alga | vertices_estrela | vertices_bolha]
```

Cada objeto sabe seu pedaço: `(start_index, count)`. Quando desenhamos, dizemos:
```python
glDrawArrays(GL_TRIANGLES, start, count)
# "use os vértices do VBO a partir do índice 'start', desenhando 'count' vértices como triângulos"
```

### 4.4 Coordenadas NDC

Sem matriz de projeção ou câmera, os objetos são posicionados diretamente em **NDC (Normalized Device Coordinates)**:
- x ∈ [-1, +1] → da esquerda para a direita da tela
- y ∈ [-1, +1] → de baixo para cima da tela
- z ∈ [-1, +1] → profundidade (**z menor = mais na frente**)

⚠️ **Atenção**: O eixo z é contra-intuitivo. Objetos com z **negativo** aparecem **na frente**. Por isso, o reflexo das bolhas está em `cz = -0.82` (na frente da esfera) e não `+0.82` (que ficaria atrás).

### 4.5 Depth Test

```python
glEnable(GL_DEPTH_TEST)
```

Ativa o teste de profundidade: quando dois objetos se sobrepõem na tela, o que tem z menor (mais negativo) aparece na frente, escondendo o outro. Sem isso, o último objeto desenhado apareceria sempre na frente.

---

## 5. Arquitetura do código

### Estrutura de arquivos

```
projeto_1/
├── cena.py        # PROGRAMA PRINCIPAL — integra tudo
├── tubarao.py     # Geometria do tubarão (build_tubarao)
├── concha.py      # Geometria da concha (build_concha)
├── estrela.py     # Geometria da estrela (build_estrela)
├── alga.py        # Geometria da alga (build_alga)
└── bolha.py       # Geometria da bolha (build_bolha)
```

### Como os arquivos se relacionam

Cada arquivo de objeto (tubarao.py, concha.py, etc.) tem duas responsabilidades:

1. **`build_*(vl)`** — função que gera a geometria e pode ser importada por `cena.py`
2. **`if __name__ == '__main__':`** — código para rodar o objeto isolado (para visualização/debug)

O `cena.py` faz:
```python
from tubarao import build_tubarao
from concha  import build_concha
from estrela import build_estrela
from alga    import build_alga
from bolha   import build_bolha
```

E chama cada função passando a lista de vértices compartilhada:
```python
vertices_list = []
partes_tubarao = build_tubarao(vertices_list)    # adiciona vértices do tubarão
partes_concha_base, partes_concha_tampa, RZ = build_concha(vertices_list)  # adiciona vértices da concha
# ... etc
```

Cada `build_*` **appenda** seus vértices no `vertices_list` e retorna um dicionário `partes`:
```python
partes = {
    'nome_da_parte': (start_index, count, (R, G, B, A)),
    # ex:
    'dorso':  (0,   960, (0.38, 0.50, 0.65, 1.0)),
    'barriga':(960, 960, (0.88, 0.92, 0.97, 1.0)),
    ...
}
```

### Por que um único VBO?

Seria possível criar um VBO por objeto, mas um VBO único é mais eficiente: enviamos todos os dados para a GPU **uma vez só** no início do programa. Durante o loop de renderização, só mudamos os uniforms (matriz e cor) — não movemos dados entre CPU e GPU a cada frame.

---

## 6. Como as transformações geométricas funcionam

### Matrizes 4×4

Todas as transformações 3D são representadas como matrizes 4×4. Usamos coordenadas homogêneas — o ponto (x, y, z) vira o vetor (x, y, z, 1).

#### Translação — move o objeto
```
T(tx, ty, tz) = | 1  0  0  tx |
                | 0  1  0  ty |
                | 0  0  1  tz |
                | 0  0  0   1 |
```

#### Escala — aumenta/diminui o objeto
```
S(sx, sy, sz) = | sx  0   0  0 |
                |  0  sy  0  0 |
                |  0   0  sz  0 |
                |  0   0   0  1 |
```

#### Rotação em Z — gira no plano XY (o que a estrela usa)
```
Rz(θ) = | cos(θ)  -sin(θ)  0  0 |
         | sin(θ)   cos(θ)  0  0 |
         |   0        0     1  0 |
         |   0        0     0  1 |
```

### Composição de matrizes

Para aplicar múltiplas transformações, multiplicamos as matrizes. A ordem importa!

A convenção é: a transformação mais à **direita** é aplicada **primeiro**.

```python
mat = T × Ry × Rx
# Aplicação: primeiro Rx (gira em X), depois Ry (gira em Y), depois T (translada)
```

Para o tubarão:
```python
mat_tubarao = multiplica_matriz(
    mat_translacao(tubarao_x, tubarao_y, 0.0),   # 3. move para posição na cena
    multiplica_matriz(
        mat_rotacao_y(tubarao_rot_y),              # 2. rotaciona em Y
        mat_rotacao_x(tubarao_rot_x)               # 1. rotaciona em X
    )
)
```

### `multiplica_matriz`

```python
def multiplica_matriz(a, b):
    return np.dot(a.reshape(4,4), b.reshape(4,4)).reshape(1, 16)
```

O OpenGL espera a matriz como um array de 16 floats. A função converte para 4×4, faz a multiplicação matricial com `np.dot`, e volta para formato plano (1×16).

### Como a matriz chega na GPU

```python
glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)
#                  ^          ^ ^          ^
#                  location   1 matrix    transposta (GL_TRUE = sim, transpor)
#                             matrix
```

`GL_TRUE` indica que a matriz deve ser transposta. Isso acontece porque o numpy armazena em **row-major** (linha por linha) mas o OpenGL espera **column-major** (coluna por coluna).

---

## 7. Como cada objeto foi implementado

### 7.1 Tubarão (tubarao.py)

O tubarão é o objeto mais complexo, composto de 7 partes.

#### Corpo — elipsoide paramétrico

Um elipsoide é uma esfera "esticada". A fórmula paramétrica é:
```
x = RX * cos(v)
y = RY * sin(v) * sin(u)
z = RZ * sin(v) * cos(u)

com u ∈ [0, 2π]  e  v ∈ [0, π]
RX = 0.28 (comprimento — eixo longo, tubarão aponta para +x)
RY = 0.13 (altura)
RZ = 0.16 (largura)
```

O corpo é dividido em dois: **dorso** (u de 0 a π, y ≥ 0 = parte de cima, azul-cinza) e **barriga** (u de π a 2π, y ≤ 0 = parte de baixo, branco). Cada metade é uma lista de setores (N_SET=16) × pilhas (N_PIL=10) = 160 quads = 320 triângulos.

Cada quad é formado por 4 pontos (p0, p1, p2, p3) e dividido em 2 triângulos:
```
p0 --- p2       Triângulo 1: p0, p2, p1
|    / |        Triângulo 2: p3, p1, p2
|   /  |
p1 --- p3
```

#### Nadadeira dorsal — pirâmide de base retangular

4 vértices formam a base retangular no topo do corpo, e um vértice `apex` no topo. 4 triângulos laterais + 2 triângulos para fechar a base = 6 triângulos.

#### Nadadeiras peitorais — triângulos simples

Dois triângulos, um de cada lado. Cada um tem 3 vértices: ponto frontal, ponto traseiro e ponta lateral.

#### Cauda — dois lobos em V

6 vértices formando 2 triângulos que abrem em V a partir da traseira do corpo.

#### Olhos — esferas 3D

Cada olho é uma esfera paramétrica menor posicionada na lateral frontal do tubarão. A função `esfera_pos(cx, cy, cz, r)` gera uma esfera de raio `r` centrada em `(cx, cy, cz)`.

A **íris** (esfera branca) está em `(EX, EY, ±EZ)`. A **pupila** (esfera preta menor) está deslocada em `+x` — ou seja, para a frente da face do tubarão — para parecer que está olhando para frente.

#### Sorriso — arco paramétrico

8 triângulos em leque formam um arco na frente do focinho:
```
z = BRZ * cos(t)           } com t ∈ [0, π]
y = BCY - BRY * sin(t)     } cria curva que vai para baixo = sorriso
```

---

### 7.2 Concha (concha.py)

A concha usa a mesma fórmula paramétrica de elipsoide, mas com o eixo y como polo:
```
x = RX * sin(v) * cos(u)
y = RY * cos(v)
z = RZ * sin(v) * sin(u)
```

Dividindo as "pilhas" no meio (v = π/2, onde y = 0):
- **Base** (pilhas do meio até o final): y vai de 0 até -RY → forma uma tigela aberta para cima
- **Tampa** (pilhas de 0 até o meio): y vai de +RY até 0 → forma um domo

#### Pérola

Esfera pequena centrada dentro da base, deslocada um pouco para cima (-RY × 0.35) para ficar no interior. Dividida em dois meios com cores ligeiramente diferentes (branco-pérola e branco-azulado).

#### Animação da tampa (hinge)

A tampa gira em torno do "hinge" (dobradura), que é o ponto mais atrás da borda (z = +RZ). A composição de matrizes para isso é:

```
mat_tampa = T(cena) × Rx(tilt) × T(+hinge) × Rx(angle_lid) × T(-hinge)
```

Lendo da direita para a esquerda:
1. `T(-hinge)`: move o ponto de dobradura para a origem
2. `Rx(angle_lid)`: rotaciona a tampa em torno da origem (= em torno do hinge)
3. `T(+hinge)`: devolve o hinge para seu lugar
4. `Rx(tilt)`: inclina a concha -50° para mostrar o interior ao usuário
5. `T(cena)`: posiciona na cena

---

### 7.3 Água-viva (cena.py — build_agua_viva)

A água-viva não tem arquivo standalone porque é sempre decoração automática.

#### Domo — meio-elipsoide

Mesma fórmula da concha, mas só a metade superior (v de 0 a π/2 → y de +RY até 0).

#### Anel/saia — uma faixa paramétrica extra

Uma única "pilha" extra do elipsoide, abaixo do domo, para dar volume à borda.

#### Tentáculos — 8 fitas retangulares

Para cada tentáculo `i` de 0 a 7:
1. Calcula o ângulo `u = 2π × i / 8`
2. O ponto base é `(RX×cos(u), 0, RZ×sin(u))` — na borda do domo
3. O vetor perpendicular no plano XZ `(-sin(u), 0, cos(u))` dá a largura
4. 2 triângulos formam a fita que desce até y = -TENT_LEN

#### Animação automática

No loop, para cada água-viva `av`:
```python
t = aviva_t  # contador de tempo global
y = av['by'] + av['amp'] * sin(t * av['freq'] + av['phase'])  # oscilação vertical
pulso = 0.88 + 0.12 * sin(t * av['freq'] * 2 + av['phase'])  # pulsação (escala y)
av['rot'] += av['rot_speed']  # rotação própria em Y
```

Cada instância tem `freq` e `phase` diferentes → oscilam de forma dessincronizada, parecendo independentes.

---

### 7.4 Estrela-do-mar (estrela.py)

#### Corpo — polígono estrela

10 vértices no contorno, alternando entre raio externo (R_EXT=0.22, nas pontas) e raio interno (R_INT=0.09, nos vales). Cada vértice está em ângulo `base + 2π×i/10`. O centro é conectado a cada par de vértices adjacentes → 10 triângulos.

#### Detalhes nas pontas — elipses

Uma elipse girada na direção de cada ponta, posicionada a 62% do caminho até a ponta. Serve como textura visual.

#### Centro — círculo de destaque

Um círculo (leque de triângulos) na origem, em z ligeiramente negativo para aparecer na frente do corpo.

---

### 7.5 Alga (alga.py)

#### Caule — faixa em zig-zag

7 pontos centrais em alturas crescentes (y de 0 a 0.88), com um deslocamento horizontal que alterna seno:
```python
x = amplitude * sin(π × i)  # alterna entre +amp, 0, -amp, 0, ...
```

Para cada segmento entre dois pontos consecutivos, geramos uma faixa retangular:
- Calculamos o vetor perpendicular ao segmento
- 4 cantos = 2 triângulos

#### Folhas — elipses inclinadas

4 elipses, alternando lados (direita/esquerda), cada uma inclinada ±35° da vertical.

#### Múltiplas instâncias

A alga é desenhada 8 vezes com matrizes diferentes (`T(x) × Rz(ângulo) × S(escala)`). A **mesma geometria** no VBO é reutilizada — o que muda é só a matriz enviada à GPU.

---

### 7.6 Bolha (bolha.py)

#### Template reutilizável

A bolha é o caso mais extremo de reutilização: uma **única** geometria de esfera no VBO é desenhada 12 vezes, uma para cada bolha, com matrizes `T(x, y) × S(r, r, r)` diferentes.

```python
for b in bolhas:
    b['y'] += b['speed']          # sobe devagar
    r = b['r'] * bolha_escala     # raio × fator de escala global (teclas Z/X)
    mat = T(b['x'], b['y'], 0) × S(r, r, r)
    # desenha esfera + reflexo com esta matriz
```

#### Reflexo — meia-elipse

A meia-elipse é gerada com `t ∈ [0, π]`, que produz o arco superior de uma elipse:
```python
x = cx + ax * cos(t)
y = cy + ay * sin(t)
z = cz  # fixo (plano)
```

O ponto `center = (cx, cy, cz)` é conectado a cada par de pontos do arco → leque de triângulos.

**Por que cz = -0.82?** A esfera unitária tem sua face frontal (a que o usuário vê) em z negativo (lembre: z menor = mais perto). A face frontal em x=0.38, y=0.55 está em z ≈ -0.74. Para o reflexo aparecer na frente, precisa de z < -0.74, por isso usamos -0.82.

---

## 8. O loop de renderização

O loop roda indefinidamente até o usuário fechar a janela:

```python
while not glfw.window_should_close(window):
    glfw.poll_events()          # processa eventos de teclado/mouse

    # 1. Atualiza estado (posição do tubarão, tempo das águas-vivas)
    tubarao_x += tubarao_x_inc
    aviva_t += 0.022

    # 2. Limpa a tela
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.0, 0.15, 0.35, 1.0)  # azul-escuro do fundo do mar

    # 3. Para cada objeto:
    #    a) Calcula a matriz
    #    b) Envia para a GPU: glUniformMatrix4fv(...)
    #    c) Para cada parte do objeto:
    #       - Envia a cor: glUniform4f(loc_color, R, G, B, A)
    #       - Desenha: glDrawArrays(GL_TRIANGLES, start, count)

    # 4. Mostra o frame
    glfw.swap_buffers(window)
```

### Double buffering

`glfw.swap_buffers(window)` troca dois buffers: enquanto um está sendo exibido, desenhamos no outro. Isso evita flickering (tremulação) na tela.

### A função `desenha`

```python
def desenha(partes_dict, mat):
    glUniformMatrix4fv(loc_trans, 1, GL_TRUE, mat)
    for nome, (start, count, cor) in partes_dict.items():
        glUniform4f(loc_color, cor[0], cor[1], cor[2], cor[3])
        glDrawArrays(GL_TRIANGLES, start, count)
```

Helper que aplica a matriz e desenha todas as partes de um objeto. Usado para tubarão, concha, estrela, algas e água-vivas.

---

## 9. Controles do teclado

| Tecla | Efeito | Objeto |
|-------|--------|--------|
| `←` `→` `↑` `↓` | Move | Tubarão |
| `R` / `T` | Gira no eixo Y | Tubarão |
| `F` / `G` | Gira no eixo X | Tubarão |
| `A` / `S` | Abre / fecha a tampa | Concha |
| `Q` / `E` | Gira no sentido anti/horário | Estrela-do-mar |
| `Z` / `X` | Aumenta / diminui | Bolhas (todas) |
| `P` | Alterna wireframe | Global (todos) |

### Como o teclado funciona no GLFW

```python
def key_event(window, key, scancode, action, mods):
    # action pode ser: glfw.PRESS, glfw.RELEASE, glfw.REPEAT
    if action == glfw.PRESS or action == glfw.REPEAT:
        # REPEAT: ativado quando a tecla fica pressionada
        ...

glfw.set_key_callback(window, key_event)
```

Para o **movimento suave** do tubarão usamos uma técnica de velocidade acumulada:
- `PRESS`: define incremento (`tubarao_x_inc = +STEP`)
- `RELEASE`: zera o incremento (`tubarao_x_inc = 0`)
- A cada frame: `tubarao_x += tubarao_x_inc`

Isso faz o tubarão se mover continuamente enquanto a tecla está pressionada, e parar suavemente ao soltar.

---

## 10. Problemas encontrados e como foram resolvidos

### Problema 1 — z invertido (reflexo da bolha não aparecia)

**O que aconteceu**: Colocamos o reflexo em `cz = +0.82` esperando que ficasse na frente da esfera. Mas não aparecia nada.

**Por quê**: No OpenGL sem matriz de projeção, fragmentos com z **menor** (mais negativo) ganham o depth test e aparecem na frente. A face frontal da esfera unitária está em z ≈ -0.74 (negativo). Com `cz = +0.82`, o reflexo estava atrás da esfera inteira.

**Solução**: Usar `cz = -0.82`, que é mais negativo que -0.74, logo aparece na frente.

---

### Problema 2 — código duplicado entre standalone e cena.py

**O que aconteceu**: Cada objeto tinha seu código de geometria escrito duas vezes — uma no arquivo standalone e outra dentro de `build_*` no `cena.py`.

**Solução**: Cada arquivo standalone expõe uma função `build_*` no topo, e o código OpenGL (janela, shaders, VBO, loop) foi colocado dentro de `if __name__ == '__main__':`. O `cena.py` importa `build_*` de cada arquivo.

```python
# Se rodar direto: python tubarao.py
if __name__ == '__main__':
    # setup OpenGL + loop standalone

# Se importado: from tubarao import build_tubarao
# → só executa build_tubarao, não o bloco acima
```

---

### Problema 3 — bolhas "apenas uma esfera" não atende ao requisito 2

**O que aconteceu**: As bolhas eram somente esferas, o que é uma primitiva básica.

**Solução**: Adicionamos uma **meia-elipse branca** no canto superior direito de cada bolha, simulando o reflexo de luz. Agora cada bolha é composta de duas peças geometricamente distintas.

---

### Problema 4 — água-viva era borderline para o requisito 2

**O que aconteceu**: O domo da água-viva é apenas um meio-elipsoide (variação de esfera).

**Mitigação**: Adicionamos o anel/saia e os 8 tentáculos como fitas retangulares. Com 3 partes distintas, o objeto se torna uma composição válida. Além disso, os outros 5 objetos são claramente compostos, então mesmo que a água-viva seja questionada, o requisito 1 ainda é atendido com 5 objetos restantes.

---

## 11. Walkthrough do cena.py — linha a linha

Esta seção explica o que cada bloco do arquivo principal faz, em ordem de execução.

### Bloco 1 — Imports

```python
import glfw          # biblioteca de janela e eventos (teclado, mouse, loop)
from OpenGL.GL import *  # funções do OpenGL (gl*, GL_*)
import numpy as np   # arrays numéricos (vértices, matrizes)
import math          # seno, cosseno, pi
import ctypes        # para passar ponteiro nulo ao OpenGL (offset do VBO)
import random        # para posição aleatória das bolhas

from tubarao import build_tubarao  # importa a geometria de cada objeto
from concha  import build_concha   # (o código só existe em um lugar)
from estrela import build_estrela
from alga    import build_alga
from bolha   import build_bolha
```

### Bloco 2 — Inicialização da janela

```python
glfw.init()                              # inicializa a biblioteca GLFW
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)  # começa invisível (mostramos depois)
window = glfw.create_window(900, 700, "Fundo do Mar", None, None)
glfw.make_context_current(window)        # torna esta janela o contexto OpenGL ativo
```

É necessário ter um contexto OpenGL antes de chamar qualquer função `gl*`. O contexto é criado junto com a janela pelo GLFW.

### Bloco 3 — Compilação dos shaders

```python
program  = glCreateProgram()             # cria o programa de shader na GPU
vertex   = glCreateShader(GL_VERTEX_SHADER)
fragment = glCreateShader(GL_FRAGMENT_SHADER)

glShaderSource(vertex, vertex_code)      # envia o código fonte para a GPU
glCompileShader(vertex)                  # compila na GPU
# (mesma coisa para o fragment)

glAttachShader(program, vertex)          # anexa os dois shaders ao programa
glAttachShader(program, fragment)
glLinkProgram(program)                   # linka (como um executável)
glUseProgram(program)                    # ativa este programa para uso
```

Isso acontece **uma vez só** no início. Os shaders ficam carregados na GPU para o resto da execução.

### Bloco 4 — Funções de matrizes e geometria

As funções `multiplica_matriz`, `mat_translacao`, `mat_escala`, `mat_rotacao_*` são definidas aqui. São funções puras de matemática — não chamam nada do OpenGL.

### Bloco 5 — Construção do VBO

```python
vertices_list = []  # lista Python, cresce conforme adicionamos objetos

partes_aviva                             = build_agua_viva(vertices_list)
partes_concha_base, partes_concha_tampa, CONCHA_HINGE_Z = build_concha(vertices_list)
partes_tubarao                           = build_tubarao(vertices_list)
partes_alga                              = build_alga(vertices_list)
partes_estrela                           = build_estrela(vertices_list)
bolha_geo_start, bolha_geo_count, \
reflexo_geo_start, reflexo_geo_count     = build_bolha(vertices_list)
```

Cada `build_*` recebe a lista, appenda seus vértices e retorna os índices. Depois:

```python
vertices = np.zeros(total, [("position", np.float32, 3)])
vertices['position'] = np.array(vertices_list)

buffer_VBO = glGenBuffers(1)             # cria o buffer na GPU
glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO)  # seleciona este buffer
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
# GL_DYNAMIC_DRAW: o buffer pode ser lido frequentemente (dica de otimização)
```

### Bloco 6 — Configuração do atributo `position`

```python
loc_pos = glGetAttribLocation(program, "position")  # onde o shader lê a posição
glEnableVertexAttribArray(loc_pos)
glVertexAttribPointer(loc_pos, 3, GL_FLOAT, False, stride, offset)
# "o atributo 'position' tem 3 floats, stride=tamanho de um vértice, offset=0"
```

Isso conecta o VBO ao atributo `position` do vertex shader. A cada `glDrawArrays`, a GPU lê os vértices do VBO automaticamente.

### Bloco 7 — Localização dos uniforms

```python
loc_color = glGetUniformLocation(program, "color")       # onde enviar a cor
loc_trans = glGetUniformLocation(program, "mat_transformation")  # onde enviar a matriz
```

`loc_color` e `loc_trans` são inteiros (IDs). Usamos eles mais tarde com `glUniform4f` e `glUniformMatrix4fv`.

### Bloco 8 — Estado global e posições fixas

Definimos aqui as posições de cada objeto na cena (constantes) e as variáveis de estado que mudam com o teclado:

```python
AVIVAS = [...]        # 3 dicionários com parâmetros de cada água-viva
CONCHA_POS = (...)    # posição fixa da concha
ALGAS = [...]         # 8 posições e inclinações das algas
ESTRELA_POS = (...)   # posição da estrela

tubarao_x = 0.0      # posição atual do tubarão (muda com as setas)
tubarao_rot_y = 0.0  # ângulo atual (muda com R/T)
bolha_escala = 1.0   # fator de escala das bolhas (muda com Z/X)
# ... etc
```

### Bloco 9 — Callback de teclado

```python
def key_event(window, key, scancode, action, mods):
    # Modifica as variáveis de estado baseado na tecla pressionada
    ...

glfw.set_key_callback(window, key_event)
```

Esta função é chamada pelo GLFW **automaticamente** quando uma tecla é pressionada, repetida ou solta. Ela nunca é chamada diretamente no código — o GLFW a chama via `glfw.poll_events()`.

### Bloco 10 — Loop principal

```python
glfw.show_window(window)    # agora mostra a janela
glEnable(GL_DEPTH_TEST)     # ativa o teste de profundidade

while not glfw.window_should_close(window):
    glfw.poll_events()      # GLFW processa eventos → chama key_event se necessário

    # Atualiza posições
    tubarao_x = clamp(tubarao_x + tubarao_x_inc, -LIMITE, +LIMITE)
    aviva_t += 0.022         # tempo avança a cada frame (~60 fps → ~1.3 seg por ciclo)

    # Limpa
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.0, 0.15, 0.35, 1.0)

    # Wireframe ou fill
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)

    # Desenha cada objeto com sua matriz
    desenha(partes_aviva, mat_av)          # água-vivas (3x em loop)
    desenha(partes_concha_base, mat_base)  # concha base
    desenha(partes_concha_tampa, mat_lid)  # concha tampa
    desenha(partes_tubarao, mat_tubarao)   # tubarão
    desenha(partes_alga, mat_alga)         # algas (8x em loop)
    desenha(partes_estrela, mat_estrela)   # estrela
    # bolhas (12x em loop manual — dois glDrawArrays por bolha)

    glfw.swap_buffers(window)  # mostra o frame desenhado
```

---

## 12. Glossário

| Termo | Significado |
|-------|-------------|
| **Shader** | Programa que roda na GPU. Vertex shader processa vértices, fragment shader processa pixels. |
| **VBO** | Vertex Buffer Object — bloco de memória na GPU com os vértices. |
| **Uniform** | Variável enviada da CPU para a GPU que é igual para todos os vértices do mesmo draw call. |
| **Attribute** | Variável que muda a cada vértice (ex: posição). |
| **NDC** | Normalized Device Coordinates — sistema de coordenadas da tela: x,y,z ∈ [-1,+1]. |
| **Depth test** | Mecanismo que decide qual objeto aparece na frente quando há sobreposição. |
| **Double buffer** | Técnica de desenhar num buffer escondido e exibir só quando pronto (evita flickering). |
| **Partes** | Dicionário `nome → (start, count, cor)` que descreve as subdivisões de um objeto. |
| **Paramétrico** | Superfície definida por equações com parâmetros u,v. Permite gerar formas complexas matematicamente. |
| **Elipsoide** | Esfera "esticada" em um ou mais eixos. Usada para o corpo do tubarão e da concha. |
| **Hinge** | Ponto de dobradura da tampa da concha. A tampa rotaciona em torno dele. |
| **Row-major / Column-major** | Ordem de armazenamento de matrizes. NumPy usa row-major, OpenGL espera column-major — por isso usamos `GL_TRUE` na transposição. |
| **glDrawArrays** | Comando que manda a GPU desenhar triângulos usando os vértices do VBO. |
| **poll_events** | Função do GLFW que processa eventos pendentes (teclado, mouse, fechar janela). |
| **swap_buffers** | Troca o buffer de renderização com o buffer de exibição (double buffering). |

---

## 13. Como estudar o código para a apresentação

### Ordem sugerida de leitura

1. **Leia este README completo** (você está fazendo isso)
2. **Abra `bolha.py`** — é o mais simples. Entenda o `build_bolha` e o `if __name__ == '__main__':`
3. **Abra `estrela.py`** — entenda como um polígono 2D é construído com triângulos em leque
4. **Abra `alga.py`** — entenda a geração de faixas (caule) e elipses (folhas)
5. **Abra `concha.py`** — entenda a parametrização do elipsoide e a composição de matrizes da tampa
6. **Abra `tubarao.py`** — o mais complexo; veja como cada parte é adicionada à lista
7. **Abra `cena.py`** — veja como tudo se integra; o loop e os callbacks

### Perguntas que o professor pode fazer

**"Como você gerou o corpo do tubarão?"**
> Usando parametrização de elipsoide: `x = RX·cos(v)`, `y = RY·sin(v)·sin(u)`, `z = RZ·sin(v)·cos(u)`. Dividimos os setores em dois grupos: u ∈ [0,π] para o dorso (azul) e u ∈ [π,2π] para a barriga (branca).

**"Como as transformações funcionam?"**
> Representamos cada transformação como uma matriz 4×4. Composição de transformações = multiplicação de matrizes (da direita para a esquerda). Enviamos a matriz final para a GPU via `glUniformMatrix4fv`, e o vertex shader multiplica cada vértice por ela.

**"Por que um VBO único?"**
> Eficiência: enviamos todos os vértices para a GPU uma vez só no início. Durante o loop, apenas mudamos os uniforms (matriz e cor), sem transferir dados. Cada objeto sabe seu pedaço via `(start, count)`.

**"Como a tampa da concha gira em torno da dobradura?"**
> Composição de matrizes: `T(cena) × Rx(tilt) × T(+hinge) × Rx(ângulo) × T(-hinge)`. O truque é mover o hinge para a origem, girar, e devolvê-lo ao lugar. Isso faz a rotação ocorrer em torno do hinge e não da origem do mundo.

**"Como o wireframe funciona?"**
> `glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)` faz o OpenGL desenhar apenas as arestas dos triângulos em vez de preenchê-los. `GL_FILL` volta ao normal. É um único toggle global.

**"Por que os objetos são composições de triângulos?"**
> O OpenGL só sabe desenhar triângulos (e pontos/linhas). Qualquer forma — esfera, elipse, cubo — precisa ser aproximada por uma malha de triângulos. Quanto mais triângulos, mais suave fica a superfície.

**"Como a água-viva oscila?"**
> Usamos `y = by + amp·sin(t·freq + phase)` onde `t` é um contador de tempo incrementado a cada frame. Cada água-viva tem `freq` e `phase` diferentes para parecerem independentes. O efeito de "pulso" é feito escalando y no render: `S(1, 0.88 + 0.12·sin(2t), 1)`.

**"Escala, rotação e translação precisam estar em objetos diferentes — como vocês fizeram?"**
> Translação nas setas do tubarão, rotação com Q/E na estrela-do-mar, escala com Z/X nas bolhas. São três objetos distintos, cada um com sua transformação exclusiva controlada pelo teclado.

---

*Gerado em março de 2026 para SCC0250 — ICMC USP São Carlos*
