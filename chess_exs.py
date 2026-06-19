import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — deben coincidir con chess_box.py para compatibilidad de apilado
# ══════════════════════════════════════════════════════════════════════════════
ANCHO        = 155   # igual que CP.ANCHO
PROFUNDIDAD  = 155   # igual que CP.PROFUNDIDAD
GROSOR_PARED = 3     # igual que CP.GROSOR_PARED_EXT

# Parámetros propios del ExS
ALTURA_EXS    = 40   # altura del cuerpo del extensor (mm)
ALTO_ALETA    = 10   # alto de la aleta (mm encajados en la CP)
GROSOR_ALETA  = 2    # grosor de la aleta (perpendicular a la pared)
TOLERANCIA    = 0.2  # holgura entre cara interior de aleta y CP (mm)
RADIO_ESQ     = 3    # radio de redondeo esquinas exteriores de la aleta (mm)
N_SEG_ESQ     = 4    # segmentos de arco por esquina

# Parámetros del riel de cola de milano (cara frontal)
ANCHO_PLACA    = ANCHO * 0.5   # ancho de la placa = 50 % del ExS → 77.5 mm
ALTO_BASE_RIEL = 8             # alto (Z) del riel en la base (mm)
PROF_RIEL      = 2.5           # profundidad (Y) del riel hacia afuera (mm)
# Ángulo dovetail implícito 45°: ensanche = PROF_RIEL * tan(45°) = PROF_RIEL


def crear_exs(ancho, profundidad, altura, grosor_pared,
              alto_aleta, grosor_aleta, tolerancia, radio_esq, n_seg_esq,
              ancho_placa, alto_base_riel, prof_riel):

    ge  = grosor_pared
    a   = ancho
    p   = profundidad
    h   = altura
    ga  = grosor_aleta
    tol = tolerancia
    ha  = alto_aleta
    r   = max(0.5, radio_esq)
    n   = max(2, n_seg_esq)

    AO    = ga + tol          # cuánto sobresale la aleta más allá del ExS
    AI    = min(ge - 0.1, 1.0)  # penetración en la pared para unión en slicer
    OVL_Z = 1.0               # solapamiento Z con el cuerpo del ExS

    # ── Material ──────────────────────────────────────────────────────────────
    mat = bpy.data.materials.new(name="Material_ExS")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.9, 0.65, 0.3, 1.0)

    # ── Mesh / Objeto ─────────────────────────────────────────────────────────
    mesh = bpy.data.meshes.new("ExtensorSoporte")
    obj  = bpy.data.objects.new("ExtensorSoporte", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vertices = []
    faces    = []

    # ══════════════════════════════════════════════════════════════════════════
    # CUERPO PRINCIPAL: marco rectangular watertight
    # ══════════════════════════════════════════════════════════════════════════

    vEB = len(vertices)
    vertices.extend([(0,0,0),(a,0,0),(a,p,0),(0,p,0)])
    vIB = len(vertices)
    vertices.extend([(ge,ge,0),(a-ge,ge,0),(a-ge,p-ge,0),(ge,p-ge,0)])
    vET = len(vertices)
    vertices.extend([(0,0,h),(a,0,h),(a,p,h),(0,p,h)])
    vIT = len(vertices)
    vertices.extend([(ge,ge,h),(a-ge,ge,h),(a-ge,p-ge,h),(ge,p-ge,h)])

    faces.append([vEB,   vEB+1, vIB+1, vIB  ])   # bordes inferiores
    faces.append([vEB+1, vEB+2, vIB+2, vIB+1])
    faces.append([vEB+2, vEB+3, vIB+3, vIB+2])
    faces.append([vEB+3, vEB,   vIB,   vIB+3])

    faces.append([vET,   vIT,   vIT+1, vET+1])   # bordes superiores
    faces.append([vET+1, vIT+1, vIT+2, vET+2])
    faces.append([vET+2, vIT+2, vIT+3, vET+3])
    faces.append([vET+3, vIT+3, vIT,   vET  ])

    faces.append([vEB,   vEB+1, vET+1, vET  ])   # paredes exteriores
    faces.append([vEB+1, vEB+2, vET+2, vET+1])
    faces.append([vEB+2, vEB+3, vET+3, vET+2])
    faces.append([vEB+3, vEB,   vET,   vET+3])

    faces.append([vIB,   vIT,   vIT+1, vIB+1])   # paredes interiores
    faces.append([vIB+1, vIT+1, vIT+2, vIB+2])
    faces.append([vIB+2, vIT+2, vIT+3, vIB+3])
    faces.append([vIB+3, vIT+3, vIT,   vIB  ])

    # ══════════════════════════════════════════════════════════════════════════
    # ANILLOS DE ALETA CON ESQUINAS REDONDEADAS
    # ══════════════════════════════════════════════════════════════════════════

    def rounded_rect_poly(x0, y0, x1, y1):
        pts = []
        for cx, cy, a0, a1 in [
            (x0+r, y0+r, math.pi,      3*math.pi/2),
            (x1-r, y0+r, 3*math.pi/2,  2*math.pi  ),
            (x1-r, y1-r, 0,            math.pi/2  ),
            (x0+r, y1-r, math.pi/2,    math.pi    ),
        ]:
            for i in range(n):
                ang = a0 + (a1 - a0) * i / n
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    def add_rounded_ring(ox0, oy0, ox1, oy1, ix0, iy0, ix1, iy1, z0, z1):
        outer_xy = rounded_rect_poly(ox0, oy0, ox1, oy1)
        N = len(outer_xy)
        inner_xy = [(ix0,iy0),(ix1,iy0),(ix1,iy1),(ix0,iy1)]

        s = len(vertices)
        for x, y in outer_xy:  vertices.append((x, y, z0))
        for x, y in outer_xy:  vertices.append((x, y, z1))
        for x, y in inner_xy:  vertices.append((x, y, z0))
        for x, y in inner_xy:  vertices.append((x, y, z1))

        ob = s;      ot = s + N
        ib = s+2*N;  it = s + 2*N + 4

        for i in range(N):
            j = (i + 1) % N
            faces.append([ob+i, ob+j, ot+j, ot+i])

        for i in range(4):
            j = (i + 1) % 4
            faces.append([ib+i, it+i, it+j, ib+j])

        for z_base, ob_r, ib_r, sign in [(z0, ob, ib, -1), (z1, ot, it, +1)]:
            for k in range(4):
                nk    = (k + 1) % 4
                arc_s = k * n
                ik    = ib_r + k
                ik_n  = ib_r + nk

                for i in range(n - 1):
                    oi  = ob_r + (arc_s + i)     % N
                    oii = ob_r + (arc_s + i + 1) % N
                    if sign < 0:
                        faces.append([ik, oii, oi])
                    else:
                        faces.append([ik, oi,  oii])

                ol = ob_r + (arc_s + n - 1) % N
                of = ob_r + (nk * n)        % N
                if sign < 0:
                    faces.append([ik, ik_n, of, ol])
                else:
                    faces.append([ik, ol,   of, ik_n])

    # Aleta inferior: z de -ha hasta OVL_Z
    add_rounded_ring(
        ox0=-AO, oy0=-AO, ox1=a+AO, oy1=p+AO,
        ix0=AI,  iy0=AI,  ix1=a-AI, iy1=p-AI,
        z0=-ha,  z1=OVL_Z,
    )

    # Aleta superior: z de h-OVL_Z hasta h+ha
    add_rounded_ring(
        ox0=-AO, oy0=-AO, ox1=a+AO, oy1=p+AO,
        ix0=AI,  iy0=AI,  ix1=a-AI, iy1=p-AI,
        z0=h-OVL_Z, z1=h+ha,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # RIEL DE COLA DE MILANO — cara frontal (Y=0, exterior)
    #
    # El riel es un prisma trapezoidal que sobresale de la cara frontal del ExS.
    # La placa (chess_plate.py) tiene la ranura negativa de este riel y desliza
    # horizontalmente sobre él a lo largo del eje X.
    #
    # Sección transversal (plano YZ):
    #
    #    Z
    #    │       OVL_Y (dentro de la pared, para unión en slicer)
    #    │  base ├─────┐
    #    │       │     │  ← base, altura ALTO_BASE_RIEL
    #    │  base └─────┘
    #    │       ╲     ╱  ← ensanche 45°
    #    │    tip ╲───╱   ← punta, altura ALTO_BASE_RIEL + 2*PROF_RIEL
    #    │──────────────── Y=0 (cara exterior ExS)
    #    │        Y=-PROF_RIEL (punta del riel, hacia afuera)
    #    └──────────────────────── Y
    #
    # ══════════════════════════════════════════════════════════════════════════

    OVL_Y = 1.0   # penetración en la pared del ExS para slicer union
    rx0   = (a - ancho_placa) / 2
    rx1   = (a + ancho_placa) / 2
    rz_c  = h / 2
    rz_bb = rz_c - alto_base_riel / 2
    rz_bt = rz_c + alto_base_riel / 2
    rz_tb = rz_bb - prof_riel         # punta ensanchada 45°
    rz_tt = rz_bt + prof_riel

    vR = len(vertices)
    # Izquierda (X=rx0)
    vertices.extend([
        (rx0,  OVL_Y,    rz_bb),   # 0 base-fondo
        (rx0,  OVL_Y,    rz_bt),   # 1 base-techo
        (rx0, -prof_riel, rz_tt),  # 2 punta-techo
        (rx0, -prof_riel, rz_tb),  # 3 punta-fondo
    ])
    # Derecha (X=rx1)
    vertices.extend([
        (rx1,  OVL_Y,    rz_bb),   # 4
        (rx1,  OVL_Y,    rz_bt),   # 5
        (rx1, -prof_riel, rz_tt),  # 6
        (rx1, -prof_riel, rz_tb),  # 7
    ])

    faces.append([vR,   vR+3, vR+2, vR+1])          # tapa izquierda  (-X)
    faces.append([vR+4, vR+5, vR+6, vR+7])          # tapa derecha    (+X)
    faces.append([vR,   vR+4, vR+5, vR+1])          # cara interior   (+Y, solapada)
    faces.append([vR+3, vR+2, vR+6, vR+7])          # cara exterior   (-Y, frontal)
    faces.append([vR+1, vR+5, vR+6, vR+2])          # cara superior   (+Z)
    faces.append([vR,   vR+3, vR+7, vR+4])          # cara inferior   (-Z)

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
    radio_esq      = RADIO_ESQ,
    n_seg_esq      = N_SEG_ESQ,
    ancho_placa    = ANCHO_PLACA,
    alto_base_riel = ALTO_BASE_RIEL,
    prof_riel      = PROF_RIEL,
)

print(f"✓ ExS creado correctamente")
print(f"  Cuerpo:  {ANCHO} x {PROFUNDIDAD} x {ALTURA_EXS} mm")
print(f"  Aletas:  grosor={GROSOR_ALETA} mm  |  alto={ALTO_ALETA} mm  |  tol={TOLERANCIA} mm")
print(f"  Esquinas: radio={RADIO_ESQ} mm  |  segmentos/esquina={N_SEG_ESQ}")
print(f"  Riel cola de milano: ancho={ANCHO_PLACA:.1f} mm  |  base={ALTO_BASE_RIEL} mm  |  prof={PROF_RIEL} mm")
print(f"  Riel centrado en Z={ALTURA_EXS/2:.1f} mm, X=[{(ANCHO-ANCHO_PLACA)/2:.1f}, {(ANCHO+ANCHO_PLACA)/2:.1f}] mm")
