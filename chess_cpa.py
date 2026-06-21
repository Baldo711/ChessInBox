import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — los marcados (*) deben coincidir con chess_box.py y chess_exs.py
# ══════════════════════════════════════════════════════════════════════════════
ANCHO            = 155    # (*) mm
PROFUNDIDAD      = 155    # (*) mm
ALTURA           = 45     # altura del cuerpo CPa (= ALTURA de la CP normal)
ALTURA_MAX       = 55     # (KEY) distancia desde la base de CPa hasta donde apoya
                          # la base de la siguiente CP al apilarla

ALTO_ALETA_EMB   = 3.5    # mm de aleta embebida dentro del cuerpo  (overlap estructural)
#  → aleta libre  = ALTURA_MAX - ALTURA  (ej: 55 - 45 = 10 mm)
#  → aleta emb    = ALTO_ALETA_EMB        (ej: 3.5 mm)
#  → aleta total  = libre + emb           (ej: 13.5 mm)
#  → z inicio aleta = ALTURA - ALTO_ALETA_EMB

ALTURA_DIVISIONES = ALTURA * 0.7   # altura max divisiones internas (≤ ALTURA)
DIVISIONES_X     = 3
DIVISIONES_Y     = 3
DIVISIONES_Z     = 0
GROSOR_BASE      = 3     # grosor del suelo (eje Z), independiente de las paredes
GROSOR_PARED_INT = 2
GROSOR_PARED_EXT = 3     # (*)
GROSOR_ALETA     = 2     # (*)
TOLERANCIA       = 0.2   # holgura aleta–CP en zona libre (*)
RADIO_ESQ        = 3     # (*)
N_SEG_ESQ        = 4     # (*)


def crear_cpa(ancho, profundidad, altura, altura_max, alto_aleta_emb,
              div_x, div_y, div_z,
              grosor_int, grosor_ext, grosor_base, altura_div,
              grosor_aleta, tolerancia,
              radio_esq, n_seg_esq):
    """
    CPa – CP Apilable.

    Igual que CP en su cuerpo (z=0 a z=ALTURA), pero con una aleta superior
    integrada que permite apilar otra CP directamente encima sin el ExS.

    ALTURA_MAX define dónde apoya la base de la siguiente CP:
      ┌─────────────────────── z = ALTURA_MAX  ← base de la CP superior
      │  zona libre (–tol)      aleta libre
      ├─────────────────────── z = ALTURA      ← techo del cuerpo CPa
      │  zona embebida (ge)     aleta embebida  ← fusionada con la pared
      ├─────────────────────── z = ALTURA - ALTO_ALETA_EMB
      │  cuerpo CPa normal
      ├─────────────────────── z = GROSOR_BASE
      │  suelo
      └─────────────────────── z = 0

    Geometría integrada — un único sólido manifold sin costuras ni shells separadas.
    """

    ge  = grosor_ext
    gb  = grosor_base
    ga  = grosor_aleta
    tol = tolerancia
    a   = ancho
    p   = profundidad
    h   = altura
    hm  = max(h + 1.0, altura_max)                       # ALTURA_MAX ≥ ALTURA+1
    hae = max(0.5, min(alto_aleta_emb, h - gb - 0.5))    # emb clamped
    hd  = max(gb, min(altura_div, h))
    r   = max(0.5, min(radio_esq, ge))
    n   = max(2, n_seg_esq)
    N   = 4 * n
    AO  = ga + tol    # cuánto sobresale la aleta del cuerpo (= 2.2 mm)

    # Z levels
    z_ua_bot = h - hae   # inicio zona embebida  (ej: 45 - 3.5 = 41.5 mm)
    z_ua_mid = h         # ALTURA — límite cuerpo / aleta libre
    z_ua_top = hm        # ALTURA_MAX — techo aleta = base siguiente CP

    # ── XY profiles ──────────────────────────────────────────────────────────
    def rrp(x0, y0, x1, y1):
        """Rounded rect poly, 4*n puntos CCW."""
        pts = []
        for cx, cy, a0, a1 in [
            (x0+r, y0+r, math.pi,     3*math.pi/2),
            (x1-r, y0+r, 3*math.pi/2, 2*math.pi  ),
            (x1-r, y1-r, 0,           math.pi/2  ),
            (x0+r, y1-r, math.pi/2,   math.pi    ),
        ]:
            for i in range(n):
                ang = a0 + (a1 - a0) * i / n
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    body_xy    = rrp(0,    0,    a,     p    )   # cuerpo exterior
    aleta_o_xy = rrp(-AO,  -AO,  a+AO,  p+AO )   # aleta exterior (más ancha)
    aleta_f_xy = rrp(-tol, -tol, a+tol, p+tol)   # aleta interior zona libre
    inner_4    = [(ge, ge), (a-ge, ge), (a-ge, p-ge), (ge, p-ge)]

    # ── Mesh / Objeto ─────────────────────────────────────────────────────────
    mat = bpy.data.materials.new(name="Material_CPa")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.7, 0.85, 0.95, 1.0)

    mesh = bpy.data.meshes.new("CPa")
    obj  = bpy.data.objects.new("CPa", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vertices = []
    faces    = []

    def add_ring(xy_pts, z):
        base = len(vertices)
        for x, y in xy_pts:
            vertices.append((x, y, z))
        return base

    def annular_N4(outer_base, inner_base, sign):
        """N-punto outer → 4-punto inner, cara horizontal. sign: +1=+Z, -1=-Z."""
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
    # CUERPO CPa  (z=0 → z=z_ua_bot)
    # Las paredes externas suben hasta z_ua_bot; el resto lo provee la aleta.
    # ══════════════════════════════════════════════════════════════════════════
    vA = add_ring(body_xy, 0       )   # exterior z=0       (N)
    vB = add_ring(body_xy, gb      )   # exterior z=gb      (N)
    vC = add_ring(inner_4, gb      )   # interior z=gb      (4)
    vD = add_ring(body_xy, z_ua_bot)   # exterior z=z_ua_bot (N)  ← techo del cuerpo
    vE = add_ring(inner_4, z_ua_bot)   # interior z=z_ua_bot (4)  ← techo int cuerpo

    # Tapa inferior (ring A, normal -Z)
    faces.append(list(range(vA + N - 1, vA - 1, -1)))

    # Paredes exteriores A → B
    for i in range(N):
        j = (i + 1) % N
        faces.append([vA+i, vA+j, vB+j, vB+i])

    # Suelo annular B → C (normal +Z)
    annular_N4(vB, vC, sign=+1)

    # Centro del suelo (ring C, normal +Z)
    faces.append([vC, vC+1, vC+2, vC+3])

    # Paredes exteriores B → D
    for i in range(N):
        j = (i + 1) % N
        faces.append([vB+i, vB+j, vD+j, vD+i])

    # Paredes interiores C → E (normal hacia el interior)
    for i in range(4):
        j = (i + 1) % 4
        faces.append([vC+i, vE+i, vE+j, vC+j])

    # ══════════════════════════════════════════════════════════════════════════
    # ALETA SUPERIOR INTEGRADA  (z_ua_bot → z_ua_top)
    #
    #  Zona embebida (z_ua_bot → z_ua_mid):
    #    exterior: aleta_o_xy (x = -AO)  |  interior: inner_4 (x = ge)
    #    → fusionada con la pared del cuerpo, sin costuras
    #
    #  Zona libre (z_ua_mid → z_ua_top):
    #    exterior: aleta_o_xy (x = -AO)  |  interior: aleta_f_xy (x = -tol)
    #    → la CP superior encaja aquí con holgura de TOLERANCIA mm
    # ══════════════════════════════════════════════════════════════════════════
    ua_o_bot = add_ring(aleta_o_xy, z_ua_bot)   # aleta outer  en z_ua_bot  (N)
    ua_o_mid = add_ring(aleta_o_xy, z_ua_mid)   # aleta outer  en z_ua_mid  (N)
    ua_f_mid = add_ring(aleta_f_xy, z_ua_mid)   # aleta free   en z_ua_mid  (N)
    ua_e_mid = add_ring(inner_4,    z_ua_mid)   # inner emb    en z_ua_mid  (4)
    ua_o_top = add_ring(aleta_o_xy, z_ua_top)   # aleta outer  en z_ua_top  (N)
    ua_f_top = add_ring(aleta_f_xy, z_ua_top)   # aleta free   en z_ua_top  (N)

    # Hombro en z_ua_bot: cuerpo exterior (vD, x=0) → aleta exterior (ua_o_bot, x=-AO)
    # Cara horizontal, normal -Z (mira hacia abajo / al exterior inferior)
    for i in range(N):
        j = (i + 1) % N
        faces.append([vD+j, vD+i, ua_o_bot+i, ua_o_bot+j])

    # Paredes int embebidas vE → ua_e_mid  (z_ua_bot → z_ua_mid, interior en ge)
    for i in range(4):
        j = (i + 1) % 4
        faces.append([vE+i, ua_e_mid+i, ua_e_mid+j, vE+j])

    # Paredes exteriores aleta  z_ua_bot → z_ua_mid  (zona embebida)
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_bot+i, ua_o_bot+j, ua_o_mid+j, ua_o_mid+i])

    # Paredes exteriores aleta  z_ua_mid → z_ua_top  (zona libre)
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_mid+i, ua_o_mid+j, ua_o_top+j, ua_o_top+i])

    # Escalón en z_ua_mid: outer (x=-AO) → free inner (x=-tol), normal +Z
    # Cierra el techo de la zona embebida y el suelo de la zona libre.
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_mid+i, ua_f_mid+i, ua_f_mid+j, ua_o_mid+j])

    # Transición en z_ua_mid: free (x=-tol) → emb inner (x=ge), normal +Z
    # Escalón interior que cierra el hueco entre -tol y ge.
    annular_N4(ua_f_mid, ua_e_mid, sign=+1)

    # Paredes interiores zona libre  ua_f_mid → ua_f_top  (x=-tol)
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_f_mid+i, ua_f_top+i, ua_f_top+j, ua_f_mid+j])

    # Tapa superior en z_ua_top (ALTURA_MAX): outer → free inner, normal +Z
    for i in range(N):
        j = (i + 1) % N
        faces.append([ua_o_top+i, ua_f_top+i, ua_f_top+j, ua_o_top+j])

    # ══════════════════════════════════════════════════════════════════════════
    # DIVISIONES INTERNAS
    # ══════════════════════════════════════════════════════════════════════════
    def add_box(x0, y0, z0, x1, y1, z1):
        s = len(vertices)
        vertices.extend([
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ])
        faces.append([s,   s+3, s+2, s+1])
        faces.append([s+4, s+5, s+6, s+7])
        faces.append([s,   s+1, s+5, s+4])
        faces.append([s+2, s+3, s+7, s+6])
        faces.append([s,   s+4, s+7, s+3])
        faces.append([s+1, s+2, s+6, s+5])

    paso_x = a / (div_x + 1)
    for i in range(1, div_x + 1):
        x = paso_x * i
        add_box(x - grosor_int/2, ge, gb, x + grosor_int/2, p-ge, hd)

    paso_y = p / (div_y + 1)
    for i in range(1, div_y + 1):
        y = paso_y * i
        add_box(ge, y - grosor_int/2, gb, a-ge, y + grosor_int/2, hd)

    if div_z > 0:
        paso_z = hd / (div_z + 1)
        for i in range(1, div_z + 1):
            z = paso_z * i
            add_box(ge, ge, z - grosor_int/2, a-ge, p-ge, z + grosor_int/2)

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
cpa = crear_cpa(
    ancho          = ANCHO,
    profundidad    = PROFUNDIDAD,
    altura         = ALTURA,
    altura_max     = ALTURA_MAX,
    alto_aleta_emb = ALTO_ALETA_EMB,
    div_x          = DIVISIONES_X,
    div_y          = DIVISIONES_Y,
    div_z          = DIVISIONES_Z,
    grosor_int     = GROSOR_PARED_INT,
    grosor_ext     = GROSOR_PARED_EXT,
    grosor_base    = GROSOR_BASE,
    altura_div     = ALTURA_DIVISIONES,
    grosor_aleta   = GROSOR_ALETA,
    tolerancia     = TOLERANCIA,
    radio_esq      = RADIO_ESQ,
    n_seg_esq      = N_SEG_ESQ,
)

print(f"✓ CPa creada correctamente")
print(f"  Cuerpo:          {ANCHO} x {PROFUNDIDAD} x {ALTURA} mm")
print(f"  Altura apilado:  {ALTURA_MAX} mm")
print(f"  Aleta libre:     {ALTURA_MAX - ALTURA:.1f} mm  (z={ALTURA} → {ALTURA_MAX})")
print(f"  Aleta embebida:  {ALTO_ALETA_EMB} mm           (z={ALTURA - ALTO_ALETA_EMB:.1f} → {ALTURA})")
print(f"  Divisiones hasta {ALTURA_DIVISIONES:.1f} mm  |  base {GROSOR_BASE} mm")
print(f"  Divisiones: {DIVISIONES_X}x{DIVISIONES_Y} (+ {DIVISIONES_Z} horizontales)")
