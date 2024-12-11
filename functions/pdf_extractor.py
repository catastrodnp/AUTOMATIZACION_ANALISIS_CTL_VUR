import pandas as pd
import re
import math
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTChar

# Función para limpiar campos extraídos
def clean_field(field_text):
    """
    Limpia el texto extraído eliminando letras individuales al final y espacios en blanco.
    """
    return re.sub(r'\s+[a-zA-Z]$', '', field_text.strip())

# Función para extraer datos de cada PDF
def extract_pdf_data(pdf_path):
    """
    Extrae y procesa la información de un archivo PDF específico.

    Args:
        pdf_path (str): Ruta al archivo PDF.

    Returns:
        dict: Diccionario con los campos extraídos.
    """
    # Diccionario para almacenar los datos extraídos
    data = {
        'Círculo Registral': None,
        'Nro Matrícula': None,
        'Referencia catastral': None,
        'Tipo Predio': None,
        'Departamento': None,
        'Municipio': None,
        'Vereda': None,
        'Dirección actual': None,
        'Estado del Folio': None,
        'Cabida y Linderos': None,
        'Fecha de apertura': None,
        'Tipo de instrumento': None,
        'Fecha del instrumento': None,
        'Número total de anotaciones': None,
        'Número total de salvedades': None,
        'Complementaciones': None,
        'Referencia catastral anterior': None,
        'Direcciones anteriores': None,
        'Trámites en curso': None,
        'Anotaciones': [],
        'Salvedades': []
    }

    # Función para calcular el ángulo de un carácter
    def get_char_angle(char):
        """
        Calcula el ángulo de un carácter basado en su matriz de transformación.

        Args:
            char (LTChar): Objeto de carácter de pdfminer.

        Returns:
            float: Ángulo en grados.
        """
        a, b, c, d, e, f = char.matrix
        angle = round(math.degrees(math.atan2(b, a)))
        return angle

    normal_text = []

    # Extracción y ordenamiento del texto sin caracteres rotados
    for page_layout in extract_pages(pdf_path):
        # Lista para almacenar elementos de texto con sus posiciones
        text_elements = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        line_text = ''
                        for text_obj in text_line:
                            if isinstance(text_obj, LTChar):
                                angle = get_char_angle(text_obj)
                                if angle == 0:
                                    line_text += text_obj.get_text()
                                else:
                                    # Omitir los caracteres rotados (ELIMINAR MARCAS DE AGUA)
                                    pass
                            else:
                                # Incluir otros objetos de texto (espacios, saltos de línea)
                                line_text += text_obj.get_text()
                        # Agregar la línea si no está vacía
                        if line_text.strip():
                            # Se usa y0 para la posición vertical y x0 para la horizontal
                            x0, y0, x1, y1 = text_line.bbox
                            text_elements.append((-y0, x0, line_text))
        # Ordenar los elementos de texto por posición vertical y luego horizontal
        text_elements.sort()
        # Agregar el texto en orden
        for y0, x0, line_text in text_elements:
            normal_text.append(line_text)

    # Unir y limpiar el texto
    texto_final = '\n'.join(normal_text).strip()

    # --- Paso 1: Eliminar todo antes de 'CONSULTA JURIDICADA VUR DE MATRICULA INMOBILIARIA' ---
    consulta_juridicada = 'CONSULTA JURIDICADA VUR DE MATRICULA INMOBILIARIA'
    index = texto_final.find(consulta_juridicada)
    if index != -1:
        # Mantener el texto después de 'CONSULTA JURIDICADA VUR DE MATRICULA INMOBILIARIA'
        texto_final = texto_final[index + len(consulta_juridicada):].strip()
    else:
        # Opcional: manejar casos donde no se encuentra la cadena
        print(f"Advertencia: '{consulta_juridicada}' no encontrado en {pdf_path}")

    # --- Paso 2: Eliminar todas las ocurrencias de 'CONSULTA JURIDICADA VUR DE MATRICULA INMOBILIARIA' ---
    texto_final = re.sub(re.escape(consulta_juridicada), '', texto_final, flags=re.IGNORECASE)

    # --- Paso 3: Eliminar los pies de página específicos ---
    # Definir los campos de pie de página a eliminar
    campos_a_eliminar = [
        r'Número de consulta:\s*\d+',
        r'Fecha consulta:\s*\d{2} de \w+ de \d{4} a las \d{2}:\d{2}:\d{2} [APM]{2}',
        #r'Nro Matrícula:\s*\d+\s*-\s*\d+',
        r'Usuario que consultó:\s*\w+',
        r'Entidad:\s*\w+',
        r'Ciudad:\s*\w+',
        r'IP:\s*[\d\.]+'
    ]

    # Eliminar los campos definidos usando re.sub
    for campo in campos_a_eliminar:
        texto_final = re.sub(campo, '', texto_final, flags=re.IGNORECASE)

    # Eliminar posibles líneas vacías resultantes de la eliminación
    texto_final = re.sub(r'\n\s*\n', '\n', texto_final)

    # --- Paso 4: Realizar las búsquedas sobre texto_final ---
    if texto_final:
        # Extracción de campos con reglas específicas

        # Círculo Registral
        match = re.search(r'Círculo Registral:\s*(.*?)\s*$', texto_final, re.MULTILINE)
        if match:
            data['Círculo Registral'] = clean_field(match.group(1))

        # Nro Matrícula (Ya eliminado en pie de página, pero se mantiene por si aparece nuevamente)
        match = re.search(r'Nro Matrícula:\s*(\d+\s*-\s*\d+)', texto_final)
        if match:
            data['Nro Matrícula'] = match.group(1).replace(' ', '')

        # Referencia catastral - solo la parte numérica
        match = re.search(r'Referencia catastral:\s*([\d-]+)', texto_final)
        if match:
            data['Referencia catastral'] = match.group(1)

        # Tipo Predio
        match = re.search(r'Tipo Predio:\s*([^\s]+)', texto_final)
        if match:
            data['Tipo Predio'] = clean_field(match.group(1))

        # Departamento
        match = re.search(r'DEPTO:\s*(\w+)', texto_final)
        if match:
            data['Departamento'] = match.group(1)

        # Municipio y Vereda
        match = re.search(r'MUNICIPIO:\s*(.*?)\s*VEREDA:\s*(.*?)\s*$', texto_final, re.MULTILINE)
        if match:
            data['Municipio'] = clean_field(match.group(1))
            data['Vereda'] = clean_field(match.group(2))

        # Dirección actual
        match = re.search(r'Dirección actual:\s*(.*?)\s*$', texto_final, re.MULTILINE)
        if match:
            data['Dirección actual'] = clean_field(match.group(1))

        # Estado del Folio
        match = re.search(r'Estado del Folio:\s*(\w+)', texto_final, re.MULTILINE)
        if match:
            data['Estado del Folio'] = clean_field(match.group(1))

        # Cabida y Linderos
        match = re.search(r'Cabida y Linderos:\s*(.*?)\s*(Complementaciones|Fecha de apertura)', texto_final, re.DOTALL)
        if match:
            data['Cabida y Linderos'] = match.group(1).strip()

        # Fecha de apertura
        match = re.search(r'Fecha de apertura:\s*(\d{2}-\d{2}-\d{4})', texto_final)
        if match:
            data['Fecha de apertura'] = match.group(1)

        # Tipo de instrumento y Fecha del instrumento
        match = re.search(r'Tipo de instrumento:\s*(\w+)\s*Fecha del instrumento:\s*(\d{2}-\d{2}-\d{4})', texto_final)
        if match:
            data['Tipo de instrumento'] = match.group(1).strip()
            data['Fecha del instrumento'] = match.group(2)

        # Número total de anotaciones
        match = re.search(r'Número total de anotaciones:\s*(\d+)', texto_final)
        if match:
            data['Número total de anotaciones'] = match.group(1)

        # Número total de salvedades
        match = re.search(r'Número total de salvedades:\s*(\d+)', texto_final)
        if match:
            data['Número total de salvedades'] = match.group(1)

        # Complementaciones
        match = re.search(r'Complementaciones:\s*(.*?)\s*(Fecha de apertura|Referencia catastral anterior)', texto_final, re.DOTALL)
        if match:
            data['Complementaciones'] = match.group(1).strip()

        # Referencia catastral anterior
        match = re.search(r'Referencia catastral anterior:\s*(\d+)', texto_final)
        if match:
            data['Referencia catastral anterior'] = match.group(1).strip()

        # Direcciones anteriores
        match = re.search(r'Direcciones anteriores:\s*(\d+)', texto_final)
        if match:
            data['Direcciones anteriores'] = match.group(1).strip()

        # Trámites en curso
        match = re.search(r'Trámites en curso:\s*(.*?)\s*(ANOTACIONES|SALVEDADES|$)', texto_final, re.DOTALL)
        if match:
            data['Trámites en curso'] = match.group(1).strip()

        # Anotaciones (funciona bien)
        annotations = re.findall(r'ANOTACION:.*?(?=ANOTACION:|SALVEDADES:|Trámites en curso|$)', texto_final, re.DOTALL | re.IGNORECASE)
        for annotation in annotations:
            data['Anotaciones'].append(annotation.strip())

        # Salvedades (captura mejorada)
        salvedades = re.findall(
            r'SALVEDADES:\s*\(Información Anterior o Corregida\)\s*([\s\S]*?)(?=SALVEDADES:\s*\(Información Anterior o Corregida\)|Trámites en curso|$)',
            texto_final,
            re.DOTALL | re.IGNORECASE
        )
        for salvedad in salvedades:
            salvedad_limpia = salvedad.strip()
            # Excluir salvedades que contengan 'Número total de salvedades' o sean solo '(Información Anterior o Corregida)'
            if salvedad_limpia and \
               "Número total de salvedades" not in salvedad_limpia and \
               salvedad_limpia.lower() != '(información anterior o corregida)':
                data['Salvedades'].append(salvedad_limpia)

    return data



def process_pdfs(pdf_list):
    """
    Procesa múltiples PDFs y devuelve un DataFrame con los resultados.

    Args:
        pdf_list (list): Lista de rutas a los archivos PDF.

    Returns:
        pd.DataFrame: DataFrame con los datos extraídos.
    """
    all_data = []
    for pdf_file in pdf_list:
        print(f"Procesando: {pdf_file}")
        pdf_data = extract_pdf_data(pdf_file)
        all_data.append(pdf_data)
    return pd.DataFrame(all_data)

