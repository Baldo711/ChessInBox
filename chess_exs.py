import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — los marcados (*) deben coincidir con chess_box.py
# ══════════════════════════════════════════════════════════════════════════════
ANCHO        = 155   # (*)
PROFUNDIDAD  = 155   # (*)
GROSOR_PARED = 3     # (*)
RADIO_ESQ    = 3     # (*)  radio de redondeo de esquinas exteriores
N_SEG_ESQ    = 4     # (*)  segmentos de arco por esquina

ALTURA_EXS    = 40
ALTO_ALETA    = 10
GROSOR_ALETA  = 2
TOLERANCIA    = 0.2   # holgura entre aleta interior y CP exterior (mm)
FRAC_SOLAPE   = 0.35  # fracción del alto de aleta embebida en el cuerpo ExS (≥0.35)

ANCHO_PLACA    = ANCHO * 0.5
ALTO_BASE_RIEL = 8
PROF_RIEL      = 2.5


def crear_exs(ancho, profundidad, altura, grosor_pared,
              alto_aleta, grosor_aleta, tolerancia, frac_solape, radio_esq, n_seg_esq,
              ancho_placa, alto_base_riel, prof_riel):
    """
    ExS – Extensor de Soporte.

    Cuerpo exterior redondeado (igual que CP) para consistencia visual.
    Aletas con AMBAS caras redondeadas:
      · Cara exterior: misma curvatura que cuerpo (r = RADIO_ESQ)
      · Cara interior: también redondeada con r = RADIO_ESQ, desplazada TOLERANCIA
                       hacia afuera → calza perfectamente con las esquinas del CP.

    Antes la cara interior era un rectángulo recto, lo que dejaba ~3 mm de
    separación en las esquinas respecto a las esquinas redondeadas del CP.
    """

    ge  = grosor_pared
    a   = ancho
    p   = profundidad
    h   = altura
    ga  = grosor_aleta
    fs  = max(0.0, min(1.0, frac_solape))   # clamp 0..1
    tol = tolerancia
    ha  = alto_aleta
    r   = max(0.5, radio_esq)
    n   = max(2, n_seg_esq)
    N   = 4 * n
    AO  = ga + tol   # cuánto sobresale la aleta más allá del ExS (2.2 mm)

    # ── Material ──────────────────────────────────────────────────────────────
    mat = bpy.data.materials.new(name="Material_ExS")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.9, 0.65, 0.3, 1.0)

    mesh = bpy.data.meshes.new("ExtensorSoporte")
    obj  = bpy.data.objects.new("ExtensorSoporte", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vertices = []
    faces    = []

    def rounded_rect_poly(x0, y0, x1, y1, rad=None):
        """
        4*n puntos CCW para un rectángulo con esquinas redondeadas.
        El orden de esquinas es: BL → BR → TR → TL (igual que chess_box.py).
        """
        rad = rad if rad is not None else r
        pts = []
        for cx, cy, a0, a1 in [
            (x0+rad, y0+rad, math.pi,      3*math.pi/2),   # BL
            (x1-rad, y0+rad, 3*math.pi/2,  2*math.pi  ),   # BR
            (x1-rad, y1-rad, 0,            math.pi/2  ),   # TR
            (x0+rad, y1-rad, math.pi/2,    math.pi    ),   # TL
        ]:
            for i in range(n):
                ang = a0 + (a1 - a0) * i / n
                pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        return pts

    # ── Triangulación N→4: outer ring (N verts) hacia inner rect (4 verts) ────
    # Igual que chess_box.py — usada para los bordes del cuerpo del ExS.
    def add_annular_rim_N4(outer_base, inner_base, sign):
        for k in range(4):
            nk    = (k + 1) % 4
            arc_s = k * n
            ik    = inner_base + k
            ik_n  = inner_base + nk
            for i in range(n - 1):
                oi  = outer_base + (arc_s + i)     % N
                oii = outer_base + (arc_s + i + 1) % N
                if sign > 0:
                    faces.append([ik, oi, oii])
                else:
                    faces.append([ik, oii, oi])
            ol = outer_base + (arc_s + n - 1) % N
            of = outer_base + (nk * n)        % N
            if sign > 0:
                faces.append([ik, ol, of, ik_n])
            else:
                faces.append([ik, ik_n, of, ol])

    # ══════════════════════════════════════════════════════════════════════════
    # CUERPO DEL ExS: marco abierto (sin techo ni suelo sólido)
    # Exterior redondeado (N verts) + Interior rectangular (4 verts)
    # ══════════════════════════════════════════════════════════════════════════

    body_outer = rounded_rect_poly(0, 0, a, p)
    body_inner = [(ge,ge),(a-ge,ge),(a-ge,p-ge),(ge,p-ge)]

    vEB = len(vertices)
    for x,y in body_outer:  vertices.append((x, y, 0))    # outer bottom (N)
    vIB = len(vertices)
    for x,y in body_inner:  vertices.append((x, y, 0))    # inner bottom (4)
    vET = len(vertices)
    for x,y in body_outer:  vertices.append((x, y, h))    # outer top (N)
    vIT = len(vertices)
    for x,y in body_inner:  vertices.append((x, y, h))    # inner top (4)

    # Paredes exteriores: N quads
    for i in range(N):
        j = (i + 1) % N
        faces.append([vEB+i, vEB+j, vET+j, vET+i])

    # Paredes interiores: 4 quads
    for i in range(4):
        j = (i + 1) % 4
        faces.append([vIB+i, vIT+i, vIT+j, vIB+j])

    # Borde inferior (z=0): anillo N→4, normal −z (cara visible desde abajo)
    add_annular_rim_N4(vEB, vIB, sign=-1)

    # Borde superior (z=h): anillo N→4, normal +z
    add_annular_rim_N4(vET, vIT, sign=+1)

    # ══════════════════════════════════════════════════════════════════════════
    # ANILLOS DE ALETA — ambas caras redondeadas, N vertices cada una
    #
    # Cara exterior: rounded_rect_poly(-AO, -AO, a+AO, p+AO, r)
    # Cara interior: rounded_rect_poly(-tol,-tol, a+tol, p+tol, r)
    #                ↑ con el mismo radio r y desplazada TOLERANCIA hacia afuera
    #                  → calza exactamente con las esquinas redondeadas del CP
    #
    # La aleta inferior abarca z de −ha a 0 (debajo del ExS, guía el CP inferior).
    # La aleta superior abarca z de  h a h+ha (guía el CP superior si se apila).
    # ══════════════════════════════════════════════════════════════════════════

    def add_aleta(z0, z1):
        o_xy = rounded_rect_poly(-AO,  -AO,  a+AO,  p+AO )   # exterior
        i_xy = rounded_rect_poly(-tol, -tol, a+tol, p+tol)   # interior (+tol sobre CP)

        s   = len(vertices)
        ob0 = s;       ob1 = s + N
        ib0 = s + 2*N; ib1 = s + 3*N

        for x,y in o_xy:  vertices.append((x, y, z0))   # outer bottom
        for x,y in o_xy:  vertices.append((x, y, z1))   # outer top
        for x,y in i_xy:  vertices.append((x, y, z0))   # inner bottom
        for x,y in i_xy:  vertices.append((x, y, z1))   # inner top

        for i in range(N):
            j = (i + 1) % N
            faces.append([ob0+i, ob0+j, ob1+j, ob1+i])   # paredes exteriores
            faces.append([ib0+i, ib1+i, ib1+j, ib0+j])   # paredes interiores
            faces.append([ob0+i, ib0+i, ib0+j, ob0+j])   # aro inferior
            faces.append([ob1+i, ob1+j, ib1+j, ib1+i])   # aro superior

    add_aleta(-(ha * (1 - fs)),  ha * fs     )   # inferior: fs*ha dentro, (1-fs)*ha hacia abajo
    add_aleta(h - ha * fs,       h + ha*(1-fs))  # superior: fs*ha dentro, (1-fs)*ha hacia arriba

    # ══════════════════════════════════════════════════════════════════════════
    # RIEL DE COLA DE MILANO — cara frontal (Y=0)
    # ══════════════════════════════════════════════════════════════════════════

    OVL_Y  = 1.0
    rx0    = (a - ancho_placa) / 2
    rx1    = (a + ancho_placa) / 2
    rz_c   = h / 2
    rz_bb  = rz_c - alto_base_riel / 2
    rz_bt  = rz_c + alto_base_riel / 2
    rz_tb  = rz_bb - prof_riel
    rz_tt  = rz_bt + prof_riel

    vR = len(vertices)
    vertices.extend([
        (rx0,  OVL_Y,     rz_bb),   # 0
        (rx0,  OVL_Y,     rz_bt),   # 1
        (rx0, -prof_riel, rz_tt),   # 2
        (rx0, -prof_riel, rz_tb),   # 3
        (rx1,  OVL_Y,     rz_bb),   # 4
        (rx1,  OVL_Y,     rz_bt),   # 5
        (rx1, -prof_riel, rz_tt),   # 6
        (rx1, -prof_riel, rz_tb),   # 7
    ])
    faces.append([vR,   vR+3, vR+2, vR+1])   # tapa izquierda (−X)
    faces.append([vR+4, vR+5, vR+6, vR+7])   # tapa derecha   (+X)
    faces.append([vR,   vR+4, vR+5, vR+1])   # cara interior  (+Y, solapada en pared)
    faces.append([vR+3, vR+2, vR+6, vR+7])   # cara frontal   (−Y)
    faces.append([vR+1, vR+5, vR+6, vR+2])   # cara superior  (+Z)
    faces.append([vR,   vR+3, vR+7, vR+4])   # cara inferior  (−Z)

    # ── Construir mesh ────────────────────────────────────────────────────────
    mesh.from_pydata(vertices, [], faces)
    mesh.validate()
    mesh.update()

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
exs = crear_exs(
    ancho          = ANCHO,
    profundidad    = PROFUNDIDAD,
    altura         = ALTURA_EXS,
    grosor_pared   = GROSOR_PARED,
    alto_aleta     = ALTO_ALETA,
    grosor_aleta   = GROSOR_ALETA,
    tolerancia     = TOLERANCIA,
    frac_solape    = FRAC_SOLAPE,
    radio_esq      = RADIO_ESQ,
    n_seg_esq      = N_SEG_ESQ,
    ancho_placa    = ANCHO_PLACA,
    alto_base_riel = ALTO_BASE_RIEL,
    prof_riel      = PROF_RIEL,
)

print(f"✓ ExS creado correctamente")
print(f"  Cuerpo:  {ANCHO} x {PROFUNDIDAD} x {ALTURA_EXS} mm  (exterior redondeado r={RADIO_ESQ})")
print(f"  Aletas:  grosor={GROSOR_ALETA} mm | alto={ALTO_ALETA} mm | tolerancia={TOLERANCIA} mm")
print(f"  Solape:  {FRAC_SOLAPE*100:.0f}% ({ALTO_ALETA*FRAC_SOLAPE:.1f} mm) embebido en ExS | {ALTO_ALETA*(1-FRAC_SOLAPE):.1f} mm libre")
print(f"  Esquinas aleta interior: r={RADIO_ESQ} mm  (= CP exterior → encaje exacto)")
print(f"  Riel: ancho={ANCHO_PLACA:.1f} mm | base={ALTO_BASE_RIEL} mm | prof={PROF_RIEL} mm")
