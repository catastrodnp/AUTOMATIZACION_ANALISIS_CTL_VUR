import re
import pandas as pd

# Función para limpiar los campos extraídos
def limpiar_campo(texto):
    return re.sub(r'\s+[a-zA-Z]$', '', texto.strip())

# Función para procesar cada salvedad y extraer detalles
def procesar_salvedad(texto_salvedad):
    # Diccionario para almacenar los datos extraídos
    datos_salvedad = {
        'Anotación Nro': None,
        'Nro corrección': None,
        'Radicación': None,
        'Fecha': None,
        'Descripción Salvedad': None
    }

    # Extracción del número de anotación
    match = re.search(r'Anotación Nro:\s*(\d+)', texto_salvedad)
    if match:
        datos_salvedad['Anotación Nro'] = match.group(1)

    # Extracción del número de corrección
    match = re.search(r'Nro corrección:\s*(\d+)', texto_salvedad)
    if match:
        datos_salvedad['Nro corrección'] = match.group(1)

    # Extracción de la radicación
    match = re.search(r'Radicación:\s*([\w\-]+)', texto_salvedad)
    if match:
        datos_salvedad['Radicación'] = limpiar_campo(match.group(1))

    # Extracción de la fecha
    match = re.search(r'Fecha:\s*(\d{2}-\d{2}-\d{4})', texto_salvedad)
    if match:
        datos_salvedad['Fecha'] = match.group(1)

    # Extracción de la descripción de la salvedad (texto después de la fecha)
    match = re.search(r'Fecha:\s*\d{2}-\d{2}-\d{4}\s*(.*?)(?=Anotación Nro:|Trámites en curso|$)', texto_salvedad, re.DOTALL)
    if match:
        datos_salvedad['Descripción Salvedad'] = match.group(1).strip()

    return datos_salvedad

# Función para procesar las salvedades de un bloque de texto
def procesar_todas_las_salvedades(texto):
    # Lista para almacenar todas las salvedades encontradas
    salvedades = []

    # Expresión regular para separar cada salvedad completa basada en "Anotación Nro"
    bloques_salvedades = re.split(r'(Anotación Nro:\s*\d+)', texto)

    # Reconstruir los bloques separados por "Anotación Nro"
    for i in range(1, len(bloques_salvedades), 2):
        anotacion_header = bloques_salvedades[i]
        anotacion_body = bloques_salvedades[i + 1]
        texto_completo_salvedad = anotacion_header + anotacion_body
        salvedades.append(procesar_salvedad(texto_completo_salvedad))

    return salvedades

# Función para procesar la columna 'Salvedades' en el DataFrame
def procesar_salvedades(df):
    # Lista para guardar todas las filas de salvedades
    filas_salvedades = []

    # Procesar cada fila en el DataFrame original
    for idx, fila in df.iterrows():
        numero_matricula = fila['Nro Matrícula']
        nombre_archivo_pdf = fila['Archivo PDF']  # Obtener el nombre del archivo PDF
        salvedades = fila['Salvedades']
        if salvedades:
            for salvedad in salvedades:
                todas_las_salvedades = procesar_todas_las_salvedades(salvedad)
                for datos_salvedad in todas_las_salvedades:
                    # Incluir el número de matrícula y nombre del archivo para referencia
                    datos_salvedad['Nro Matrícula'] = numero_matricula
                    datos_salvedad['Archivo PDF'] = nombre_archivo_pdf
                    # Añadir a la lista de filas de salvedades
                    filas_salvedades.append(datos_salvedad)

    # Crear un nuevo DataFrame para todas las filas de salvedades
    salvedades_df = pd.DataFrame(filas_salvedades)
    return salvedades_df