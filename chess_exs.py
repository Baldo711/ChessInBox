import bpy

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS — deben coincidir con chess_box.py para compatibilidad de apilado
# ══════════════════════════════════════════════════════════════════════════════
ANCHO        = 155   # igual que CP.ANCHO
PROFUNDIDAD  = 155   # igual que CP.PROFUNDIDAD
GROSOR_PARED = 3     # igual que CP.GROSOR_PARED_EXT

# Parámetros propios del ExS
ALTURA_EXS   = 20    # altura del cuerpo del extensor (espacio añadido al apilado)
ALTO_ALETA   = 10    # alto de la aleta (cuánto encaja en la CP)
GROSOR_ALETA = 2     # grosor de la aleta (perpendicular a la pared)
TOLERANCIA   = 0.2   # holgura entre la cara interior de la aleta y la CP (mm)
                     # ponlo a 0.0 para ajuste exacto en CAD


def crear_exs(ancho, profundidad, altura, grosor_pared,
              alto_aleta, grosor_aleta, tolerancia):
    """
    ExS – Extensor de Soporte.

    Marco rectangular watertight (sin techo ni suelo) que se apila entre dos CP.
    Las aletas forman un ANILLO RECTANGULAR CONTINUO (incluidas esquinas) en el
    borde inferior y superior, actuando como guías de encaje para la CP de abajo
    y la CP de arriba respectivamente.

    Sección transversal del anillo de aleta (vista desde arriba):

        ┌──────────────────────────────────────────┐  ← aleta outer
        │  ┌────────────────────────────────────┐  │
        │  │  (pared ExS + espacio libre CP)    │  │
        │  └────────────────────────────────────┘  │
        └──────────────────────────────────────────┘

    Los anillos de aleta se solapan ligeramente con el cuerpo del ExS en XY y Z
    para que el slicer los una en un sólido continuo.

    Disposición vertical al apilar (de abajo a arriba):
      [CP inferior]
      ────────────── ← top rim CP inferior
      aleta inferior del ExS  (cuelga ALTO_ALETA mm sobre la CP)
      cuerpo del ExS          (ALTURA_EXS mm de espacio extra)
      aleta superior del ExS  (ALTO_ALETA mm que recibe la CP superior)
      [CP superior]
    """

    ge  = grosor_pared
    a   = ancho
    p   = profundidad
    h   = altura
    ga  = grosor_aleta
    tol = tolerancia
    ha  = alto_aleta

    # Solapamiento para asegurar unión sólida en el slicer:
    #   OVL_XY: la cara interior del anillo penetra esta distancia dentro
    #           de la pared del ExS (que mide 'ge' mm de grosor).
    #   OVL_Z:  el anillo de aleta se extiende esta distancia hacia dentro
    #           del cuerpo del ExS en el eje Z.
    OVL_XY = min(ge - 0.1, 1.0)   # < ge para no atravesar la pared por dentro
    OVL_Z  = 1.0

    # Límites del anillo de aleta
    # · Exterior: sobresale (ga + tol) más allá del exterior del ExS
    # · Interior: penetra OVL_XY dentro de la pared del ExS
    AO = ga + tol   # "aleta offset" → cuánto sobresale por fuera
    AI = OVL_XY     # "aleta inner"  → cuánto penetra hacia dentro

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
    #
    # 4 anillos de 4 vértices:
    #   EB – exterior inferior (z=0)   IB – interior inferior (z=0)
    #   ET – exterior superior (z=h)   IT – interior superior (z=h)
    # ══════════════════════════════════════════════════════════════════════════

    vEB = len(vertices)
    vertices.extend([(0,0,0),(a,0,0),(a,p,0),(0,p,0)])

    vIB = len(vertices)
    vertices.extend([(ge,ge,0),(a-ge,ge,0),(a-ge,p-ge,0),(ge,p-ge,0)])

    vET = len(vertices)
    vertices.extend([(0,0,h),(a,0,h),(a,p,h),(0,p,h)])

    vIT = len(vertices)
    vertices.extend([(ge,ge,h),(a-ge,ge,h),(a-ge,p-ge,h),(ge,p-ge,h)])

    # Borde inferior
    faces.append([vEB,   vEB+1, vIB+1, vIB  ])
    faces.append([vEB+1, vEB+2, vIB+2, vIB+1])
    faces.append([vEB+2, vEB+3, vIB+3, vIB+2])
    faces.append([vEB+3, vEB,   vIB,   vIB+3])

    # Borde superior
    faces.append([vET,   vIT,   vIT+1, vET+1])
    faces.append([vET+1, vIT+1, vIT+2, vET+2])
    faces.append([vET+2, vIT+2, vIT+3, vET+3])
    faces.append([vET+3, vIT+3, vIT,   vET  ])

    # Paredes exteriores
    faces.append([vEB,   vEB+1, vET+1, vET  ])
    faces.append([vEB+1, vEB+2, vET+2, vET+1])
    faces.append([vEB+2, vEB+3, vET+3, vET+2])
    faces.append([vEB+3, vEB,   vET,   vET+3])

    # Paredes interiores
    faces.append([vIB,   vIT,   vIT+1, vIB+1])
    faces.append([vIB+1, vIT+1, vIT+2, vIB+2])
    faces.append([vIB+2, vIT+2, vIT+3, vIB+3])
    faces.append([vIB+3, vIT+3, vIT,   vIB  ])

    # ══════════════════════════════════════════════════════════════════════════
    # ANILLOS DE ALETA
    #
    # Cada aleta es un prisma rectangular hueco (anillo) — igual que el cuerpo
    # del ExS pero más corto y con las dimensiones exteriores aumentadas en AO
    # y las interiores reducidas en AI (para penetrar en la pared del ExS).
    #
    # Se solapan con el cuerpo del ExS en OVL_Z mm en Z y OVL_XY mm en XY
    # para que el slicer los funda en un único sólido.
    # ══════════════════════════════════════════════════════════════════════════

    def add_ring(ox0, oy0, ox1, oy1, ix0, iy0, ix1, iy1, z0, z1):
        """
        Anillo rectangular (prisma hueco).
        o* = límites exteriores del anillo
        i* = límites del hueco interior
        z0, z1 = rango en Z
        """
        s = len(vertices)
        vertices.extend([
            # Exterior inferior (0–3)
            (ox0, oy0, z0), (ox1, oy0, z0), (ox1, oy1, z0), (ox0, oy1, z0),
            # Exterior superior (4–7)
            (ox0, oy0, z1), (ox1, oy0, z1), (ox1, oy1, z1), (ox0, oy1, z1),
            # Interior inferior (8–11)
            (ix0, iy0, z0), (ix1, iy0, z0), (ix1, iy1, z0), (ix0, iy1, z0),
            # Interior superior (12–15)
            (ix0, iy0, z1), (ix1, iy0, z1), (ix1, iy1, z1), (ix0, iy1, z1),
        ])
        # Fondo (z=z0): 4 trapecios formando el aro inferior
        faces.extend([
            [s+0,  s+8,  s+9,  s+1 ],
            [s+1,  s+9,  s+10, s+2 ],
            [s+2,  s+10, s+11, s+3 ],
            [s+3,  s+11, s+8,  s+0 ],
        ])
        # Techo (z=z1): 4 trapecios formando el aro superior
        faces.extend([
            [s+4,  s+5,  s+13, s+12],
            [s+5,  s+6,  s+14, s+13],
            [s+6,  s+7,  s+15, s+14],
            [s+7,  s+4,  s+12, s+15],
        ])
        # Paredes exteriores
        faces.extend([
            [s+0,  s+1,  s+5,  s+4 ],
            [s+1,  s+2,  s+6,  s+5 ],
            [s+2,  s+3,  s+7,  s+6 ],
            [s+3,  s+0,  s+4,  s+7 ],
        ])
        # Paredes interiores
        faces.extend([
            [s+8,  s+12, s+13, s+9 ],
            [s+9,  s+13, s+14, s+10],
            [s+10, s+14, s+15, s+11],
            [s+11, s+15, s+12, s+8 ],
        ])

    # ── Aleta inferior (cuelga bajo el ExS, abraza la CP de abajo) ───────────
    #    z: de -ha  hasta  OVL_Z (solapamiento con el cuerpo del ExS)
    add_ring(
        ox0=-AO,   oy0=-AO,   ox1=a+AO,  oy1=p+AO,
        ix0=AI,    iy0=AI,    ix1=a-AI,  iy1=p-AI,
        z0=-ha,    z1=OVL_Z,
    )

    # ── Aleta superior (sobresale sobre el ExS, guía la CP de arriba) ─────────
    #    z: de h-OVL_Z  hasta  h+ha
    add_ring(
        ox0=-AO,   oy0=-AO,   ox1=a+AO,  oy1=p+AO,
        ix0=AI,    iy0=AI,    ix1=a-AI,  iy1=p-AI,
        z0=h-OVL_Z, z1=h+ha,
    )

    # ── Construir mesh ────────────────────────────────────────────────────────
    mesh.from_pydata(vertices, [], faces)
    mesh.validate()
    mesh.update()

    # Recalcular normales para asegurar orientación correcta
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
)

print(f"✓ ExS creado correctamente")
print(f"  Cuerpo:  {ANCHO} x {PROFUNDIDAD} x {ALTURA_EXS} mm")
print(f"  Aletas:  grosor={GROSOR_ALETA} mm  |  alto={ALTO_ALETA} mm  |  tolerancia={TOLERANCIA} mm")
print(f"  Aleta exterior: {ANCHO + 2*(GROSOR_ALETA+TOLERANCIA):.1f} x {PROFUNDIDAD + 2*(GROSOR_ALETA+TOLERANCIA):.1f} mm")
print(f"  Altura total apilada (CP + ExS): {45 + ALTURA_EXS} mm  (asumiendo CP.ALTURA=45)")
