import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — los marcados (*) deben coincidir con chess_box.py
# ══════════════════════════════════════════════════════════════════════════════
ANCHO        = 155   # (*)
PROFUNDIDAD  = 155   # (*)
GROSOR_PARED = 3     # (*)
RADIO_ESQ    = 3     # (*)
N_SEG_ESQ    = 4     # (*)

ALTURA_EXS   = 40
ALTO_ALETA   = 10
GROSOR_ALETA = 2
TOLERANCIA   = 0.2   # holgura CP-aleta en zona libre (mm)
FRAC_SOLAPE  = 0.35  # fracción del alto de aleta embebida en el cuerpo ExS

ANCHO_PLACA    = ANCHO * 0.5
ALTO_BASE_RIEL = 8
PROF_RIEL      = 2.5


def crear_exs(ancho, profundidad, altura, grosor_pared,
              alto_aleta, grosor_aleta, tolerancia, frac_solape,
              radio_esq, n_seg_esq,
              ancho_placa, alto_base_riel, prof_riel):
    """
    ExS – Extensor de Soporte.

    Las aletas son GEOMETRÍA INTEGRADA, no objetos separados.
    El perfil de la pared exterior tiene forma de T en Z:

    Zona libre (aleta fuera del cuerpo ExS):
        Cara exterior: x = -AO   (aleta outer)
        Cara interior: x = -tol  (holgura 0.2 mm → CP cabe con justo)

    Zona embebida (aleta dentro del cuerpo ExS):
        Cara exterior: x = -AO   (sigue siendo la aleta outer)
        Cara interior: x = ge    (= pared interior del ExS → sin hueco, una sola pieza)

    Zona cuerpo (entre las dos zonas embebidas):
        Cara exterior: x = 0     (exterior normal del ExS)
        Cara interior: x = ge    (interior normal del ExS)

    Transición embebida→cuerpo: cara horizontal "hombro" (shoulder) que conecta
    la cara exterior de la aleta (x=-AO) con la del cuerpo (x=0) sin discontinuidad.
    """

    ge  = grosor_pared
    a   = ancho
    p   = profundidad
    h   = altura
    ga  = grosor_aleta
    tol = tolerancia
    ha  = alto_aleta
    fs  = max(0.0, min(1.0, frac_solape))
    r   = max(0.5, radio_esq)
    n   = max(2, n_seg_esq)
    N   = 4 * n
    AO  = ga + tol   # cuánto sobresale la aleta más allá del ExS (= 2.2 mm)

    # ── Niveles Z ─────────────────────────────────────────────────────────────
    z_la_bot = -(ha * (1 - fs))   # -6.5 mm  (base aleta inferior libre)
    z_la_mid =  0.0               #  0.0 mm  (base ExS / transición inf)
    z_la_top =  ha * fs           # +3.5 mm  (techo aleta inferior embebida)
    z_ua_bot =  h - ha * fs       # 36.5 mm  (base aleta superior embebida)
    z_ua_mid =  h                 # 40.0 mm  (techo ExS / transición sup)
    z_ua_top =  h + ha * (1 - fs) # 46.5 mm  (techo aleta superior libre)

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

    # ── Perfiles XY ───────────────────────────────────────────────────────────
    def rounded_rect_poly(x0, y0, x1, y1):
        """4*n puntos CCW para rectángulo con esquinas redondeadas (radio r)."""
        pts = []
        for cx, cy, a0, a1 in [
            (x0+r, y0+r, math.pi,     3*math.pi/2),   # BL
            (x1-r, y0+r, 3*math.pi/2, 2*math.pi  ),   # BR
            (x1-r, y1-r, 0,           math.pi/2  ),   # TR
            (x0+r, y1-r, math.pi/2,   math.pi    ),   # TL
        ]:
            for i in range(n):
                ang = a0 + (a1 - a0) * i / n
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    # N-punto rounded rects
    outer_xy   = rounded_rect_poly(-AO,  -AO,  a+AO,  p+AO )  # aleta exterior
    free_xy    = rounded_rect_poly(-tol, -tol, a+tol, p+tol)  # cara interior libre (CP clearance)
    exs_out_xy = rounded_rect_poly(0,    0,    a,     p    )  # exterior del cuerpo ExS
    # 4-punto rect (interior ExS)
    exs_in_4   = [(ge, ge), (a-ge, ge), (a-ge, p-ge), (ge, p-ge)]

    # ── Helper: añadir anillo de vértices ─────────────────────────────────────
    def add_ring(xy_pts, z):
        base = len(vertices)
        for x, y in xy_pts:
            vertices.append((x, y, z))
        return base

    # ── Helper: aro horizontal N-punto → 4-punto (triangulación corner-fan) ──
    def annular_N4(outer_base, inner_base, sign):
        """
        Triangula la cara horizontal entre un anillo exterior de N puntos
        (rounded rect) y un rectángulo interior de 4 puntos.
        sign=+1 → normal +Z;  sign=-1 → normal -Z.
        """
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
    # ALETA INFERIOR — geometría integrada
    # ══════════════════════════════════════════════════════════════════════════
    #
    # Anillos de vértices (de abajo a arriba):
    #
    #  z_la_bot  la_o_bot (N outer)  la_f_bot (N free)
    #  z_la_mid  la_o_mid (N outer)  la_f_mid (N free)  la_e_mid (4 exs_inner)
    #  z_la_top  la_o_top (N outer)  la_x_top (N exs_outer)  la_e_top (4 exs_inner)
    #
    la_o_bot = add_ring(outer_xy,   z_la_bot)   # N
    la_f_bot = add_ring(free_xy,    z_la_bot)   # N
    la_o_mid = add_ring(outer_xy,   z_la_mid)   # N
    la_f_mid = add_ring(free_xy,    z_la_mid)   # N
    la_e_mid = add_ring(exs_in_4,   z_la_mid)   # 4
    la_o_top = add_ring(outer_xy,   z_la_top)   # N
    la_x_top = add_ring(exs_out_xy, z_la_top)   # N  (ExS outer)
    la_e_top = add_ring(exs_in_4,   z_la_top)   # 4  (compartido con cuerpo ExS)

    # Paredes exteriores (aleta outer, z_la_bot → z_la_top)
    for i in range(N):
        j = (i + 1) % N
        faces.append([la_o_bot+i, la_o_bot+j, la_o_mid+j, la_o_mid+i])
        faces.append([la_o_mid+i, la_o_mid+j, la_o_top+j, la_o_top+i])

    # Pared interior LIBRE (z_la_bot → z_la_mid) — cara que ve al CP
    for i in range(N):
        j = (i + 1) % N
        faces.append([la_f_bot+i, la_f_mid+i, la_f_mid+j, la_f_bot+j])

    # Pared interior EMBEBIDA (z_la_mid → z_la_top) — coincide con pared interior ExS
    for i in range(4):
        j = (i + 1) % 4
        faces.append([la_e_mid+i, la_e_top+i, la_e_top+j, la_e_mid+j])

    # Tapa inferior en z_la_bot: outer(N) → free(N), normal -Z
    for i in range(N):
        j = (i + 1) % N
        faces.append([la_o_bot+j, la_o_bot+i, la_f_bot+i, la_f_bot+j])

    # Escalón en z_la_mid: outer(N,-AO) → free(N,-tol), normal -Z
    # Cierra el suelo de la zona embebida y el techo de la zona libre.
    for i in range(N):
        j = (i + 1) % N
        faces.append([la_o_mid+j, la_o_mid+i, la_f_mid+i, la_f_mid+j])

    # Cara de TRANSICIÓN en z_la_mid (z=0):
    # Conecta free(N, a -tol) con exs_inner(4, a ge) cerrando el hueco.
    # Es también el fondo del cuerpo ExS. Normal: -Z.
    annular_N4(la_f_mid, la_e_mid, sign=-1)

    # Cara HOMBRO en z_la_top (z=3.5mm):
    # Cara horizontal que conecta aleta outer(N,-AO) con exs outer(N,0). Normal: +Z.
    for i in range(N):
        j = (i + 1) % N
        faces.append([la_o_top+i, la_x_top+i, la_x_top+j, la_o_top+j])

    # ══════════════════════════════════════════════════════════════════════════
    # CUERPO ExS — entre las dos zonas embebidas
    # (sin bordes superior ni inferior — los proveen las aletas)
    # ══════════════════════════════════════════════════════════════════════════
    ex_o_top = la_x_top          # compartido con aleta inferior
    ex_e_top = la_e_top          # compartido con aleta inferior
    ex_o_bot = add_ring(exs_out_xy, z_ua_bot)   # N
    ex_e_bot = add_ring(exs_in_4,   z_ua_bot)   # 4

    # Paredes exteriores (exs outer, z_la_top → z_ua_bot)
    for i in range(N):
        j = (i + 1) % N
        faces.append([ex_o_top+i, ex_o_top+j, ex_o_bot+j, ex_o_bot+i])

    # Paredes interiores (exs inner, z_la_top → z_ua_bot)
    for i in range(4):
        j = (i + 1) % 4
        faces.append([ex_e_top+i, ex_e_bot+i, ex_e_bot+j, ex_e_top+j])

    # ══════════════════════════════════════════════════════════════════════════
    # ALETA SUPERIOR — simétrica a la inferior (espejo en Z alrededor de h/2)
    # ══════════════════════════════════════════════════════════════════════════
    ua_o_bot = add_ring(outer_xy,   z_ua_bot)   # N
    # ex_o_bot / ex_e_bot compartidos con cuerpo ExS
    ua_o_mid = add_ring(outer_xy,   z_ua_mid)   # N
    ua_f_mid = add_ring(free_xy,    z_ua_mid)   # N
    ua_e_mid = add_ring(exs_in_4,   z_ua_mid)   # 4
    ua_o_top = add_ring(outer_xy,   z_ua_top)   # N
    ua_f_top = add_ring(free_xy,    z_ua_top)   # N

    # Cara HOMBRO en z_ua_bot (z=36.5mm):
    # Conecta exs outer(N,0) con aleta outer(N,-AO). Normal: -Z.
    for i in range(N):
        j = (i + 1) % N
        faces.append([ex_o_bot+j, ex_o_bot+i, ua_o_bot+i, ua_o_bot+j])

    # Pared interior EMBEBIDA (z_ua_bot → z_ua_mid) — coincide con pared interior ExS
    for i in range(4):
        j = (i + 1) % 4
        faces.append([ex_e_bot+i, ua_e_mid+i, ua_e_mid+j, ex_e_bot+j])

    # Paredes exteriores (aleta outer, z_ua_bot → z_ua_top)
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_bot+i, ua_o_bot+j, ua_o_mid+j, ua_o_mid+i])
        faces.append([ua_o_mid+i, ua_o_mid+j, ua_o_top+j, ua_o_top+i])

    # Pared interior LIBRE (z_ua_mid → z_ua_top) — cara que ve al CP superior
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_f_mid+i, ua_f_top+i, ua_f_top+j, ua_f_mid+j])

    # Escalón en z_ua_mid: outer(N,-AO) → free(N,-tol), normal +Z
    # Cierra el techo de la zona embebida y el suelo de la zona libre.
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_mid+i, ua_f_mid+i, ua_f_mid+j, ua_o_mid+j])

    # Cara de TRANSICIÓN en z_ua_mid (z=h):
    # Conecta free(N, a -tol) con exs_inner(4, a ge). Normal: +Z.
    annular_N4(ua_f_mid, ua_e_mid, sign=+1)

    # Tapa superior en z_ua_top: outer(N) → free(N), normal +Z
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_top+i, ua_o_top+j, ua_f_top+j, ua_f_top+i])

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
        (rx0,  OVL_Y,     rz_bb),  # 0
        (rx0,  OVL_Y,     rz_bt),  # 1
        (rx0, -prof_riel, rz_tt),  # 2
        (rx0, -prof_riel, rz_tb),  # 3
        (rx1,  OVL_Y,     rz_bb),  # 4
        (rx1,  OVL_Y,     rz_bt),  # 5
        (rx1, -prof_riel, rz_tt),  # 6
        (rx1, -prof_riel, rz_tb),  # 7
    ])
    faces.append([vR,   vR+3, vR+2, vR+1])
    faces.append([vR+4, vR+5, vR+6, vR+7])
    faces.append([vR,   vR+4, vR+5, vR+1])
    faces.append([vR+3, vR+2, vR+6, vR+7])
    faces.append([vR+1, vR+5, vR+6, vR+2])
    faces.append([vR,   vR+3, vR+7, vR+4])

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

print(f"✓ ExS creado correctamente (aletas integradas, una sola pieza)")
print(f"  Cuerpo:  {ANCHO} x {PROFUNDIDAD} x {ALTURA_EXS} mm")
print(f"  Aleta inferior: z={-(ALTO_ALETA*(1-FRAC_SOLAPE)):.1f} → +{ALTO_ALETA*FRAC_SOLAPE:.1f} mm")
print(f"  Aleta superior: z={ALTURA_EXS - ALTO_ALETA*FRAC_SOLAPE:.1f} → {ALTURA_EXS + ALTO_ALETA*(1-FRAC_SOLAPE):.1f} mm")
print(f"  CP clearance (zona libre): {TOLERANCIA} mm")
print(f"  Riel: ancho={ANCHO_PLACA:.1f} mm | base={ALTO_BASE_RIEL} mm | prof={PROF_RIEL} mm")
