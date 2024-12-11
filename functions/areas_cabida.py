import pandas as pd
import re
import numpy as np

# 1A. EXTRAER ÁREA DE CABIDAD Y LINDEROS
# Función para extraer áreas de un texto
def extract_areas(text):
    if not isinstance(text, str):
        return None
    #area_pattern = re.compile(r'\b\d{1,3}(?:[.,]?\d{3})*(?:[.,]\d+)?\s*(?:M2|M.2|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MTS CUADRADOS|M\s?2|M\.2)\b', re.IGNORECASE)
    area_pattern = re.compile(r'\b\d{1,3}(?:[.,]?\d{3})*(?:[.,]\d{2})?\s*(?:M2|M.2|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MTS CUADRADOS|M\s?2|M\.2)\b', re.IGNORECASE)
    matches = area_pattern.findall(text)  # Encontrar todas las coincidencias
    return matches if matches else None

# 1B. FORMATEAR ÁREAS
# Función para formatear el área
def format_area(area_text):
    if not area_text or not isinstance(area_text, str):
        return None
    # Quitar unidad del texto del área
    numeric_area = re.sub(r'\s*(M2|M.2|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MS.2|MTS CUADRADOS|M\s?2|M\.2)$', '', area_text, flags=re.IGNORECASE)
    # Reemplazar el último punto con una coma si tiene dos dígitos después
    if re.match(r'.*\.\d{2}$', numeric_area):
        numeric_area = numeric_area[::-1].replace('.', ',', 1)[::-1]
    return numeric_area

# Función para limpiar y convertir el área a número
def clean_and_convert_area(formatted_area):
    if not formatted_area:
        return None
    # Remover puntos y reemplazar , por .
    numeric_area = formatted_area.replace('.', '').replace(',', '.')
    # Remover espacios que hayan quedado
    numeric_area = numeric_area.replace(' ', '')
    # Convertir a float
    try:
        numeric_value = float(numeric_area)
    except ValueError:
        numeric_value = None
    return numeric_value

# Función para convertir strings formateados a números con decimales (áreas más complicadas como 23,457,99)
def convert_to_numeric(value):
    if not value or value.lower() == 'none':
        return np.nan
    # Verificar si después de la última coma hay dos dígitos
    parts = value.split(',')
    if len(parts) > 1 and len(parts[-1]) == 2:
        # Reemplazar la última coma por un punto
        value = value[:value.rfind(',')] + '.' + value[value.rfind(',') + 1:]
    # Eliminar las comas restantes
    value = value.replace(',', '')
    try:
        return float(value)
    except ValueError:
        return np.nan

# Proceso completo para el DataFrame df1['Cabidad y Linderos']
def process_areas(df_column):
    # Crear una nueva columna para guardar las áreas extraídas y formateadas
    df_areas = df_column.apply(lambda x: extract_areas(x))

    # Aplicar el formateo y la limpieza de las áreas
    df_areas_formatted = df_areas.apply(lambda areas: [clean_and_convert_area(format_area(area)) for area in areas] if areas else None)

    # Convertir áreas complejas a valores numéricos
    df_areas_numeric = df_areas_formatted.apply(lambda areas: [convert_to_numeric(str(area)) for area in areas] if areas else None)

    return df_areas_numeric
