import bpy
import math

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — los marcados (*) deben coincidir con chess_exs.py
# ══════════════════════════════════════════════════════════════════════════════

# Referencia ExS (*)
ANCHO_EXS      = 155
ALTURA_EXS     = 40

# Dimensiones de la placa
ANCHO_PLACA    = ANCHO_EXS * 0.5   # 50 % del ExS → 77.5 mm (*)
ALTO_PLACA     = ALTURA_EXS        # rellena toda la cara frontal del ExS → 40 mm
GROSOR_PLACA   = 4                 # grosor total de la placa (mm)

# Parámetros del riel (deben coincidir con chess_exs.py) (*)
ALTO_BASE_RIEL  = 8    # alto (Z) del riel en la base (mm)
PROF_RIEL       = 2.5  # profundidad del riel (mm)
TOLERANCIA_RIEL = 0.3  # holgura para deslizamiento suave (mm)
# Ángulo de cola de milano implícito 45°


def crear_placa(ancho, alto, grosor, alto_base_riel, prof_riel, tol):
    """
    Placa etiqueta para el ExS.

    Es una lámina plana con una ranura de cola de milano en su cara posterior
    que desliza sobre el riel del ExS a lo largo del eje X.

    Coordenadas locales de la placa:
      X: 0 → ancho  (dirección de deslizamiento sobre el riel)
      Y: 0 → grosor (0 = cara posterior con ranura; grosor = cara frontal visible)
      Z: 0 → alto   (coincide con Z del ExS)

    Para colocar la placa sobre el ExS en Blender:
      · Ejecuta primero chess_exs.py para tener el ExS en escena.
      · Selecciona la placa y colócala en:
          X = (ANCHO_EXS - ANCHO_PLACA) / 2   → centrada horizontalmente
          Y = -GROSOR_PLACA                    → cara posterior en Y=0 (ExS frontal)
          Z = 0                                → alineada con la base del ExS
      · La placa deslizará hacia +X o -X para montarse sobre el riel.

    Ranura de cola de milano (sección en YZ, vista desde el lateral):

      Y=0 (cara posterior)                        Y=grosor (cara frontal)
      │                                                │
      │←──── PROF_G ────→│                            │
      │                                               │
      ╲                  │  ← ranura (ensancha 45°)   │
       ╲                 │                            │
        ╲________________│                            │
                                                      │
      Placa sólida: el grosor restante tras la ranura │

    """

    PROF_G  = prof_riel + tol    # profundidad de la ranura (con holgura)
    ALTO_BG = alto_base_riel + 2 * tol   # alto de la ranura en la boca (con holgura lat.)
    Z_C     = alto / 2

    # Boca de la ranura (en Y=0, cara posterior)
    Z_bb = Z_C - ALTO_BG / 2   # extremo inferior de la boca
    Z_bt = Z_C + ALTO_BG / 2   # extremo superior de la boca

    # Fondo de la ranura (en Y=PROF_G, ensanchada 45°)
    Z_tb = Z_bb - PROF_G       # extremo inferior del fondo (ensanche = PROF_G * tan45°)
    Z_tt = Z_bt + PROF_G       # extremo superior del fondo

    # ── Material ──────────────────────────────────────────────────────────────
    mat = bpy.data.materials.new(name="Material_Placa")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.95, 0.95, 0.95, 1.0)

    # ── Mesh / Objeto ─────────────────────────────────────────────────────────
    mesh = bpy.data.meshes.new("PlacaExS")
    obj  = bpy.data.objects.new("PlacaExS", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # ── Perfil de la sección transversal (plano YZ, 8 puntos CCW) ─────────────
    #
    # El perfil es el contorno de la placa con la ranura incluida.
    # Recorrido CCW visto desde el lateral izquierdo (desde -X):
    #
    #  Z
    #  │
    #  H ──────────────────────────────── 4 (0,H)   3 (GP,H)
    #  │  cara frontal (Y=GP)  ↑            │             │
    #  │                       │            │    sólido   │
    #  Z_bt ────────────────── │ ──── 6     │    (GP,Z_bt)│
    #  │                 ranura│       ╲    │             │
    #  Z_tt ─────────────── 5 ─┤        ╲──┘             │
    #  │                       │        fondo ranura      │
    #  Z_tb ─────────────── 7 ─┤        /──┐             │
    #  │                 ranura│       /    │             │
    #  Z_bb ────────────────── │ ──── 8     │    (GP,Z_bb)│
    #  │                       │            │             │
    #  0 ──────────────────────────────── 1 (0,0)  2 (GP,0)
    #  └───────────────────────────────────────────────── Y
    #   Y=0 (cara posterior / ranura)            Y=GP (cara frontal)
    #
    # Puntos del perfil (Y, Z):
    #   1: (0,   0)     frente-fondo
    #   2: (GP,  0)     posterior-fondo
    #   3: (GP,  Z_bb)  inicio ranura (abajo)
    #   4: (GP-PROF_G, Z_tb)   fondo ranura (abajo, ensanchado)
    #   5: (GP-PROF_G, Z_tt)   fondo ranura (arriba, ensanchado)
    #   6: (GP,  Z_bt)  fin ranura (arriba)
    #   7: (GP,  H)     posterior-techo
    #   8: (0,   H)     frente-techo

    GP  = grosor
    H   = alto
    PG  = PROF_G

    profile_yz = [
        (0,      0   ),   # 0 frente-fondo
        (GP,     0   ),   # 1 posterior-fondo
        (GP,     Z_bb),   # 2 inicio ranura (boca inferior)
        (GP - PG, Z_tb),  # 3 fondo ranura, esquina inferior
        (GP - PG, Z_tt),  # 4 fondo ranura, esquina superior
        (GP,     Z_bt),   # 5 fin ranura (boca superior)
        (GP,     H   ),   # 6 posterior-techo
        (0,      H   ),   # 7 frente-techo
    ]
    NP = len(profile_yz)   # = 8

    vertices = []
    faces    = []

    # ── Extrusión del perfil a lo largo de X ──────────────────────────────────
    # Cara izquierda (X=0), cara derecha (X=ancho).
    # Los vértices 0..NP-1 son X=0, NP..2*NP-1 son X=ancho.

    for y, z in profile_yz:  vertices.append((0,    y, z))  # cara izq.
    for y, z in profile_yz:  vertices.append((ancho, y, z))  # cara der.

    L = 0      # base izquierda
    R = NP     # base derecha

    # Tapa izquierda (X=0, normal -X): perfil en orden directo (CCW desde -X)
    faces.append(list(range(L, L + NP)))

    # Tapa derecha (X=ancho, normal +X): perfil en orden inverso (CCW desde +X)
    faces.append(list(range(R + NP - 1, R - 1, -1)))

    # Caras laterales: un quad por cada arista del perfil
    for i in range(NP):
        j = (i + 1) % NP
        # Quad conectando arista i→j en cara izq. con la misma en cara der.
        faces.append([L + i, R + i, R + j, L + j])

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

    # Posición de previsualización: centrada sobre la cara frontal del ExS
    obj.location = (
        (ANCHO_EXS - ancho) / 2,   # centrada en X
        -grosor,                    # cara posterior en Y=0 (cara frontal del ExS)
        0,                          # base al mismo nivel que el ExS
    )

    obj.data.materials.append(mat)
    return obj


# ── Ejecutar ──────────────────────────────────────────────────────────────────
placa = crear_placa(
    ancho          = ANCHO_PLACA,
    alto           = ALTO_PLACA,
    grosor         = GROSOR_PLACA,
    alto_base_riel = ALTO_BASE_RIEL,
    prof_riel      = PROF_RIEL,
    tol            = TOLERANCIA_RIEL,
)

PROF_G = PROF_RIEL + TOLERANCIA_RIEL
print(f"✓ Placa creada correctamente")
print(f"  Dimensiones: {ANCHO_PLACA:.1f} x {ALTO_PLACA} x {GROSOR_PLACA} mm")
print(f"  Ranura: boca={ALTO_BASE_RIEL + 2*TOLERANCIA_RIEL:.1f} mm  |  fondo={ALTO_BASE_RIEL + 2*TOLERANCIA_RIEL + 2*PROF_G:.1f} mm  |  prof={PROF_G:.1f} mm")
print(f"  Cara visible restante: {GROSOR_PLACA - PROF_G:.1f} mm de grosor")
print(f"  Posición previsualización: X={(ANCHO_EXS-ANCHO_PLACA)/2:.1f}, Y={-GROSOR_PLACA}, Z=0")
