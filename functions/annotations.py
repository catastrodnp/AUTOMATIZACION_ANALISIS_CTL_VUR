import pdfplumber
import re
import os
import pandas as pd

# Función para limpiar los campos extraídos
def limpiar_campo(texto):
    # Eliminar letras sueltas o caracteres no deseados al final
    return re.sub(r'\s+[a-zA-Z]$', '', texto.strip())

# Función para procesar cada anotación y extraer detalles
def procesar_anotacion(texto_anotacion):
    # Extracción de varios campos usando expresiones regulares
    datos_anotacion = {
        'Número de Anotación': None,
        'Fecha': None,
        'Radicación': None,
        'Documento': None,
        'Valor Acto': None,
        'Código Especificación': None,
        'Descripción Especificación': None,
        'De': None,
        'A': None,
        'Código (X/I)': None
    }

    # Número de Anotación
    match = re.search(r'ANOTACION:\s*Nro\s*(\d+)', texto_anotacion)
    if match:
        datos_anotacion['Número de Anotación'] = match.group(1)

    # Fecha
    match = re.search(r'Fecha:\s*(\d{2}-\d{2}-\d{4})', texto_anotacion)
    if match:
        datos_anotacion['Fecha'] = match.group(1)

    # Radicación
    match = re.search(r'Radicación:\s*(\S+)', texto_anotacion)
    if match:
        datos_anotacion['Radicación'] = limpiar_campo(match.group(1))

    # Documento
    match = re.search(r'Doc:\s*(.*?)(?=\s+Valor Acto:|\s+ESPECIFICACION:)', texto_anotacion)
    if match:
        datos_anotacion['Documento'] = match.group(1).strip()

    # Valor Acto
    match = re.search(r'VALOR ACTO:\s*\$\s*([\d,]+)', texto_anotacion)
    if match:
        datos_anotacion['Valor Acto'] = match.group(1)

    # Código y Descripción de la Especificación
    match = re.search(r'ESPECIFICACION:\s*(\d+)\s+(.*?)(?=\s+\()', texto_anotacion)
    if match:
        datos_anotacion['Código Especificación'] = match.group(1).strip()
        datos_anotacion['Descripción Especificación'] = match.group(2).strip()

    # "De" y "A" (partes involucradas) y "Código (X/I)"
    match = re.findall(r'DE:\s*(.*?)\s+A:\s*(.*?)\s+(X|I)', texto_anotacion)
    if match:
        lista_de = []
        lista_a = []
        codigos = []
        for entrada in match:
            lista_de.append(limpiar_campo(entrada[0].strip()))
            lista_a.append(limpiar_campo(entrada[1].strip()))
            codigos.append(entrada[2].strip())
        datos_anotacion['De'] = ', '.join(lista_de)
        datos_anotacion['A'] = ', '.join(lista_a)
        datos_anotacion['Código (X/I)'] = ', '.join(codigos)

    return datos_anotacion

# Función para procesar la columna 'Detalle de Anotaciones' en el DataFrame
def procesar_anotaciones(df):
    # Lista para guardar todas las filas de anotaciones
    filas_anotaciones = []

    # Procesar cada fila en el DataFrame original
    for idx, fila in df.iterrows():
        numero_matricula = fila['Nro Matrícula']
        nombre_archivo_pdf = fila['Archivo PDF']  # Obtener el nombre del archivo PDF
        anotaciones = fila['Anotaciones']
        if anotaciones:
            # Asumiendo que 'Detalle de Anotaciones' es una lista de cadenas de texto
            for anotacion in anotaciones:
                datos_anotacion = procesar_anotacion(anotacion)
                # Incluir el número de matrícula y nombre del archivo para referencia
                datos_anotacion['Nro Matrícula'] = numero_matricula
                datos_anotacion['Archivo PDF'] = nombre_archivo_pdf
                # Añadir a la lista de filas de anotaciones
                filas_anotaciones.append(datos_anotacion)

    # Crear un nuevo DataFrame para todas las filas de anotaciones
    anotaciones_df = pd.DataFrame(filas_anotaciones)
    return anotaciones_df
