import bpy

# PARÁMETROS
ANCHO = 155
PROFUNDIDAD = 155
ALTURA = 45
DIVISIONES_X = 3
DIVISIONES_Y = 3
DIVISIONES_Z = 0
GROSOR_PARED_INT = 2
GROSOR_PARED_EXT = 3

def crear_caja_correcta(ancho, profundidad, altura, div_x, div_y, div_z, grosor_int, grosor_ext):
    """
    Caja sin techo con mesh watertight (cerrado) apto para impresión 3D.

    Estructura de vértices (5 anillos):
      A  – anillo exterior inferior  (z=0)
      B  – anillo exterior a nivel de suelo interior  (z=ge)
      C  – anillo interior a nivel de suelo  (z=ge)
      D  – anillo exterior superior  (z=h)
      E  – anillo interior superior  (z=h)

    Caras generadas:
      · Fondo exterior
      · Paredes exteriores (A→B y B→D, dos tramos para compartir arista con el suelo)
      · Tiras del suelo: trapezoides que conectan B con C (cierran la base de las paredes)
      · Cara central del suelo interior
      · Paredes interiores (C→E, normales hacia el interior)
      · Borde superior: trapezoides que conectan D con E (cierran el remate de las paredes)
    """

    ge = grosor_ext
    a  = ancho
    p  = profundidad
    h  = altura

    # Crear material
    mat = bpy.data.materials.new(name="Material_Caja")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs[0].default_value = (0.8, 0.8, 0.9, 1.0)

    # Crear mesh
    mesh = bpy.data.meshes.new("CajaDividida")
    obj  = bpy.data.objects.new("CajaDividida", mesh)

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vertices = []
    faces    = []

    # ── ANILLO A: exterior inferior (z=0) ─────────────────────────────────────
    vA = len(vertices)
    vertices.extend([
        (0, 0, 0),   # A0  frente-izquierda
        (a, 0, 0),   # A1  frente-derecha
        (a, p, 0),   # A2  atrás-derecha
        (0, p, 0),   # A3  atrás-izquierda
    ])

    # ── ANILLO B: exterior a nivel del suelo interior (z=ge) ──────────────────
    vB = len(vertices)
    vertices.extend([
        (0, 0, ge),  # B0
        (a, 0, ge),  # B1
        (a, p, ge),  # B2
        (0, p, ge),  # B3
    ])

    # ── ANILLO C: interior a nivel del suelo (z=ge) ───────────────────────────
    vC = len(vertices)
    vertices.extend([
        (ge,   ge,   ge),  # C0  frente-izquierda interior
        (a-ge, ge,   ge),  # C1  frente-derecha interior
        (a-ge, p-ge, ge),  # C2  atrás-derecha interior
        (ge,   p-ge, ge),  # C3  atrás-izquierda interior
    ])

    # ── ANILLO D: exterior superior (z=h) ─────────────────────────────────────
    vD = len(vertices)
    vertices.extend([
        (0, 0, h),   # D0
        (a, 0, h),   # D1
        (a, p, h),   # D2
        (0, p, h),   # D3
    ])

    # ── ANILLO E: interior superior (z=h) ─────────────────────────────────────
    vE = len(vertices)
    vertices.extend([
        (ge,   ge,   h),   # E0
        (a-ge, ge,   h),   # E1
        (a-ge, p-ge, h),   # E2
        (ge,   p-ge, h),   # E3
    ])

    # ── FONDO EXTERIOR (normal hacia -z) ──────────────────────────────────────
    faces.append([vA, vA+3, vA+2, vA+1])

    # ── PAREDES EXTERIORES INFERIORES  A→B (normal hacia fuera) ───────────────
    faces.append([vA,   vA+1, vB+1, vB  ])  # frente
    faces.append([vA+1, vA+2, vB+2, vB+1])  # derecha
    faces.append([vA+2, vA+3, vB+3, vB+2])  # atrás
    faces.append([vA+3, vA,   vB,   vB+3])  # izquierda

    # ── TIRAS DEL SUELO INTERIOR  B→C  (normal hacia +z) ─────────────────────
    # Cuatro trapezoides que conectan el anillo exterior B con el interior C,
    # cerrando el grosor de las paredes a nivel del suelo.
    faces.append([vB,   vB+1, vC+1, vC  ])  # frente
    faces.append([vB+1, vB+2, vC+2, vC+1])  # derecha
    faces.append([vB+2, vB+3, vC+3, vC+2])  # atrás
    faces.append([vB+3, vB,   vC,   vC+3])  # izquierda

    # ── CARA CENTRAL DEL SUELO INTERIOR (normal hacia +z) ─────────────────────
    faces.append([vC, vC+1, vC+2, vC+3])

    # ── PAREDES EXTERIORES SUPERIORES  B→D (normal hacia fuera) ───────────────
    faces.append([vB,   vB+1, vD+1, vD  ])  # frente
    faces.append([vB+1, vB+2, vD+2, vD+1])  # derecha
    faces.append([vB+2, vB+3, vD+3, vD+2])  # atrás
    faces.append([vB+3, vB,   vD,   vD+3])  # izquierda

    # ── PAREDES INTERIORES  C→E  (normal hacia el interior) ───────────────────
    faces.append([vC,   vC+1, vE+1, vE  ])  # frente   (normal +y)
    faces.append([vC+1, vE+1, vE+2, vC+2])  # derecha  (normal -x)
    faces.append([vC+2, vE+2, vE+3, vC+3])  # atrás    (normal -y)
    faces.append([vC+3, vE+3, vE,   vC  ])  # izquierda(normal +x)

    # ── BORDE SUPERIOR  D→E  (normal hacia +z) ────────────────────────────────
    # Cuatro trapezoides que cierran el remate superior de las paredes.
    faces.append([vD,   vD+1, vE+1, vE  ])  # frente
    faces.append([vD+1, vD+2, vE+2, vE+1])  # derecha
    faces.append([vD+2, vD+3, vE+3, vE+2])  # atrás
    faces.append([vD+3, vD,   vE,   vE+3])  # izquierda

    # ── DIVISIONES INTERNAS ───────────────────────────────────────────────────
    # Cada división es un sólido cerrado (6 caras) que va del suelo (z=ge)
    # hasta la parte superior (z=h), listo para union booleana en el slicer.

    # Divisiones en X (tabiques de lado a lado)
    paso_x = ancho / (div_x + 1)
    for i in range(1, div_x + 1):
        x = paso_x * i
        s = len(vertices)
        vertices.extend([
            (x - grosor_int/2, ge,   ge),  # s+0
            (x + grosor_int/2, ge,   ge),  # s+1
            (x + grosor_int/2, p-ge, ge),  # s+2
            (x - grosor_int/2, p-ge, ge),  # s+3
            (x - grosor_int/2, ge,   h ),  # s+4
            (x + grosor_int/2, ge,   h ),  # s+5
            (x + grosor_int/2, p-ge, h ),  # s+6
            (x - grosor_int/2, p-ge, h ),  # s+7
        ])
        faces.append([s,   s+3, s+2, s+1])  # fondo
        faces.append([s+4, s+5, s+6, s+7])  # techo
        faces.append([s,   s+1, s+5, s+4])  # frente
        faces.append([s+2, s+3, s+7, s+6])  # atrás
        faces.append([s,   s+4, s+7, s+3])  # izquierda
        faces.append([s+1, s+2, s+6, s+5])  # derecha

    # Divisiones en Y (tabiques de delante a atrás)
    paso_y = profundidad / (div_y + 1)
    for i in range(1, div_y + 1):
        y = paso_y * i
        s = len(vertices)
        vertices.extend([
            (ge,   y - grosor_int/2, ge),  # s+0
            (a-ge, y - grosor_int/2, ge),  # s+1
            (a-ge, y + grosor_int/2, ge),  # s+2
            (ge,   y + grosor_int/2, ge),  # s+3
            (ge,   y - grosor_int/2, h ),  # s+4
            (a-ge, y - grosor_int/2, h ),  # s+5
            (a-ge, y + grosor_int/2, h ),  # s+6
            (ge,   y + grosor_int/2, h ),  # s+7
        ])
        faces.append([s,   s+3, s+2, s+1])  # fondo
        faces.append([s+4, s+5, s+6, s+7])  # techo
        faces.append([s,   s+1, s+5, s+4])  # frente
        faces.append([s+2, s+3, s+7, s+6])  # atrás
        faces.append([s,   s+4, s+7, s+3])  # izquierda
        faces.append([s+1, s+2, s+6, s+5])  # derecha

    # Divisiones en Z (bandejas horizontales)
    if div_z > 0:
        paso_z = altura / (div_z + 1)
        for i in range(1, div_z + 1):
            z = paso_z * i
            s = len(vertices)
            vertices.extend([
                (ge,   ge,   z - grosor_int/2),  # s+0
                (a-ge, ge,   z - grosor_int/2),  # s+1
                (a-ge, p-ge, z - grosor_int/2),  # s+2
                (ge,   p-ge, z - grosor_int/2),  # s+3
                (ge,   ge,   z + grosor_int/2),  # s+4
                (a-ge, ge,   z + grosor_int/2),  # s+5
                (a-ge, p-ge, z + grosor_int/2),  # s+6
                (ge,   p-ge, z + grosor_int/2),  # s+7
            ])
            faces.append([s,   s+3, s+2, s+1])  # abajo
            faces.append([s+4, s+5, s+6, s+7])  # arriba
            faces.append([s,   s+1, s+5, s+4])  # frente
            faces.append([s+2, s+3, s+7, s+6])  # atrás
            faces.append([s,   s+4, s+7, s+3])  # izquierda
            faces.append([s+1, s+2, s+6, s+5])  # derecha

    # Construir mesh
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj.data.materials.append(mat)

    return obj

# Ejecutar
caja = crear_caja_correcta(ANCHO, PROFUNDIDAD, ALTURA, DIVISIONES_X, DIVISIONES_Y, DIVISIONES_Z, GROSOR_PARED_INT, GROSOR_PARED_EXT)

print(f"✓ Caja creada correctamente")
print(f"  Dimensiones: {ANCHO} x {PROFUNDIDAD} x {ALTURA}")
print(f"  Grosor paredes externas: {GROSOR_PARED_EXT}")
print(f"  Grosor divisiones internas: {GROSOR_PARED_INT}")