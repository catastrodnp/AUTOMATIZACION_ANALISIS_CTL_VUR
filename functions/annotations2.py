import os, glob, re
import pandas as pd
import numpy as np
from pdfminer.high_level import extract_text
import PyPDF2

#######1. EXTRAER TEXTO DE SECCIONES ESPECÍFICAS (TÍTULOS Y SUBTÍTULOS)
#Esta función extrae una sección específica de texto dentro de un documento de texto más largo.
def extract_section_from_text(text, section_title, next_section_titles):
    start_index = text.find(section_title)
    if start_index == -1:
        return None
    end_index = len(text)
    for next_title in next_section_titles:
        next_index = text.find(next_title, start_index + len(section_title))
        if next_index != -1 and next_index < end_index:
            end_index = next_index
    section_text = text[start_index + len(section_title):end_index].strip()
    section_text = re.sub(r'http\S+', '', section_text)
    section_text = re.split(r'Linderos Tecnicamente Definidos|Area Y Coeficiente|Salvedades', section_text)[0].strip()
    return section_text

#Esta función extrae múltiples secciones de un archivo PDF, utilizando los títulos de las secciones como puntos de referencia.
def extract_sections_from_pdf(pdf_path, section_titles):
    text = extract_text(pdf_path)
    sections = {}
    for i, section_title in enumerate(section_titles):
        next_section_titles = section_titles[i + 1:]
        sections[section_title] = extract_section_from_text(text, section_title, next_section_titles)
    return sections

#Esta función aplica la extracción de secciones a múltiples archivos PDF y organiza los resultados en un DataFrame de pandas.
def extract_sections_from_pdfs(pdf_paths, section_titles):
    data = []
    for pdf_path in pdf_paths:
        sections = extract_sections_from_pdf(pdf_path, section_titles)
        row = {'file': os.path.basename(pdf_path)}
        row.update(sections)
        data.append(row)
    return pd.DataFrame(data)

#######1A. EXTRAER AREA DE CABIDAD Y LINDEROS
#Extraer áreas
def extract_areas(text):
    area_pattern = re.compile(r'\b\d{1,3}(?:[.,]?\d{3})*(?:[.,]\d+)?\s*(?:M2|M.2|MTS|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MTS CUADRADOS|MS.2|M\s?2|M\.2)\b', re.IGNORECASE)
    matches = area_pattern.findall(text)  # Find all matches
    return matches if matches else None

#######1B. FORMATEAR ÁREAS
#Formatear áreas
def format_area(area_text):
    if not area_text or not isinstance(area_text, str):
        return None
    # Quitar unidad del texto del área
    numeric_area = re.sub(r'\s*(M2|M.2|MTS|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MTS CUADRADOS|MS.2|M\s?2|M\.2)$', '', area_text, flags=re.IGNORECASE)
    # Reemplazar el último punto con una coma si tiene dos dígitos después
    if re.match(r'.*\.\d{2}$', numeric_area):
        numeric_area = numeric_area[::-1].replace('.', ',', 1)[::-1]
    return numeric_area

#Limpiar y dejar las áreas como números
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

#FORMATEO FINAL DE LOS VALORES NUMÉRICOS MÁS ENREDADOS
#Formatear areas con formatos más complicados como 23,457,99
# Función para convertir strings formateados a números con decimales
def convert_to_numeric(value):
    if pd.isna(value):
        return np.nan
    # Verificar si después de la última coma hay dos dígitos
    parts = value.split(',')
    if len(parts) > 1 and len(parts[-1]) == 2:
        # Reemplazar la última coma por un punto
        value = value[:value.rfind(',')] + '.' + value[value.rfind(',') + 1:]
    # Eliminar las comas restantes
    value = value.replace(',', '')
    return float(value)


#######1C. IDENTIFICAR MATRÍCULA MATRIZ
#Obtener dato de matrícula matriz
def extraer_dato(texto):
    pattern = r'\b(\d{2,4}-\d{4,7})\b'  # Patrón para encontrar "##-####", ##-#####", ###-####", ##-#####",##-######", ###-######"
    matches = re.findall(pattern, texto)
    if matches:
        return matches[0]
    else:
        return None


#######2. ANOTACIONES ##########################

# Función para extraer anotaciones del texto
def extract_annotations(text):
    # Patrón para coincidir con las anotaciones (ANOTACION seguido de detalles hasta la siguiente anotación o el final del texto)
    annotation_pattern = re.compile(r'(ANOTACION:\s*.*?)(?=\nANOTACION:|$)', re.DOTALL)
    matches = annotation_pattern.findall(text)
    return matches

# Función para analizar una anotación individual en un diccionario
def parse_annotation(annotation_text):
    annotation = {}

    annotation['Validez'] = 'NO TIENE VALIDEZ' if 'NO TIENE VALIDEZ' in annotation_text else ''
    annotation['Nro de anotacion'] = re.search(r'ANOTACION:\s*Nro (\d+)', annotation_text).group(1) if re.search(r'ANOTACION:\s*Nro (\d+)', annotation_text) else None
    annotation['Fecha'] = re.search(r'Fecha:\s*([\d-]+)', annotation_text).group(1) if re.search(r'Fecha:\s*([\d-]+)', annotation_text) else None
    annotation['Radiación'] = re.search(r'Radicación:\s*(\d+)', annotation_text).group(1) if re.search(r'Radicación:\s*(\d+)', annotation_text) else None
    annotation['Doc'] = re.search(r'Doc:\s*(.*?)\n', annotation_text).group(1) if re.search(r'Doc:\s*(.*?)\n', annotation_text) else None
    annotation['Especificacion'] = re.search(r'ESPECIFICACION:\s*(.*?)\n', annotation_text).group(1) if re.search(r'ESPECIFICACION:\s*(.*?)\n', annotation_text) else None

    # Extracción de "Personas que intervienen en el acto"
    personas = re.findall(r'PERSONAS QUE INTERVIENEN EN EL ACTO (.*?)(?=\n\s*[A-Z]+:|$)', annotation_text, re.DOTALL)
    #annotation['Personas que intervienen en el acto'] = personas[0].strip() if personas else None

    # Extracción de datos que comienzan con "A:"
    a_section = re.search(r'A:\s*(.*?)\n', annotation_text)
    annotation['Personas que intervienen en el acto'] = a_section.group(1).strip() if a_section else None

    return annotation

# Función para extraer anotaciones de un PDF
def extract_annotations_from_pdf(pdf_path):
    text = extract_text(pdf_path)
    annotations = extract_annotations(text)
    return annotations

# Función para extraer anotaciones de múltiples PDFs
def extract_annotations_from_pdfs(pdf_paths):
    data = []
    for pdf_path in pdf_paths:
        annotations = extract_annotations_from_pdf(pdf_path)
        for annotation in annotations:
            parsed_annotation = parse_annotation(annotation)
            parsed_annotation['file'] = os.path.basename(pdf_path)
            parsed_annotation['folio'] = os.path.basename(pdf_path).replace('(2)', '').replace('.pdf', '').strip()
            data.append(parsed_annotation)
    return pd.DataFrame(data)

# Función para extraer valores monetarios de la columna 'Doc'
def extract_monetary_value(text):
    if not text:
        return None
    match = re.search(r'\$\s*([\d,.]+)', text)
    if match:
        value = match.group(1)
        value = value.replace('.', '').replace(',', '.')
        return float(value)
    return None

"""
# Función para extraer áreas
def extract_areas(text):
    area_pattern = re.compile(r'\b\d{1,3}(?:[.,]?\d{3})*(?:[.,]\d+)?\s*(?:M2|M.2|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MTS CUADRADOS|M\s?2|M\.2)\b', re.IGNORECASE)
    matches = area_pattern.findall(text)
    return matches if matches else None

# Función para formatear áreas
def format_area(area_text):
    if not area_text or not isinstance(area_text, str):
        return None
    numeric_area = re.sub(r'\s*(M2|M.2|MTS2|METROS 2|MTS 2|MTRS2|METROS CUADRADOS|MTS CUADRADOS|M\s?2|M\.2)$', '', area_text, flags=re.IGNORECASE)
    if re.match(r'.*\.\d{2}$', numeric_area):
        numeric_area = numeric_area[::-1].replace('.', ',', 1)[::-1]
    return numeric_area

def clean_and_convert_area(formatted_area):
    if not formatted_area:
        return None
    numeric_area = formatted_area.replace('.', '').replace(',', '.')
    numeric_area = numeric_area.replace(' ', '')
    try:
        numeric_value = float(numeric_area)
    except ValueError:
        numeric_value = None
    return numeric_value
"""

# Función para extraer áreas de la columna 'Especificacion'
def extract_area_from_especificacion(text):
    if not text:
        return None
    areas = extract_areas(text)
    if areas:
        formatted_area = format_area(areas[0])
        return clean_and_convert_area(formatted_area)
    return None

def extract_second_area_from_especificacion(text):
    if not text:
        return None
    areas = extract_areas(text)
    if areas and len(areas) > 1:
        formatted_area = format_area(areas[1])
        return clean_and_convert_area(formatted_area)
    return None

# Función para extraer detalles adicionales de la columna 'Doc'
def extract_doc_details(doc_text):
    detalles = {
        'Doc_Escritura': None,
        'Doc_Escritura_Fecha': None,
        'Doc_Notaria': None,
        'Doc_Notaria_ciudad': None
    }
    if not doc_text:
        return detalles
    escritura_match = re.search(r'ESCRITURA\s*(\d+)', doc_text)
    fecha_match = re.search(r'DEL\s*([\d-]+)', doc_text)
    notaria_match = re.search(r'NOTARIA\s*(\d+)', doc_text)
    ciudad_match = re.search(r'NOTARIA \d+\s*DE\s*([A-Z\s]+)', doc_text)

    if escritura_match:
        detalles['Doc_Escritura'] = escritura_match.group(1)
    if fecha_match:
        detalles['Doc_Escritura_Fecha'] = fecha_match.group(1)
    if notaria_match:
        detalles['Doc_Notaria'] = notaria_match.group(1)
    if ciudad_match:
        detalles['Doc_Notaria_ciudad'] = ciudad_match.group(1).strip()

    return detalles

# Función para extraer detalles adicionales de la columna 'Especificacion'
def extract_especificacion_details(text):
    detalles = {
        'Especificacion_cod': None,
        'Especificacion_area2': None
    }
    if not text:
        return detalles
    cod_match = re.search(r'(\d+)\s+', text)
    area2 = extract_second_area_from_especificacion(text)

    if cod_match:
        detalles['Especificacion_cod'] = cod_match.group(1)
    detalles['Especificacion_area2'] = area2

    return detalles