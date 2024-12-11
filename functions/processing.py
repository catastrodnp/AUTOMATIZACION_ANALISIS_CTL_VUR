import streamlit as st
import pandas as pd
import re
from hermetrics.jaro_winkler import JaroWinkler
from hermetrics.jaro import Jaro
from datetime import datetime
import string
from rapidfuzz import fuzz

from functions import preprocessing, data_converter

comparator = JaroWinkler()
list_cods = pd.read_excel('utils\\codigos_trazabilidad.xlsx')
list_past_cods = pd.read_excel('utils\\codigos_past.xlsx')

# OBTENCION DE AREAS

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

def process_areas(data_area):
    # Crear una nueva columna para guardar las áreas extraídas y formateadas
    df_areas = extract_areas(data_area)

    # Aplicar el formateo y la limpieza de las áreas
    df_areas_formatted = [clean_and_convert_area(format_area(area)) for area in df_areas] if df_areas else None
    #df_areas.apply(lambda areas: [clean_and_convert_area(format_area(area)) for area in areas] if areas else None)

    # Convertir áreas complejas a valores numéricos
    df_areas_numeric = [convert_to_numeric(str(area)) for area in df_areas_formatted] if df_areas_formatted else None

    return df_areas_numeric

# Función para detectar si la dirección hace referencia a una propiedad horizontal
def es_propiedad_horizontal(direccion):
    if not isinstance(direccion, str):
        return False
    # Convertir a minúsculas para hacer la búsqueda insensible a mayúsculas/minúsculas
    direccion = direccion.lower()

    # Lista de palabras clave comunes para propiedades horizontales
    palabras_clave = ['propiedad horizontal', 'ph', 'torre', 'bloque', 'conjunto', 'edificio', 'unidad residencial', 'apartamento']

    # Buscar las palabras clave en la dirección
    for palabra in palabras_clave:
        if re.search(r'\b' + re.escape(palabra) + r'\b', direccion):
            return True  # Si se encuentra una palabra clave, es una propiedad horizontal
    return False  # Si no se encuentran las palabras clave, no es propiedad horizontal

# FUNCIONES GENERALES
def new_matricula(original, new_value):
    """Reforma la estructura de la nueva matrícula, para incluir el círculo registral.

    Args:
        original (str): Número de matrícula del predio matriz
        new_value (str): Número de matrícula sin círculo registral, predio hijo.

    Returns:
        str: Número de matrícula completo para predio hijo.
    """
    return re.findall(r"\d{3}-", original)[0] + new_value

def especification_similarity(a,b):
    """Verifica la similitud entre dos cadenas de texto, según el comparador "comparator".

    Args:
        a (str): Primer texto
        b (str): Segundo texto

    Returns:
        float: Similitud entre las cadenas a y b.
    """
    return comparator.similarity(data_converter.eliminar_tildes(a),
                                        data_converter.eliminar_tildes(b))

def similarity_cod(words, cod, df_all, n=10):
    resumen = {}
    wrd_lst = re.sub(f"[{string.punctuation}\d]|  ", "", words).lstrip().split(' ')[0:n]

    for k in range(0,n):
        resumen[k] = (df_all[df_all['codigo_especificacion']==cod][k].value_counts()/df_all[df_all['codigo_especificacion']==cod][k].count()).to_dict()

    # Obtencion para todas las k posiciones
    total_sum = 0
    sum_max = 0
    for k in range(len(wrd_lst)):
        sum_word = 0
        # Obtencion de similitudespara cada palabra en la posicion k
        for item, value in resumen[k].items():
            #print(item, value)
            sum_word += (n+1-k)*comparator.similarity(wrd_lst[k], item)*value
        
        sum_max += n+1-k
        total_sum += sum_word
    return total_sum/sum_max

def validate_code(code, especification, date_ann):
    #print('---------------------')
    #min_date = min(pd.read_excel('app\\utils\\codigos_trazabilidad.xlsx').iloc[:,1:].columns)
    
    data = None
    
    for col in list_cods.columns[1:]:
        if date_ann>col:
            data = col
            break
    
    if data:        
        lst = list_cods[list_cods['CODIGO']==int(code)][data]
    
        #print(lst)
        if lst.shape[0]>0:
            real_descr =lst.iloc[0]
            #print(code, '|', especification, '|', real_descr,'|', date_ann, '|', col)
            if not pd.isna(real_descr):
                real_descr = re.sub('[%s]' % re.escape(string.punctuation), '', real_descr)
            else:
                real_descr = ''
            actual_descr = re.sub('[%s]' % re.escape(string.punctuation), '', especification)
            metric = especification_similarity(real_descr, actual_descr)
            
            #print(real_descr, actual_descr, date_ann, col)
            return metric
    
    else:
        return similarity_cod(especification, int(code), list_past_cods)
        #return True

def persons_text(text:str):
    """Algoritmo para extraer nombres de personas.

    Args:
        text (str): Texto de las personas existentes en una anotación

    Returns:
        [str, str]: Lista con el nombre completo y la indicación "A", "I", "X", "DE", según el caso.
    """
    if text.startswith('DE:'):
        return [re.sub('DE: ', '',text), 'DE']
    elif text.startswith('A:'):
        if text.endswith(' X'):
            return [re.sub('A: | X|X$', '',text), '-X']
        elif text.endswith(' I'):
            return [re.sub('A: | I|I$', '',text), '-I']
        else:
            return [re.sub('A: ', '',text), '-A']
    else:
        return [text, 'NN']

def process_persons(annotations):
    """Permite reconocer cuáles son todos los actores en las anotaciones existentes.

    Args:
        annotations (dict): Objeto que posee todas las anotaciones y descripción de las mismas.

    Returns:
        df, pandas.DataFrame: DataFrame con las personas identificadas y su trazabilidad
        alerts, list(dict): Alertas encontradas.
    """
    alerts = []
    
    result = {part: annotations[part]['personas'] for part in annotations.keys()}
    
    for textlist in result.keys():
        result[textlist] = [data_converter.process_whitespaces(
            re.sub('(?:\$\d{1,3}(?:\.\d{3})*(?:\.\d{2})?|(?<!\d)\d{1,3}(?:\.\d{3})*(?:\.\d{2})?(?!\d))', '', k)
            ) for k in result[textlist]]
    
    resume = {}
    
    for textlist in result.keys():
        resume[textlist] = {'DE': [], 'A': [], 'X': [], 'I': [], 'NN': []}
        for k in range(1,len(result[textlist])):
            if result[textlist][k].startswith('DE: '):
                if result[textlist][k].endswith(' X'):
                    resume[textlist]['DE'] = resume[textlist]['DE'] + [re.sub('DE: | X', '', result[textlist][k])]
                    alerts += [
                        {'anotacion': textlist,
                         'mensaje': f'''Asignación de titular errónea (DE), a {resume[textlist]['DE'][-1]}'''                         
                         }]
                else:
                    resume[textlist]['DE'] = resume[textlist]['DE'] + [re.sub('DE: ', '', result[textlist][k])]
            elif result[textlist][k].startswith('A: '):
                if result[textlist][k].endswith('X'):
                    resume[textlist]['X'] = resume[textlist]['X'] + [data_converter.process_whitespaces(re.sub('A: | X|X$', '', result[textlist][k]))]
                elif result[textlist][k].endswith('I') or result[textlist][k].endswith('I'):
                    resume[textlist]['I'] = resume[textlist]['I'] + [data_converter.process_whitespaces(re.sub('A: | I|I$', '', result[textlist][k]))]
                else:
                    resume[textlist]['A'] = resume[textlist]['A'] + [re.sub('A: ', '', result[textlist][k])]
            else:
                resume[textlist]['NN'] = resume[textlist]['NN'] + [result[textlist][k]]
    
    #st.write(resume)
    
    output = {}
    for key, value in resume.items():
        for de_a, strings in value.items():  # 'de_a' será "DE" o "A", y 'strings' es la lista
            for string in strings:
                num_nit_list = re.findall(r'\d+', string)
                num_nit = None
                
                if len(num_nit_list)>0:
                    num_nit = num_nit_list[0]
                
                string = re.sub(r'[^A-Za-z0-9\s]', '', string)    
                string = re.sub(r'NIT | CC |\d+\w+', '', string)
                string = data_converter.process_whitespaces(string)
                
                #Obtener strings para dejar solo uno
                string_changed = False
                if len(output.keys())>0:
                    for string_actual in output:
                        if comparator.similarity(string, string_actual)>0.92:
                            #st.write(output)
                            #st.write(string, string_actual)
                            if len(string)>len(string_actual):
                                output[string] = output.pop(string_actual)
                            else:
                                string = string_actual
                            string_changed = True
                            break
                        if fuzz.ratio(string, 'SIN INFORMACION')>95:
                            alerts += [
                                {'anotacion': key,
                                'mensaje': f'''Se encontró un caso SIN INFORMACIÓN.'''                         
                                }]
                
                if not string_changed:
                    output[string] = {}
                    
                if 'CC' not in output[string]:
                    output[string]['CC'] = num_nit
                else:
                    if num_nit is not None:
                        if output[string]['CC'] is None:
                            output[string]['CC'] = num_nit
                        else:
                            if output[string]['CC'] != num_nit:
                                alerts += [
                                {'anotacion': key,
                                'mensaje': f'''Asignación de cédula errónea, a {string}'''                         
                                }]
                output[string][key] = de_a
    #st.write(output)
    
    df = pd.DataFrame.from_dict(output, orient='index').T
    #st.subheader('Trazabilidad de personas')
    #st.write(df)
    return df.T, alerts

def condicion_resolutoria(annotations, alerts):
    """
    Se verifica si la condición resolutoria (expresa) ha sido cancelada.
    Con el fin de ser independiente al código de la especificación, se usa un regex
    para su análisis. Se imprime al usuario cuando se encuentra y su estado.

    Args:
        annotations (_type_): _description_
        alerts (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    for k in annotations.keys():
        if comparator.similarity('CONDICION RESOLUTORIA', annotations[k]['especificacion'])>0.75:
            alerts += [
                        {'anotacion': k,
                        'mensaje': f'''Condición resolutoria encontrada.'''                         
                        }]
            #Tengo condicion resolutoria expresa
            if 'canceledby' in annotations[k].keys():
                alerts[-1]['mensaje'] += ' Se encuentra cancelada.'
            else:
                alerts[-1]['mensaje'] += ' Se encuentra sin cancelar.'
    return alerts

def demanda_reivindicatoria(annotations, alerts, persons):
    """Verifica si una demanda en proceso reivindicatorio ha sido asignado correctamente.
    Si no lo está, envía una alerta.

    Args:
        annotations (dict): _description_
        alerts (list(dict)): _description_
        persons (_type_): _description_

    Returns:
        list(dict): Alertas actualizadas.
    """
    procesed_persons = persons.copy().fillna('')
    previous_key = None
    for k in annotations.keys():
        if comparator.similarity('DEMANDA EN PROCESO REIVINDICATORIO', annotations[k]['especificacion'])>0.85:
            alerts += [
                        {'anotacion': k,
                        'mensaje': f'''Demanda en proceso reivindicatorio encontrada.'''                         
                        }]
            #Tengo demanda
            
            #alerts[-1]['mensaje'] += ''.join(annotations[previous_key]['personas'])
            
            actual_ann = set(procesed_persons[procesed_persons[k].str.contains('X|A')][k].index.to_list())
            
            past_ann = set(procesed_persons[procesed_persons[str(int(k)-1)].str.contains('X')][str(int(k)-1)].index.to_list())
            
            diff = actual_ann.union(past_ann) - actual_ann.intersection(past_ann)
            
            alerts[-1]['mensaje'] += ' Los propietarios no coinciden: Se encuentran los nombres ' + ', '.join([person for person in diff])
            alerts[-1]['mensaje'] += f' entre las anotaciones {int(k)-1} y {k}.'
        previous_key = k
    return alerts
    
def correct_dates(annotations, alerts):
    n = len(annotations)
    anns = list(annotations.keys())
    
    if n > 1:
        for ann_number in range(2,len(anns)):
            if annotations[anns[ann_number]]['fecha'] < annotations[anns[ann_number-1]]['fecha']:
    
                alerts += [
                            {'anotacion': anns[ann_number],
                            'mensaje': f'''La fecha no es coherente, pues es posterior a la anotación anterior ({anns[ann_number-1]}).'''                         
                            }]
            past_ann = ann_number
    return alerts

def englobes(annotations):
    output = {
        'englobes':[],
        'desenglobes': []
    }
    
    for k in annotations.keys():
        if annotations[k]['especificacion'].__contains__('DESENGLOBE'):
            output['desenglobes'] += [k]
        elif annotations[k]['especificacion'].__contains__('ENGLOBE'):
            output['englobes'] += [k]
    
    n_des = len(output['desenglobes'])
    n_eng = len(output['englobes'])
    
    output_text = f"Existen {n_des} desenglobe" + ("s" if n_des!=1 else "") + (f", en la(s) anotacion(es): {', '.join(output['desenglobes'])}" if n_des>0 else "") + \
    f" y existen {n_eng} englobe" + ("s" if n_eng!=1 else "") + (f", en la(s) anotacion(es): {', '.join(output['englobes'])}." if n_eng>0 else ".")
    return output_text

def process_document(bb_data):
    consulta, informacion, anotaciones, salvedades, nuevas_matriculas = preprocessing.preprocess_pdf(bb_data)
    
    persons, alerts = process_persons(anotaciones)
    
    alerts = correct_dates(anotaciones, alerts)
    
    alerts = condicion_resolutoria(anotaciones, alerts)
    
    alerts = demanda_reivindicatoria(anotaciones, alerts, persons)
    
    return consulta, informacion, anotaciones, salvedades, nuevas_matriculas, alerts, persons