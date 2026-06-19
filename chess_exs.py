import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — deben coincidir con chess_box.py para compatibilidad de apilado
# ══════════════════════════════════════════════════════════════════════════════
ANCHO        = 155   # igual que CP.ANCHO
PROFUNDIDAD  = 155   # igual que CP.PROFUNDIDAD
GROSOR_PARED = 3     # igual que CP.GROSOR_PARED_EXT

# Parámetros propios del ExS
ALTURA_EXS    = 20   # altura del cuerpo del extensor (mm)
ALTO_ALETA    = 10   # alto de la aleta (mm encajados en la CP)
GROSOR_ALETA  = 2    # grosor de la aleta (perpendicular a la pared)
TOLERANCIA    = 0.2  # holgura entre la cara interior de la aleta y la CP (mm)
RADIO_ESQ     = 3    # radio de redondeo de las esquinas exteriores de la aleta (mm)
N_SEG_ESQ     = 4    # segmentos de arco por esquina (más = más suave, mín. 2)


def crear_exs(ancho, profundidad, altura, grosor_pared,
              alto_aleta, grosor_aleta, tolerancia, radio_esq, n_seg_esq):
    """
    ExS – Extensor de Soporte.

    Marco rectangular watertight (sin techo ni suelo) que se apila entre dos CP.
    Las aletas forman un anillo rectangular CONTINUO con esquinas redondeadas
    que rodea el exterior del ExS en el borde inferior y superior.

    Función de las aletas:
      Al apoyar el ExS sobre la CP inferior, las aletas inferiores rodean las
      paredes exteriores de la CP, impidiendo que se desplace lateralmente.
      Las aletas superiores hacen lo mismo con la CP colocada encima.

    Sección transversal del anillo de aleta (vista desde arriba):

        ╭──────────────────────────────────────────╮  ← aleta exterior (redondeada)
        │  ┌────────────────────────────────────┐  │
        │  │  pared del ExS + holgura para CP   │  │
        │  └────────────────────────────────────┘  │
        ╰──────────────────────────────────────────╯

    Los anillos de aleta se solapan levemente con el cuerpo del ExS en XY y Z
    para que el slicer los una en un único sólido imprimible.
    """

    ge  = grosor_pared
    a   = ancho
    p   = profundidad
    h   = altura
    ga  = grosor_aleta
    tol = tolerancia
    ha  = alto_aleta
    r   = max(0.5, radio_esq)          # radio mínimo 0.5 mm
    n   = max(2, n_seg_esq)            # mínimo 2 segmentos de arco

    # Aleta offset: cuánto sobresale la aleta más allá del exterior del ExS
    AO  = ga + tol

    # Aleta inner: penetra esta distancia en la pared del ExS para
    # garantizar unión volumétrica con el cuerpo principal en el slicer.
    AI  = min(ge - 0.1, 1.0)

    # Z-overlap: cuánto se extiende la aleta dentro del cuerpo del ExS
    OVL_Z = 1.0

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
    # CUERPO PRINCIPAL: marco rectangular watertight (sin techo ni suelo)
    # ══════════════════════════════════════════════════════════════════════════

    vEB = len(vertices)
    vertices.extend([(0,0,0),(a,0,0),(a,p,0),(0,p,0)])
    vIB = len(vertices)
    vertices.extend([(ge,ge,0),(a-ge,ge,0),(a-ge,p-ge,0),(ge,p-ge,0)])
    vET = len(vertices)
    vertices.extend([(0,0,h),(a,0,h),(a,p,h),(0,p,h)])
    vIT = len(vertices)
    vertices.extend([(ge,ge,h),(a-ge,ge,h),(a-ge,p-ge,h),(ge,p-ge,h)])

    faces.append([vEB,   vEB+1, vIB+1, vIB  ])   # borde inf
    faces.append([vEB+1, vEB+2, vIB+2, vIB+1])
    faces.append([vEB+2, vEB+3, vIB+3, vIB+2])
    faces.append([vEB+3, vEB,   vIB,   vIB+3])

    faces.append([vET,   vIT,   vIT+1, vET+1])   # borde sup
    faces.append([vET+1, vIT+1, vIT+2, vET+2])
    faces.append([vET+2, vIT+2, vIT+3, vET+3])
    faces.append([vET+3, vIT+3, vIT,   vET  ])

    faces.append([vEB,   vEB+1, vET+1, vET  ])   # paredes ext
    faces.append([vEB+1, vEB+2, vET+2, vET+1])
    faces.append([vEB+2, vEB+3, vET+3, vET+2])
    faces.append([vEB+3, vEB,   vET,   vET+3])

    faces.append([vIB,   vIT,   vIT+1, vIB+1])   # paredes int
    faces.append([vIB+1, vIT+1, vIT+2, vIB+2])
    faces.append([vIB+2, vIT+2, vIT+3, vIB+3])
    faces.append([vIB+3, vIT+3, vIT,   vIB  ])

    # ══════════════════════════════════════════════════════════════════════════
    # ANILLOS DE ALETA CON ESQUINAS REDONDEADAS
    # ══════════════════════════════════════════════════════════════════════════

    def rounded_rect_poly(x0, y0, x1, y1):
        """
        Polígono CCW para un rectángulo con esquinas redondeadas (radio r, n seg/esquina).
        Devuelve 4*n puntos (x,y). Los segmentos rectos entre arcos quedan implícitos.
        """
        pts = []
        for cx, cy, a0, a1 in [
            (x0+r, y0+r, math.pi,      3*math.pi/2),   # BL: 180° → 270°
            (x1-r, y0+r, 3*math.pi/2,  2*math.pi   ),   # BR: 270° → 360°
            (x1-r, y1-r, 0,            math.pi/2   ),   # TR:   0° →  90°
            (x0+r, y1-r, math.pi/2,    math.pi     ),   # TL:  90° → 180°
        ]:
            for i in range(n):
                a = a0 + (a1 - a0) * i / n
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts  # N = 4*n puntos

    def add_rounded_ring(ox0, oy0, ox1, oy1, ix0, iy0, ix1, iy1, z0, z1):
        """
        Anillo rectangular watertight con esquinas exteriores redondeadas.

        Outer polygon: rectángulo redondeado (4*n vértices en XY)
        Inner polygon: rectángulo con esquinas vivas (4 vértices en XY)

        Caras generadas (normales hacia afuera):
          · N paredes exteriores (a lo largo de Z)
          · 4 paredes interiores (a lo largo de Z)
          · Aro inferior (z=z0): triangulación de anillo outer→inner
          · Aro superior (z=z1): triangulación de anillo inner→outer
        """
        outer_xy = rounded_rect_poly(ox0, oy0, ox1, oy1)
        N = len(outer_xy)                                # = 4 * n
        inner_xy = [(ix0,iy0),(ix1,iy0),(ix1,iy1),(ix0,iy1)]

        s = len(vertices)
        for x, y in outer_xy:  vertices.append((x, y, z0))   # ob = s .. s+N-1
        for x, y in outer_xy:  vertices.append((x, y, z1))   # ot = s+N .. s+2N-1
        for x, y in inner_xy:  vertices.append((x, y, z0))   # ib = s+2N .. s+2N+3
        for x, y in inner_xy:  vertices.append((x, y, z1))   # it = s+2N+4 .. s+2N+7

        ob = s;      ot = s + N
        ib = s+2*N;  it = s + 2*N + 4

        # Paredes exteriores: N cuadriláteros a lo largo de Z
        for i in range(N):
            j = (i + 1) % N
            faces.append([ob+i, ob+j, ot+j, ot+i])

        # Paredes interiores: 4 cuadriláteros
        for i in range(4):
            j = (i + 1) % 4
            faces.append([ib+i, it+i, it+j, ib+j])

        # ── Aros inferior y superior ──────────────────────────────────────────
        # Triangulación del anillo: por cada esquina k del polígono exterior,
        # sus n vértices de arco corresponden a la esquina k del rectángulo interior.
        # Se generan:
        #   · n-1 triángulos en abanico desde el vértice interior k al arco exterior
        #   · 1 cuadrilátero "puente" que cierra la sección recta entre esquinas k y k+1
        #
        # normals_make_consistent al final corrige cualquier orientación incorrecta.

        for z_base, ob_r, ib_r, sign in [(z0, ob, ib, -1), (z1, ot, it, +1)]:
            for k in range(4):
                nk      = (k + 1) % 4
                arc_s   = k * n
                ik      = ib_r + k
                ik_next = ib_r + nk

                # Abanico de triángulos sobre el arco de la esquina k
                for i in range(n - 1):
                    oi  = ob_r + (arc_s + i)     % N
                    oii = ob_r + (arc_s + i + 1) % N
                    if sign < 0:
                        faces.append([ik, oii, oi])    # aro inferior: normal -z
                    else:
                        faces.append([ik, oi,  oii])   # aro superior: normal +z

                # Cuadrilátero puente hasta la siguiente esquina
                ol = ob_r + (arc_s + n - 1) % N
                of = ob_r + (nk * n)        % N
                if sign < 0:
                    faces.append([ik, ik_next, of, ol])    # normal -z
                else:
                    faces.append([ik, ol, of, ik_next])    # normal +z

    # ── Aleta inferior ────────────────────────────────────────────────────────
    # z: de -ha hasta OVL_Z (solapamiento con cuerpo ExS para unión en slicer)
    add_rounded_ring(
        ox0=-AO,  oy0=-AO,  ox1=a+AO,  oy1=p+AO,
        ix0=AI,   iy0=AI,   ix1=a-AI,  iy1=p-AI,
        z0=-ha,   z1=OVL_Z,
    )

    # ── Aleta superior ────────────────────────────────────────────────────────
    # z: de h-OVL_Z hasta h+ha
    add_rounded_ring(
        ox0=-AO,  oy0=-AO,  ox1=a+AO,  oy1=p+AO,
        ix0=AI,   iy0=AI,   ix1=a-AI,  iy1=p-AI,
        z0=h-OVL_Z, z1=h+ha,
    )

    # ── Construir mesh ────────────────────────────────────────────────────────
    mesh.from_pydata(vertices, [], faces)
    mesh.validate()
    mesh.update()

    # Recalcular normales para asegurar orientación correcta en todo el sólido
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
    ancho        = ANCHO,
    profundidad  = PROFUNDIDAD,
    altura       = ALTURA_EXS,
    grosor_pared = GROSOR_PARED,
    alto_aleta   = ALTO_ALETA,
    grosor_aleta = GROSOR_ALETA,
    tolerancia   = TOLERANCIA,
    radio_esq    = RADIO_ESQ,
    n_seg_esq    = N_SEG_ESQ,
)

print(f"✓ ExS creado correctamente")
print(f"  Cuerpo:  {ANCHO} x {PROFUNDIDAD} x {ALTURA_EXS} mm")
print(f"  Aletas:  grosor={GROSOR_ALETA} mm  |  alto={ALTO_ALETA} mm  |  tolerancia={TOLERANCIA} mm")
print(f"  Esquinas: radio={RADIO_ESQ} mm  |  segmentos/esquina={N_SEG_ESQ}")
print(f"  Exterior aleta: {ANCHO + 2*(GROSOR_ALETA+TOLERANCIA):.1f} x {PROFUNDIDAD + 2*(GROSOR_ALETA+TOLERANCIA):.1f} mm")
print(f"  Altura total apilada (CP + ExS): {45 + ALTURA_EXS} mm  (asumiendo CP.ALTURA=45)")
