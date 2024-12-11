from pypdf import PdfReader
import re, string, regex
from datetime import datetime
import pandas as pd
from pprint import pprint

from functions import processing
    
def preprocess_pdf(documento_pdf):
    # creating a pdf reader object 
    reader = PdfReader(documento_pdf)#(f'Topaipi/170-{documento_pdf}.pdf') 
      
    # printing number of pages in pdf file 
    #print(len(reader.pages)) 
    
    complete_text = []
    # extracting text from page 
    for page in reader.pages:
        complete_text.append(page.extract_text())
    
    #CONSULTA JURIDICADA VUR DE MATRICULA INMOBILIARIA
    complete_text = "".join(complete_text)
    complete_text = re.sub('CONSULTA JURIDICADA VUR DE MATRICULA INMOBILIARIA',
                           '',
                           complete_text)
    complete_text = re.sub('NO ES UN CERTIFICADO, SOLO SIRVE DE CONSULTA',
                           '',
                           complete_text)
        
    complete_text = complete_text.replace('LA PRESENTE CONSULTA NO PERMITE ESTABLECER SI  A LA FECHA DE SU EXPEDICIÓN EXISTE UNA ACTUACIÓN','')

    complete_text = re.sub('ADMINISTRATIVA O UN PROCESO DE REGISTRO QUE MODIFIQUE EL ESTADO JURÍDICO DE ESTE BIEN INMUEBLE',
                           '',
                           complete_text)

    complete_text = re.sub('\n','', complete_text)
    complete_text = re.sub('No válido como certificado detradición de matrícula inmobiliaria  ','', complete_text)
        
    consult_list = re.findall('(?=Número de consulta).{0,210}(?:1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])',
               complete_text)
    
    complete_text = re.sub(r'Número de consulta: \d+\s+Fecha consulta: \d{1,2} de \w+ de \d{4} a las \d{2}:\d{2}:\d{2} [AP]M\s*Nro Matrícula: \d+\s*-\s*\d+\s+Usuario que consultó: \w+\s*Entidad: \w+\s*Ciudad: \w+\s*IP: \d+\.\d+\.\d+\.\d+', 
                           '',
                           complete_text)

    consult_data = consult_list[0]
    
    new_registration = re.search('(?<=CON BASE EN LA PRESENTE SE ABRIERON LAS SIGUIENTES MATRICULAS).*(?=Referencia catastral anterior:)', complete_text)
    
    property_register = None
    if new_registration:
        property_register = re.findall('\d{1,3} -> \d{5,6}',new_registration[0])
        for element in range(len(property_register)):
            property_register[element] = dict(zip(['anotacion','matricula'],property_register[element].split(' -> ')))
    
    watermark = complete_text.split('Información Básica de la Matrícula')
    info = watermark[1].split('Detalle de las Anotaciones')
    annotations = info[1].split('Trámites en Curso')
    processes = annotations[1]
    
    watermark = re.sub('\n','', watermark[0])
    info = re.sub('\n','', info[0])
    annotations = re.sub('\n','', annotations[0])
    
    consult_dict = {
        'numero consulta': re.search('(?<=Número de consulta: ).*(?=Fecha consulta:)', consult_data)[0],
        'fecha consulta': re.search('(?<=Fecha consulta: ).*(?=Nro Matrícula:)', consult_data)[0],
        'numero matricula': re.search('(?<=Nro Matrícula: ).*(?=Usuario que consultó:)', consult_data)[0],
        'usuario': re.search('(?<=Usuario que consultó: ).*(?=Entidad:)', consult_data)[0],
        'entidad': re.search('(?<=Entidad: ).*(?=Ciudad:)', consult_data)[0],
        'ciudad': re.search('(?<=Ciudad: ).*(?=IP:)', consult_data)[0],
        'ip': re.search('(?<=IP: ).*', consult_data)[0]
        
    }
    
    info_dict = {
        'circulo registral': re.search('(?<=Círculo Registral: ).*(?=Nro Matrícula:)', info)[0],
        'numero matricula': re.search('(?<=Nro Matrícula: ).*(?=Referencia catastral:)', info)[0],
        'referencia catastral': re.search('(?<=Referencia catastral: ).*(?=Tipo Predio:)', info)[0],
        'tipo predio': re.search('(?<=Tipo Predio: ).*(?=DEPTO: )', info)[0],
        'departamento': re.search('(?<=DEPTO: ).*(?= MUNICIPIO: )', info)[0],
        'municipio': re.search('(?<=MUNICIPIO: ).*(?= VEREDA: )', info)[0],
        'vereda': re.search('(?<=VEREDA: ).*(?=Dirección actual:)', info)[0],
        'direccion actual': re.search('(?<=Dirección actual:).*(?=Estado del Folio:)', info)[0],
        'estado folio': re.search('(?<=Estado del Folio: ).*(?=Número total de anotaciones:)', info)[0],
        'numero salvedades': re.search('(?<=Número total de salvedades: ).*(?=Cabida y Linderos:)', info)[0],
        'cabida_linderos': re.search('(?<=Cabida y Linderos:).*(?=Complementaciones:)', info)[0],
        'complementaciones': re.search('(?<=Complementaciones: ).*(?=Fecha de apertura:)', info)[0],
        'fecha apertura': re.search('(?<=Fecha de apertura: ).*(?=Tipo de instrumento:)', info)[0],
        'tipo instrumento': re.search('(?<=Tipo de instrumento: ).*(?=Fecha del instrumento:)', info)[0],
        'fecha instrumento': re.search('Fecha del instrumento: (\d{2}-\d{2}-\d{4})', info)[0].replace('Fecha del instrumento: ',''),#re.search('(?<=Fecha del instrumento: ).*(?=Referencia catastral anterior:)', info)[0],
        'referencia anterior': re.search('(?<=Referencia catastral anterior: ).*(?=Direcciones anteriores:)', info)[0],
        'direcciones_anteriores': re.search('(?<=Direcciones anteriores: ).*', info)[0]
    }
    
    info_dict['area'] = processing.process_areas(info_dict['cabida_linderos'])
    info_dict['propiedad horizontal'] = 'SI' if processing.es_propiedad_horizontal(info_dict['direccion actual']) else 'NO'
    
    annotations_description = re.search('(?<=Anotaciones:).*(?=SALVEDADES:)', annotations)[0]
    
    exceptions = re.search('(?<=SALVEDADES: \(Información Anterior o Corregida\)).*', annotations)[0]
    
    anotations_list = re.split('ANOTACION: ', annotations_description)[1:]
    
    #print('ANOTACIONES')
    ann_items = {}
    for ann in anotations_list:

        number_ann = re.search('(?<=Nro ).*(?= Fecha: )', ann)[0]
        #pprint(ann)
        ann_items[number_ann] = {
            #'numero': re.search('(?<=Nro ).*(?= Fecha: )', ann)[0],
            'fecha': re.search('(?<= Fecha:).*(?=Radicación:)', ann)[0],
            'radicacion': re.search('(?<=Radicación:).*(?=Doc: )', ann)[0],
            'doc': re.search('(?<=Doc: ).*(?=VALOR ACTO:)', ann)[0],
            'valor': re.search('(?<=VALOR ACTO: \$).*(?=ESPECIFICACION: )', ann)[0],
            'especificacion': re.search('(?<=ESPECIFICACION: ).*(?=PERSONAS QUE INTERVIENEN EN EL ACTO \(X-Titular de derecho real de dominio,I-Titular de dominio incompleto\))', ann)[0],
            'personas': re.search('(?<=PERSONAS QUE INTERVIENEN EN EL ACTO \(X-Titular de derecho real de dominio,I-Titular de dominio incompleto\)).*', ann)[0],
        }
        ann_items[number_ann]['fecha'] = re.sub(" ", "", ann_items[number_ann]['fecha'])
        ann_items[number_ann]['fecha'] = datetime.strptime(ann_items[number_ann]['fecha'], r'%d-%m-%Y')
        ann_items[number_ann]['personas'] = re.split("(?=A: |DE: )", ann_items[number_ann]['personas'])
        
        for key_p in range(len(ann_items[number_ann]['personas'])):
            ann_items[number_ann]['personas'][key_p] = re.sub("LA PRESENTE CONSULTA NO PERMITE ESTABLECER SI  A LA FECHA DE SU EXPEDICIÓN EXISTE UNA ACTUACIÓN","", ann_items[number_ann]['personas'][key_p])
        
        ann_items[number_ann]['codigo_especificacion'] = re.split(" ", ann_items[number_ann]['especificacion'])[0].replace(" ","")#re.findall('\d+',ann_items[number_ann]['especificacion'])[0]
        ann_items[number_ann]['especificacion'] = " ".join(re.split(" ", ann_items[number_ann]['especificacion'])[1:])
        ann_items[number_ann]['valid_true'] = processing.validate_code(ann_items[number_ann]['codigo_especificacion'], 
                                                            ann_items[number_ann]['especificacion'],
                                                            ann_items[number_ann]['fecha'])
        eliminations = re.search('Se cancela anotación No: \d+', ann)
        
        ann_items[number_ann]['valor'] = re.sub('Se cancela anotación No: \d+','',ann_items[number_ann]['valor'])
        
        if eliminations:
            ann_items[number_ann]['cancels'] = re.search('\d+',eliminations[0])[0]
            if ann_items[number_ann]['cancels'] in ann_items.keys(): #not 
            #   ann_items[ann_items[number_ann]['cancels']] = {}
                ann_items[ann_items[number_ann]['cancels']]['canceledby'] = number_ann
        
        #print(ann_items)
    
    exceptions_list = re.split('Anotación Nro: ',exceptions)[1:]
    
    #print('CORRECCIONES')
    exc_items = []
    for exc in exceptions_list:
        #number_exc = re.search('(?<=Nro corrección: ).*(?=Radicación:)', exc)[0]
        exc_item = {
            'anotacion': re.search('.*(?=Nro corrección:)', exc)[0],
            'numero': re.search('(?<=Nro corrección: ).*(?=Radicación:)', exc)[0],
            'radicacion': re.search('(?<=Radicación:).*(?=Fecha: )', exc)[0],
            'final': re.search('(?<=Fecha: ).*', exc)[0]
        }
        if re.search(r'\d{2}\-\d{2}\-\d{4}',exc_item['final']):
            exc_item['fecha']=re.search(r'\d{2}\-\d{2}\-\d{4}',exc_item['final'])[0]
            exc_item['descripcion']=re.findall(r'[^(\d{2}\-\d{2}\-\d{4})].*',exc_item['final'])[0]
        else:
            exc_item['fecha']=None
            exc_item['descripcion']=exc_item['final']
        exc_item.pop('final')
        exc_items.append(exc_item)
        #print(exc_items)
    
    return consult_dict, info_dict, ann_items, exc_items, property_register