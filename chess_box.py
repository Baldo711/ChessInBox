import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS
# ══════════════════════════════════════════════════════════════════════════════
ANCHO          = 155
PROFUNDIDAD    = 155
ALTURA         = 45
ALTURA_DIVISIONES = ALTURA * 0.7   # altura máxima de las divisiones internas (≤ ALTURA)
DIVISIONES_X   = 3
DIVISIONES_Y   = 3
DIVISIONES_Z   = 0
GROSOR_BASE    = 3   # grosor del suelo (dirección Z); independiente de las paredes
GROSOR_PARED_INT = 2
GROSOR_PARED_EXT = 3
RADIO_ESQ      = 3   # radio de redondeo esquinas exteriores (mm); max = GROSOR_PARED_EXT
N_SEG_ESQ      = 4   # segmentos de arco por esquina (mismo que ExS = visual consistente)


def crear_caja_correcta(ancho, profundidad, altura,
                        div_x, div_y, div_z,
                        grosor_int, grosor_ext,
                        grosor_base, altura_div,
                        radio_esq, n_seg_esq):
    """
    CP – Contenedor de Piezas con esquinas exteriores redondeadas.

    Estructura de vértices (5 anillos):
      A  – anillo exterior inferior  (z=0,  N vértices, redondeado)
      B  – anillo exterior a nivel del suelo interior (z=gb, N vértices, redondeado)
      C  – anillo interior a nivel del suelo (z=gb, 4 vértices, rectangular)
      D  – anillo exterior superior  (z=h,  N vértices, redondeado)
      E  – anillo interior superior  (z=h,  4 vértices, rectangular)

    Parámetros independientes:
      · grosor_base  → grosor del suelo (Z); puede diferir de grosor_ext
      · altura_div   → hasta dónde llegan las divisiones internas (≤ altura)
      · grosor_ext   → solo controla el grosor de las paredes externas (XY)

    Las esquinas interiores se mantienen rectangulares para no reducir el espacio
    interior y porque no son visibles. Las exteriores se redondean para que el ExS
    (que también usa RADIO_ESQ) encaje visualmente.

    Caras generadas (normales hacia afuera):
      · Fondo (ring A, normal -z)
      · Paredes exteriores A→B y B→D (N quads cada tramo)
      · Tiras del suelo B→C (triangulación annular exterior redondeado → interior recto)
      · Cara central del suelo (ring C, normal +z)
      · Paredes interiores C→E (4 quads, normales hacia el interior)
      · Borde superior D→E (triangulación annular, normal +z)
      · Divisiones internas hasta altura_div (cajas sólidas rectangulares)
    """

    ge = grosor_ext
    gb = grosor_base
    hd = max(gb, min(altura_div, altura))   # altura divisiones, clamped [gb, h]
    a  = ancho
    p  = profundidad
    h  = altura
    r  = max(0.5, min(radio_esq, ge))   # r ≤ ge para que la esquina interior quepa
    n  = max(2, n_seg_esq)
    N  = 4 * n

    # ── Material ──────────────────────────────────────────────────────────────
    mat = bpy.data.materials.new(name="Material_Caja")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.9, 1.0)

    # ── Mesh / Objeto ─────────────────────────────────────────────────────────
    mesh = bpy.data.meshes.new("CajaDividida")
    obj  = bpy.data.objects.new("CajaDividida", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vertices = []
    faces    = []

    # ── Polígono exterior redondeado (CCW desde arriba) ───────────────────────
    def rounded_rect_poly(x0, y0, x1, y1):
        """4*n puntos CCW para rectángulo con esquinas redondeadas."""
        pts = []
        for cx, cy, a0, a1 in [
            (x0+r, y0+r, math.pi,     3*math.pi/2),   # BL: 180°→270°
            (x1-r, y0+r, 3*math.pi/2, 2*math.pi  ),   # BR: 270°→360°
            (x1-r, y1-r, 0,           math.pi/2  ),   # TR:   0°→ 90°
            (x0+r, y1-r, math.pi/2,   math.pi    ),   # TL:  90°→180°
        ]:
            for i in range(n):
                ang = a0 + (a1 - a0) * i / n
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    outer_xy = rounded_rect_poly(0, 0, a, p)
    inner_xy = [(ge, ge), (a-ge, ge), (a-ge, p-ge), (ge, p-ge)]   # CCW

    # ── 5 Anillos ─────────────────────────────────────────────────────────────
    vA = len(vertices)
    for x, y in outer_xy:  vertices.append((x, y, 0 ))   # A: exterior z=0  (N verts)
    vB = len(vertices)
    for x, y in outer_xy:  vertices.append((x, y, gb))   # B: exterior z=gb (N verts)
    vC = len(vertices)
    for x, y in inner_xy:  vertices.append((x, y, gb))   # C: interior z=gb (4 verts)
    vD = len(vertices)
    for x, y in outer_xy:  vertices.append((x, y, h ))   # D: exterior z=h  (N verts)
    vE = len(vertices)
    for x, y in inner_xy:  vertices.append((x, y, h ))   # E: interior z=h  (4 verts)

    # ── Fondo exterior (ring A, normal -z): polígono N-gon en orden inverso ───
    faces.append(list(range(vA + N - 1, vA - 1, -1)))

    # ── Paredes exteriores A→B  (N quads) ────────────────────────────────────
    for i in range(N):
        j = (i + 1) % N
        faces.append([vA+i, vA+j, vB+j, vB+i])

    # ── Tiras del suelo B→C (outer N verts → inner 4 verts, normal +z) ───────
    # Misma triangulación que los aros de aleta en chess_exs.py
    def add_annular_rim(outer_base, inner_base, sign):
        """
        Triangula el aro horizontal entre el anillo exterior (N verts) y
        el interior (4 verts). sign=+1 → normal +z; sign=-1 → normal -z.
        """
        for k in range(4):
            nk    = (k + 1) % 4
            arc_s = k * n
            ik    = inner_base + k
            ik_n  = inner_base + nk

            # Abanico de triángulos sobre el arco k
            for i in range(n - 1):
                oi  = outer_base + (arc_s + i)     % N
                oii = outer_base + (arc_s + i + 1) % N
                if sign > 0:
                    faces.append([ik, oi, oii])    # normal +z
                else:
                    faces.append([ik, oii, oi])    # normal -z

            # Cuadrilátero puente hasta la siguiente esquina interior
            ol = outer_base + (arc_s + n - 1) % N
            of = outer_base + (nk * n)        % N
            if sign > 0:
                faces.append([ik, ol, of, ik_n])   # normal +z
            else:
                faces.append([ik, ik_n, of, ol])   # normal -z

    add_annular_rim(vB, vC, sign=+1)   # tiras del suelo  (B→C)

    # ── Cara central del suelo interior (ring C, normal +z) ──────────────────
    faces.append([vC, vC+1, vC+2, vC+3])

    # ── Paredes exteriores B→D  (N quads) ────────────────────────────────────
    for i in range(N):
        j = (i + 1) % N
        faces.append([vB+i, vB+j, vD+j, vD+i])

    # ── Paredes interiores C→E (4 quads, normal hacia el interior) ───────────
    for i in range(4):
        j = (i + 1) % 4
        faces.append([vC+i, vE+i, vE+j, vC+j])

    # ── Borde superior D→E (outer N verts → inner 4 verts, normal +z) ────────
    add_annular_rim(vD, vE, sign=+1)

    # ══════════════════════════════════════════════════════════════════════════
    # DIVISIONES INTERNAS (rectangulares, sin cambios)
    # ══════════════════════════════════════════════════════════════════════════
    def add_box(x0, y0, z0, x1, y1, z1):
        s = len(vertices)
        vertices.extend([
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ])
        faces.append([s,   s+3, s+2, s+1])  # fondo
        faces.append([s+4, s+5, s+6, s+7])  # techo
        faces.append([s,   s+1, s+5, s+4])  # frente
        faces.append([s+2, s+3, s+7, s+6])  # atrás
        faces.append([s,   s+4, s+7, s+3])  # izquierda
        faces.append([s+1, s+2, s+6, s+5])  # derecha

    # Divisiones en X
    paso_x = a / (div_x + 1)
    for i in range(1, div_x + 1):
        x = paso_x * i
        add_box(x - grosor_int/2, ge, gb, x + grosor_int/2, p-ge, hd)

    # Divisiones en Y
    paso_y = p / (div_y + 1)
    for i in range(1, div_y + 1):
        y = paso_y * i
        add_box(ge, y - grosor_int/2, gb, a-ge, y + grosor_int/2, hd)

    # Divisiones en Z
    if div_z > 0:
        paso_z = hd / (div_z + 1)
        for i in range(1, div_z + 1):
            z = paso_z * i
            add_box(ge, ge, z - grosor_int/2, a-ge, p-ge, z + grosor_int/2)

    # ── Construir mesh ────────────────────────────────────────────────────────
    mesh.from_pydata(vertices, [], faces)
    mesh.validate()
    mesh.update()

    # Recalcular normales
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.data.materials.append(mat)
    return obj


# ── Ejecutar ──────────────────────────────────────────────────────────────────
caja = crear_caja_correcta(
    ancho        = ANCHO,
    profundidad  = PROFUNDIDAD,
    altura       = ALTURA,
    div_x        = DIVISIONES_X,
    div_y        = DIVISIONES_Y,
    div_z        = DIVISIONES_Z,
    grosor_int   = GROSOR_PARED_INT,
    grosor_ext   = GROSOR_PARED_EXT,
    grosor_base  = GROSOR_BASE,
    altura_div   = ALTURA_DIVISIONES,
    radio_esq    = RADIO_ESQ,
    n_seg_esq    = N_SEG_ESQ,
)

print(f"✓ CP creada correctamente")
print(f"  Dimensiones: {ANCHO} x {PROFUNDIDAD} x {ALTURA} mm")
print(f"  Grosor pared exterior: {GROSOR_PARED_EXT} mm  |  interior: {GROSOR_PARED_INT} mm  |  base: {GROSOR_BASE} mm")
print(f"  Altura divisiones internas: {ALTURA_DIVISIONES:.1f} mm  (de {ALTURA} mm totales)")
print(f"  Esquinas: radio={RADIO_ESQ} mm  |  segmentos/esquina={N_SEG_ESQ}")
print(f"  Divisiones: {DIVISIONES_X}x{DIVISIONES_Y} (+ {DIVISIONES_Z} horizontales)")
