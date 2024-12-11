import pandas as pd
import re
import unicodedata

def dict_to_table(element, enumerated=False):
    if enumerated:
        return pd.DataFrame(element)
    else:
        return pd.DataFrame(element, columns=['Descripción'])
    
def process_whitespaces(text):
    return re.sub(r'\s+$','',text, flags=re.MULTILINE)

def eliminar_tildes(texto):
    # Descomponer los caracteres acentuados
    texto = unicodedata.normalize('NFD', texto)
    
    # Filtrar los caracteres que no son marcas diacríticas
    texto_sin_tildes = ''.join([c for c in texto if unicodedata.category(c) != 'Mn'])
    
    # Reconstruir la cadena sin tildes
    return texto_sin_tildes
    