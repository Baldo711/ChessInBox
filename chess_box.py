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
    """Caja con paredes externas gruesas, sin techo"""
    
    # Crear material
    mat = bpy.data.materials.new(name="Material_Caja")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs[0].default_value = (0.8, 0.8, 0.9, 1.0)
    
    # Crear mesh
    mesh = bpy.data.meshes.new("CajaDividida")
    obj = bpy.data.objects.new("CajaDividida", mesh)
    
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    vertices = []
    faces = []
    
    # PAREDES EXTERNAS - Estructura caja exterior (sin techo)
    # Esquina 0: abajo frente izquierda exterior
    v_ext_0 = len(vertices)
    vertices.extend([
        # Fondo exterior (abajo)
        (0, 0, 0),
        (ancho, 0, 0),
        (ancho, profundidad, 0),
        (0, profundidad, 0),
        # Arriba exterior (altura)
        (0, 0, altura),
        (ancho, 0, altura),
        (ancho, profundidad, altura),
        (0, profundidad, altura),
    ])
    
    # INTERIOR (espacio usable)
    v_int_0 = len(vertices)
    vertices.extend([
        # Fondo interior (abajo + grosor)
        (grosor_ext, grosor_ext, grosor_ext),
        (ancho - grosor_ext, grosor_ext, grosor_ext),
        (ancho - grosor_ext, profundidad - grosor_ext, grosor_ext),
        (grosor_ext, profundidad - grosor_ext, grosor_ext),
        # Arriba interior (altura - grosor)
        (grosor_ext, grosor_ext, altura - grosor_ext),
        (ancho - grosor_ext, grosor_ext, altura - grosor_ext),
        (ancho - grosor_ext, profundidad - grosor_ext, altura - grosor_ext),
        (grosor_ext, profundidad - grosor_ext, altura - grosor_ext),
    ])
    
    # CARAS EXTERIORES
    # Fondo exterior
    faces.append([v_ext_0, v_ext_0+3, v_ext_0+2, v_ext_0+1])
    
    # Frente exterior
    faces.append([v_ext_0, v_ext_0+1, v_ext_0+5, v_ext_0+4])
    
    # Atrás exterior
    faces.append([v_ext_0+2, v_ext_0+3, v_ext_0+7, v_ext_0+6])
    
    # Derecha exterior
    faces.append([v_ext_0+1, v_ext_0+2, v_ext_0+6, v_ext_0+5])
    
    # Izquierda exterior
    faces.append([v_ext_0+3, v_ext_0, v_ext_0+4, v_ext_0+7])
    
    # CARAS INTERIORES
    # Fondo interior (visible desde dentro)
    faces.append([v_int_0, v_int_0+1, v_int_0+2, v_int_0+3])
    
    # Frente interior
    faces.append([v_int_0, v_int_0+4, v_int_0+5, v_int_0+1])
    
    # Atrás interior
    faces.append([v_int_0+2, v_int_0+6, v_int_0+7, v_int_0+3])
    
    # Derecha interior
    faces.append([v_int_0+1, v_int_0+5, v_int_0+6, v_int_0+2])
    
    # Izquierda interior
    faces.append([v_int_0+3, v_int_0+7, v_int_0+4, v_int_0+0])
    
    # === DIVISIONES INTERNAS ===
    
    # Divisiones en X (de lado a lado)
    paso_x = ancho / (div_x + 1)
    for i in range(1, div_x + 1):
        x = paso_x * i
        v_start = len(vertices)
        vertices.extend([
            (x - grosor_int/2, grosor_ext, grosor_ext),
            (x + grosor_int/2, grosor_ext, grosor_ext),
            (x + grosor_int/2, profundidad - grosor_ext, grosor_ext),
            (x - grosor_int/2, profundidad - grosor_ext, grosor_ext),
            (x - grosor_int/2, grosor_ext, altura - grosor_ext),
            (x + grosor_int/2, grosor_ext, altura - grosor_ext),
            (x + grosor_int/2, profundidad - grosor_ext, altura - grosor_ext),
            (x - grosor_int/2, profundidad - grosor_ext, altura - grosor_ext),
        ])
        faces.append([v_start, v_start+1, v_start+2, v_start+3])
        faces.append([v_start+4, v_start+7, v_start+6, v_start+5])
        faces.append([v_start, v_start+1, v_start+5, v_start+4])
        faces.append([v_start+2, v_start+3, v_start+7, v_start+6])
        faces.append([v_start, v_start+3, v_start+7, v_start+4])
        faces.append([v_start+1, v_start+2, v_start+6, v_start+5])
    
    # Divisiones en Y (de adelante a atrás)
    paso_y = profundidad / (div_y + 1)
    for i in range(1, div_y + 1):
        y = paso_y * i
        v_start = len(vertices)
        vertices.extend([
            (grosor_ext, y - grosor_int/2, grosor_ext),
            (ancho - grosor_ext, y - grosor_int/2, grosor_ext),
            (ancho - grosor_ext, y + grosor_int/2, grosor_ext),
            (grosor_ext, y + grosor_int/2, grosor_ext),
            (grosor_ext, y - grosor_int/2, altura - grosor_ext),
            (ancho - grosor_ext, y - grosor_int/2, altura - grosor_ext),
            (ancho - grosor_ext, y + grosor_int/2, altura - grosor_ext),
            (grosor_ext, y + grosor_int/2, altura - grosor_ext),
        ])
        faces.append([v_start, v_start+1, v_start+2, v_start+3])
        faces.append([v_start+4, v_start+7, v_start+6, v_start+5])
        faces.append([v_start, v_start+1, v_start+5, v_start+4])
        faces.append([v_start+2, v_start+3, v_start+7, v_start+6])
        faces.append([v_start, v_start+3, v_start+7, v_start+4])
        faces.append([v_start+1, v_start+2, v_start+6, v_start+5])
    
    # Divisiones en Z
    if div_z > 0:
        paso_z = altura / (div_z + 1)
        for i in range(1, div_z + 1):
            z = paso_z * i
            v_start = len(vertices)
            vertices.extend([
                (grosor_ext, grosor_ext, z - grosor_int/2),
                (ancho - grosor_ext, grosor_ext, z - grosor_int/2),
                (ancho - grosor_ext, profundidad - grosor_ext, z - grosor_int/2),
                (grosor_ext, profundidad - grosor_ext, z - grosor_int/2),
                (grosor_ext, grosor_ext, z + grosor_int/2),
                (ancho - grosor_ext, grosor_ext, z + grosor_int/2),
                (ancho - grosor_ext, profundidad - grosor_ext, z + grosor_int/2),
                (grosor_ext, profundidad - grosor_ext, z + grosor_int/2),
            ])
            faces.append([v_start, v_start+1, v_start+2, v_start+3])
            faces.append([v_start+4, v_start+7, v_start+6, v_start+5])
            faces.append([v_start, v_start+1, v_start+5, v_start+4])
            faces.append([v_start+2, v_start+3, v_start+7, v_start+6])
            faces.append([v_start, v_start+3, v_start+7, v_start+4])
            faces.append([v_start+1, v_start+2, v_start+6, v_start+5])
    
    # Construir mesh
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    obj.data.materials.append(mat)
    
    for face in mesh.polygons:
        face.use_smooth = True
    
    return obj

# Ejecutar
caja = crear_caja_correcta(ANCHO, PROFUNDIDAD, ALTURA, DIVISIONES_X, DIVISIONES_Y, DIVISIONES_Z, GROSOR_PARED_INT, GROSOR_PARED_EXT)

print(f"✓ Caja creada correctamente")
print(f"  Dimensiones: {ANCHO} x {PROFUNDIDAD} x {ALTURA}")
print(f"  Grosor paredes externas: {GROSOR_PARED_EXT}")
print(f"  Grosor divisiones internas: {GROSOR_PARED_INT}")