import camelot
import pandas as pd
import os
import glob
from collections import defaultdict

# Columnas clave que queremos identificar como comunes entre DataFrames
columnas_clave = ['NÚMERO DE ANOTACIÓN', 'NÚMERO DE CORRECCIÓN', 'RADICACIÓN DE ANOTACIÓN',
                  'FECHA DE SALVEDAD', 'RADICACIÓN DE SALVEDAD', 'DESCRIPCIÓN SALVEDAD FOLIO']

# Columnas que siempre debemos conservar
columnas_fijas = ['Nombre_archivo', 'Nombre_tabla']

# Función para verificar cuántas columnas clave están presentes en un DataFrame
def tiene_columnas_comunes(columnas, columnas_clave):
    comunes = [col for col in columnas if col in columnas_clave]
    return len(comunes) >= 5  # Verificamos si hay al menos 5 columnas comunes

# Función para extraer tablas de un PDF y procesar todas, concatenando aquellas con al menos 5 columnas comunes
def extraer_y_procesar_tablas(lista_pdfs):
    # Diccionario para agrupar los DataFrames por sus columnas
    dataframes_agrupados = defaultdict(list)
    dataframes_concatenar = []

    # Iterar sobre los archivos PDF
    for pdf in lista_pdfs:
        # Extraer todas las tablas del PDF
        tablas = camelot.read_pdf(pdf, pages='all')

        # Iterar sobre las tablas extraídas
        for i, tabla in enumerate(tablas):
            # Convertir la tabla a DataFrame
            df_tabla = tabla.df
            df_tabla.columns = df_tabla.iloc[0]  # La primera fila se convierte en encabezado
            df_tabla = df_tabla[1:].reset_index(drop=True)  # Eliminar la primera fila
            df_tabla.columns = df_tabla.columns.str.replace('\n', ' ')  # Limpiar nombres de columnas

            # Añadir columnas para el nombre del archivo y la tabla
            df_tabla['Nombre_archivo'] = os.path.basename(pdf)
            df_tabla['Nombre_tabla'] = f"Tabla_{i+1}"

            # Verificar si el DataFrame tiene al menos 5 columnas comunes clave
            if tiene_columnas_comunes(df_tabla.columns, columnas_clave):
                # Mantener solo las columnas clave y las columnas fijas
                columnas_a_mantener = [col for col in df_tabla.columns if col in columnas_clave or col in columnas_fijas]
                df_tabla_filtrado = df_tabla[columnas_a_mantener]
                # Guardar este DataFrame para concatenar posteriormente
                dataframes_concatenar.append(df_tabla_filtrado)
            else:
                # Agrupar las tablas que no se deben concatenar, pero se deben mantener
                columnas_clave_df = tuple(df_tabla.columns)  # Usar las columnas como clave
                dataframes_agrupados[columnas_clave_df].append(df_tabla)

    # Concatenar los DataFrames que cumplen con la condición de columnas comunes
    if dataframes_concatenar:
        salvedades_df1 = pd.concat(dataframes_concatenar, ignore_index=True)
    else:
        salvedades_df1 = pd.DataFrame()  # Si no hay DataFrames válidos, devolver un DataFrame vacío

    # Guardar las tablas que no se concatenaron en archivos separados
    for i, (columnas, dfs) in enumerate(dataframes_agrupados.items(), start=1):
        df_no_concatenado = pd.concat(dfs, ignore_index=True)
        nombre_archivo = f'tablas_no_consolidadas_{i}.csv'
        df_no_concatenado.to_csv(nombre_archivo, index=False)
        print(f"Archivo guardado: {nombre_archivo}")

    return salvedades_df1