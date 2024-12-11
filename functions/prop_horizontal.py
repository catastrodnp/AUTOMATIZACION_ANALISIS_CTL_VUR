import re

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