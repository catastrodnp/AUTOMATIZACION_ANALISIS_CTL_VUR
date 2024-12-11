import pandas as pd
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine

# Función para limpiar los campos extraídos
def limpiar_campo(texto):
    """
    Limpia el texto extraído eliminando letras individuales al final y espacios en blanco.
    """
    return re.sub(r'\s+[a-zA-Z]$', '', texto.strip())

# Función para extraer el coeficiente del texto
def extract_coeficiente(text):
    if not isinstance(text, str):
        return None
    # Buscar el patrón que incluye números decimales seguidos por un símbolo de porcentaje
    coeficiente_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
    match = coeficiente_pattern.search(text)
    if match:
        return float(match.group(1))  # Convertir el valor a float
    # Si encuentra solo el carácter &, devolver None
    elif '&' in text:
        return None
    return None


# Función para extraer los datos de cada PDF
def extraer_datos_pdf(ruta_pdf):
    """
    Extrae y procesa la información de un archivo PDF específico.

    Args:
        ruta_pdf (str): Ruta al archivo PDF.

    Returns:
        dict: Diccionario con los campos extraídos.
    """
    # Diccionario para almacenar los datos extraídos
    datos = {
        'Fecha': None,
        'Hora': None,
        'No. Consulta': None,
        'N° Matrícula Inmobiliaría': None,
        'Referencia Catastral': None,
        'Departamento': None,
        'Referencia Catastral Anterior': None,
        'Municipio': None,
        'Cédula Catastral': None,
        'Vereda': None,
        'Nupre': None,
        'Dirección Actual del Inmueble': None,
        'Direcciones Anteriores': None,
        'Determinacion': None,
        'Destinacion economica': None,
        'Modalidad': None,
        'Fecha de Apertura del Folio': None,
        'Tipo de instrumento': None,
        'Fecha de instrumento': None,
        'Estado Folio': None,
        'Matrícula(s) Matriz': None,
        'Matrícula(s) Derivada(s)': None,
        'Tipo de Predio': None,
        'Complementaciones': None,
        'Cabidad y Linderos': None,
        'Linderos Tecnicamente Deﬁnidos': None,
        'Area de terreno Hectareas': None,
        'Area de terreno Metros': None,
        'Area de terreno Centimietros': None,
        'Area Privada Metros': None,
        'Area Privada Centimietros': None,
        'Area Construida Metros': None,
        'Area Construida Centimietros': None,
        'Coeficiente': None
    }

    texto_normal = []

    # Extraer y organizar el texto
    for pagina in extract_pages(ruta_pdf):
        elementos_texto = []
        for elemento in pagina:
            if isinstance(elemento, LTTextContainer):
                for linea_texto in elemento:
                    if isinstance(linea_texto, LTTextLine):
                        texto = linea_texto.get_text()
                        elementos_texto.append(texto.strip())
        # Combinar todo el texto en una sola cadena
        texto_normal.append(' '.join(elementos_texto))

    # Unir todo el texto de las páginas
    texto_final = ' '.join(texto_normal)

    # Eliminar URLs que comienzan con "https://"
    texto_final = re.sub(r'https:\/\/\S+', '', texto_final)
    #print(texto_final)

    # --- Extraer campos basados en patrones de texto ---

    # Función para extraer campos que pueden estar vacíos
    def extraer_campo(patron, texto, siguiente_patron=None):
        if siguiente_patron:
            match = re.search(f'{patron}(.*?)(?={siguiente_patron})', texto)
        else:
            match = re.search(f'{patron}(.*)', texto)
        if match:
            return limpiar_campo(match.group(1))
        return None

    # Extraer cada campo asegurando que se detiene en el siguiente campo

    # Fecha
    datos['Fecha'] = extraer_campo(r'Fecha:\s*', texto_final, r'Hora')

    # Hora
    datos['Hora'] = extraer_campo(r'Hora:\s*', texto_final, r'No\. Consulta')

    # No. Consulta
    datos['No. Consulta'] = extraer_campo(r'No\. Consulta:\s*', texto_final, r'N° Matrícula Inmobiliaría')

    # N° Matrícula Inmobiliaría
    datos['N° Matrícula Inmobiliaría'] = extraer_campo(r'N° Matrícula Inmobiliaría:\s*', texto_final, r'Referencia Catastral')

    # Referencia Catastral
    datos['Referencia Catastral'] = extraer_campo(r'Referencia Catastral:\s*', texto_final, r'Departamento')

    # Departamento
    datos['Departamento'] = extraer_campo(r'Departamento:\s*', texto_final, r'Referencia Catastral Anterior')

    # Referencia Catastral Anterior
    datos['Referencia Catastral Anterior'] = extraer_campo(r'Referencia Catastral Anterior:\s*', texto_final, r'Municipio')

    # Municipio
    datos['Municipio'] = extraer_campo(r'Municipio:\s*', texto_final, r'Cédula Catastral')

    # Cédula Catastral
    datos['Cédula Catastral'] = extraer_campo(r'Cédula Catastral:\s*', texto_final, r'Vereda')

    # Vereda
    datos['Vereda'] = extraer_campo(r'Vereda:\s*', texto_final, r'Nupre')

    # Nupre
    datos['Nupre'] = extraer_campo(r'Nupre:\s*', texto_final, r'Dirección Actual del Inmueble')

    # Dirección Actual del Inmueble
    datos['Dirección Actual del Inmueble'] = extraer_campo(r'Dirección Actual del Inmueble:\s*', texto_final, r'Direcciones Anteriores|Determinacion')

    # Direcciones Anteriores
    datos['Direcciones Anteriores'] = extraer_campo(r'Direcciones Anteriores:\s*', texto_final, r'Determinacion')

    # Determinacion
    datos['Determinacion'] = extraer_campo(r'Determinacion:\s*', texto_final, r'Destinacion economica')

    # Destinacion economica
    datos['Destinacion economica'] = extraer_campo(r'Destinacion economica:\s*', texto_final, r'Modalidad')

    # Modalidad
    datos['Modalidad'] = extraer_campo(r'Modalidad:\s*', texto_final, r'Fecha de Apertura del Folio')

    # Fecha de Apertura del Folio
    datos['Fecha de Apertura del Folio'] = extraer_campo(r'Fecha de Apertura del Folio:\s*', texto_final, r'Tipo de instrumento')

    # Tipo de instrumento
    datos['Tipo de instrumento'] = extraer_campo(r'Tipo de Instrumento:\s*', texto_final, r'Fecha de Instrumento')

    # Fecha de Instrumento
    datos['Fecha de instrumento'] = extraer_campo(r'Fecha de Instrumento:\s*', texto_final, r'Estado Folio')

    # Estado Folio
    datos['Estado Folio'] = extraer_campo(r'Estado Folio:\s*', texto_final, r'Matrícula\(s\) Matriz')

    # Matrícula(s) Matriz
    datos['Matrícula(s) Matriz'] = extraer_campo(r'Matrícula\(s\) Matriz:\s*', texto_final, r'Matrícula\(s\) Derivada\(s\)')

    # Matrícula(s) Derivada(s)
    datos['Matrícula(s) Derivada(s)'] = extraer_campo(r'Matrícula\(s\) Derivada\(s\):\s*', texto_final, r'Tipo de Predio')

    # Tipo de Predio
    datos['Tipo de Predio'] = extraer_campo(r'Tipo de Predio:\s*', texto_final, r'Complementaciones')

    # Complementaciones
    datos['Complementaciones'] = extraer_campo(r'Complementaciones\s*', texto_final, r'Cabidad y Linderos')

    # Cabidad y Linderos (Subtítulo en negrita)
    datos['Cabidad y Linderos'] = extraer_campo(r'Cabidad y Linderos\s*', texto_final, r'Linderos Tecnicamente Deﬁnidos')

    # Linderos Técnicamente Definidos
    datos['Linderos Tecnicamente Deﬁnidos'] = extraer_campo(r'Linderos Tecnicamente Deﬁnidos\s*', texto_final, r'Area Y Coeficiente')

    # Area de terreno Hectareas
    datos['Area de terreno Hectareas'] = extraer_campo(r'Area de terreno Hectareas:\s*', texto_final, r'Metros')

    # Area de terreno Metros
    datos['Area de terreno Metros'] = extraer_campo(r'Metros:\s*', texto_final, r'Area Centimietros')

    # Area Privada Centimietros
    datos['Area de terreno Centimietros'] = extraer_campo(r'Area Centimietros:\s*', texto_final, r'Area Privada Metros')

    # Area Privada Metros
    datos['Area Privada Metros'] = extraer_campo(r'Area Privada Metros:\s*', texto_final, r'Centimietros')

    # Area Privada Centimietros
    datos['Area Privada Centimietros'] = extraer_campo(r'Area Privada Metros:Centimietros:\s*', texto_final, r'Area Construida Metros')

    # Area Construida Metros
    datos['Area Construida Metros'] = extraer_campo(r'Area Construida Metros:\s*', texto_final, r'Centimietros')

    # Area COnstruida Centimietros
    datos['Area Construida Centimietros'] = extraer_campo(r'Area Construida Metros: Centimietros:\s*', texto_final, r'Coeficiente')

    # Coeficiente
    datos['Coeficiente'] = extract_coeficiente(extraer_campo(r'Coeficiente:\s*', texto_final))


    return datos