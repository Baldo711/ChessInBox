# ChessInBox

Scripts de Blender (Python) para modelar objetos 3D destinados a impresión 3D.

## Descripción

Generación procedural de cajas con divisiones internas configurables, pensadas para alojar piezas de ajedrez u otros objetos. Los modelos resultantes se exportan para ser laminados con un slicer de impresora 3D.

## Scripts

| Archivo | Descripción |
|---|---|
| `chess_box.py` | Genera una caja con paredes externas gruesas, sin techo, y divisiones internas en X, Y y Z. |

## Uso

1. Abre Blender.
2. Ve al **Script Editor** (Scripting workspace).
3. Abre el archivo `.py` deseado.
4. Ajusta los parámetros al inicio del archivo (dimensiones, divisiones, grosores).
5. Pulsa **Run Script**.
6. Exporta el objeto como `.stl` o `.3mf` para el slicer.

## Parámetros principales (`chess_box.py`)

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `ANCHO` | 155 mm | Ancho de la caja |
| `PROFUNDIDAD` | 155 mm | Profundidad de la caja |
| `ALTURA` | 45 mm | Altura de la caja |
| `DIVISIONES_X` | 3 | Número de divisiones en el eje X |
| `DIVISIONES_Y` | 3 | Número de divisiones en el eje Y |
| `DIVISIONES_Z` | 0 | Número de divisiones en el eje Z |
| `GROSOR_PARED_INT` | 2 mm | Grosor de las paredes internas |
| `GROSOR_PARED_EXT` | 3 mm | Grosor de las paredes externas |

## Requisitos

- [Blender](https://www.blender.org/) 3.x o superior
