import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

from streamlit_pdf_viewer import pdf_viewer
from streamlit_js_eval import streamlit_js_eval
from streamlit_timeline import timeline

from functions import processing, preprocessing, pdf_extractor, annotations, salvedades, areas_cabida,pdf_extractor1, salvedades1,prop_horizontal,annotations2
from tqdm import tqdm
import time, tempfile, os, re, base64
import plotly.express as px


if "final_df" not in st.session_state:
    st.session_state["final_df"] = None

if "grouped_df" not in st.session_state:
    st.session_state["grouped_df"] = None


def format_metric_with_hover(label, value, value_counts):
    """
    Genera HTML para una métrica que muestra una tabla al hacer hover y resalta el valor en rojo si es mayor a 1.
    
    Args:
        label (str): El título de la métrica.
        value (Union[str, int, float]): El valor de la métrica (puede ser string o numérico).
        value_counts (pd.Series): Serie con los conteos de valores para mostrar en la tabla al hacer hover.
    
    Returns:
        str: HTML que combina las funcionalidades de hover y resaltado.
    """
    # Convertir el valor a número si es un string (eliminar $ y , si existen)
    if isinstance(value, str):
        try:
            value_numeric = float(value.replace('$', '').replace(',', ''))
        except ValueError:
            value_numeric = 0  # Asignar 0 si la conversión falla
    else:
        value_numeric = value

    # Clase para el color basado en el valor
    color_class = "red" if value_numeric > 1 else ""

    # Convertir los value_counts a una tabla HTML
    value_counts_html = value_counts.to_frame().to_html(classes="hover-table", header=False)

    # Generar el HTML combinado
    return f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="metric-value {color_class}">{value}</div>
            <div class="hover-content">
                {value_counts_html}
            </div>
        </div>
    """



st.set_page_config(layout="wide", page_title="Análisis de VUR", page_icon="📄")

# --- Estilo personalizado ---
# --- Estilo personalizado ---
st.markdown(
    """
    <style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .main-logo {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-left: 10px;
    }
    .main-title {
        text-align: left;
        font-size: 3.4em;
        color: #1A237E;
        margin: 0;
    }
    .stButton>button {
        background-color: #1A237E;
        color: white;
        border-radius: 5px;
        padding: 10px;
        font-size: 1em;
    }
    .stButton>button:hover {
        background-color: #3949AB;
    }
    .metric-container {
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-label {
        font-size: 1.5em;
        font-weight: bold;
        color: #333333;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        color: black;
    }
    .metric-value.red {
        color: red;
    }
    .metric-container {
        position: relative;
        display: inline-block;
        margin: 10px;
        text-align: center;
    }
    .hover-content {
        visibility: hidden;
        position: absolute;
        background-color: white;
        border: 1px solid #ccc;
        padding: 10px;
        z-index: 1;
        width: 200px;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
    }
    .metric-container:hover .hover-content {
        visibility: visible;
    }
    .hover-table {
        font-size: 0.8em;
        width: 100%;
    }
    </style>
    <div class="header-container">
        <h1 class="main-title">Análisis de VUR</h1>
        <div class="main-logo">
            <img src="https://www.dnp.gov.co/img/og-img.jpg" width="250">
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# --- Crear pestañas ---
tabs = st.tabs(["1 - Análisis individual VUR", "2 - Análisis múltiple VUR","3 - Análisis múltiple CTL 1","4 - Análisis múltiple CTL 2"])

# --- Pestaña 1: Análisis individual VUR ---
with tabs[0]:
    st.title('Revisión de documentos PDF (Individual)')
    #timeline(data, height=500)
    MIN_SIMILARITY = 0.3
    uploaded_file = st.file_uploader("Inserta el archivo PDF.")
    if uploaded_file:
        
        bytes_data = uploaded_file.read()
        bb_data= BytesIO(bytes_data)
        
        consulta, informacion, anotaciones, salvedades, nuevas_matriculas, alerts, persons = processing.process_document(bb_data)
        
        data = {
        "title": {
            "text": {
                "headline": f"Matrícula inmobiliria<br>{informacion['numero matricula']}",
                "text": f"""<p>Información del predio</p>{
                        pd.DataFrame.from_dict({k: informacion[k] for k in set(list(informacion.keys())) - set(['numero matricula', 'cabida_linderos', 'complementaciones'])}, 
                        orient='index').to_html(header=False)}<br>
                        """
            },
            "start_date": {
                "year": "1900"
            },
            "end_date": {
                "year": "2024"
            }
            }
        }
        
        st.header('Alertas')
        if alerts:
            st.dataframe(pd.DataFrame(alerts).drop_duplicates(), use_container_width=True, hide_index=True)
        else:
            st.write('No existen alertas para este predio.')
        
        st.header('Anotaciones')
        
        data['events'] = [ 
            {
                "start_date": {
                    "year": element['fecha'].year,
                    "month": element['fecha'].month,
                    "day": element['fecha'].day,
                },
                "text": {
                    "headline": f"Anotación {key}",#{element['valid_true'][1] if ~element['valid_true'][0] else ""}</p>
                    "text": f"""{f"El código parece estar desactualizado o inválido ({round(element['valid_true']*100,1)} %)." if element['valid_true']<MIN_SIMILARITY else f"El código parece estar correcto ({round(element['valid_true']*100,1)} %)."}
                        {f"Esta anotación fue cancelada por la anotación número {element["canceledby"]} ." if "canceledby" in element.keys() else ""}
                        <p>Tabla de información</p>{
                        pd.DataFrame.from_dict({k: element[k] for k in set(list(element.keys())) - set(['personas', 'valid_true', "canceledby"])}, 
                        orient='index').to_html(header=False)}<br>
                        <p>Personas en la anotación</p>
                        {pd.DataFrame.from_dict(element)['personas'].iloc[1:].to_frame().to_html(index=False, header=False)}
                        """ + 
                        (f"""
                        <p>Salvedades:</p>
                        {pd.DataFrame.from_dict(salvedades)[pd.DataFrame.from_dict(salvedades)['anotacion']==key].to_html(index=False, header=pd.DataFrame.from_dict(salvedades)[pd.DataFrame.from_dict(salvedades)['anotacion']==key].shape[0]>0)}
                        """ if len(salvedades)>0 else "")
                }   
            } for key, element in anotaciones.items()
        ]
        
        timeline(data, height=800)
        
        st.subheader('Englobes y desenglobes')
        st.write(processing.englobes(anotaciones))
        
        if nuevas_matriculas:
            nuevas_matriculas = pd.DataFrame(nuevas_matriculas)
            nuevas_matriculas['matricula'] = nuevas_matriculas['matricula'].apply(lambda x: processing.new_matricula(informacion['numero matricula'],x))
            st.subheader('Nuevas matrículas creadas')
            st.dataframe(nuevas_matriculas, use_container_width=True, hide_index=True)
        
        st.subheader('Trazabilidad de personas')
        st.write(persons)
        
        
        st.header('Información de consulta')
        st.dataframe(consulta, use_container_width=True, column_config={0:'Descripción', 1:'Detalle'})
        
        st.header('Archivo')
        page_width = streamlit_js_eval(js_expressions='window.innerWidth', key='WIDTH',  want_output = True,)
        pdf_viewer(uploaded_file.getvalue(), height=700, width=int(page_width))

# --- Pestaña 2: Análisis múltiple VUR ---
with tabs[1]:
    st.title('Análisis múltiple de documentos PDF (VUR)')
    uploaded_files1 = st.file_uploader("Selecciona múltiples archivos PDF", type="pdf", accept_multiple_files=True)

    if uploaded_files1:
        # Mostrar los nombres de los archivos cargados
        pdf_names = [file.name for file in uploaded_files1]

        # Seleccionar un PDF para visualizar
        selected_pdf = st.selectbox("Selecciona un PDF para visualizar:", pdf_names)

        # Mostrar el PDF seleccionado
        if selected_pdf:
            file_index = pdf_names.index(selected_pdf)
            file_data = uploaded_files1[file_index].read()
            base64_pdf = base64.b64encode(file_data).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

        # Botón para procesar todos los PDFs
        if st.button("Procesar PDFs"):
            with st.spinner("Procesando archivos..."):
                pdf_paths = {file.name: file for file in uploaded_files1}
                pdf_dataframes = []

                # Barra de progreso con tqdm
                progress_bar = st.progress(0)
                total_files = len(pdf_paths)
                for idx, (name, file) in enumerate(tqdm(pdf_paths.items(), desc="Procesando PDFs")):
                    df = pdf_extractor.process_pdfs([file])
                    df['Archivo'] = name  # Añadir nombre del archivo
                    pdf_dataframes.append(df)
                    progress_bar.progress((idx + 1) / total_files)
                    time.sleep(0.1)  # Simulación de procesamiento

                # Concatenar los resultados
                st.session_state["final_df"] = pd.concat(pdf_dataframes, ignore_index=True)

            st.success("¡Procesamiento completado!")
            
        if st.session_state["final_df"] is not None:
            st.markdown("### Resultados del Análisis de PDFs")
            st.dataframe(st.session_state["final_df"])
            

            # Resumen compacto
            summary_data = {
                "Tipo Predio": st.session_state["final_df"]['Tipo Predio'].nunique(),
                "Municipio": st.session_state["final_df"]['Municipio'].nunique(),
                "Vereda": st.session_state["final_df"]['Vereda'].nunique(),
                "Estado del Folio": st.session_state["final_df"]['Estado del Folio'].nunique(),
                "Tipo de Instrumento": st.session_state["final_df"]['Tipo de instrumento'].nunique()
            }

            # Métricas con hover
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.markdown(format_metric_with_hover("Tipo Predio", summary_data['Tipo Predio'], st.session_state["final_df"]['Tipo Predio'].value_counts()), unsafe_allow_html=True)
            col2.markdown(format_metric_with_hover("Municipio", summary_data['Municipio'], st.session_state["final_df"]['Municipio'].value_counts()), unsafe_allow_html=True)
            col3.markdown(format_metric_with_hover("Vereda", summary_data['Vereda'], st.session_state["final_df"]['Vereda'].value_counts()), unsafe_allow_html=True)
            col4.markdown(format_metric_with_hover("Estado Folio", summary_data['Estado del Folio'], st.session_state["final_df"]['Estado del Folio'].value_counts()), unsafe_allow_html=True)
            col5.markdown(format_metric_with_hover("T. Instrumento", summary_data['Tipo de Instrumento'], st.session_state["final_df"]['Tipo de instrumento'].value_counts()), unsafe_allow_html=True)
            
        if st.button("Análisis Anotaciones"):
            if "final_df" in st.session_state and st.session_state["final_df"] is not None:
                with st.spinner("Procesando anotaciones..."):
                    # Asegurar que final_df tiene la columna necesaria
                    st.session_state["final_df"]['Archivo PDF'] = st.session_state["final_df"]['Nro Matrícula'].apply(lambda x: f"{x}.pdf")

                    # Procesar las anotaciones y guardarlas en session_state
                    st.session_state["anotaciones_df"] = annotations.procesar_anotaciones(st.session_state["final_df"])

                st.success("¡Análisis de anotaciones completado!")
            else:
                st.error("Primero debes procesar los PDFs antes de analizar las anotaciones.")

        # Mostrar resultados de anotaciones si existen
        if "anotaciones_df" in st.session_state and st.session_state["anotaciones_df"] is not None:
            st.markdown("### Resultados del Análisis de Anotaciones")
            st.dataframe(st.session_state["anotaciones_df"], use_container_width=True)

            # Métricas de resumen
            suma_valor_acto = st.session_state["anotaciones_df"]['Valor Acto'].str.replace(',', '').astype(float).sum()
            conteo_especificacion = st.session_state["anotaciones_df"]['Descripción Especificación'].nunique()
            conteo_codigo_xi = st.session_state["anotaciones_df"]['Código (X/I)'].nunique()
            conteo_de = st.session_state["anotaciones_df"]['De'].nunique()
            conteo_a = st.session_state["anotaciones_df"]['A'].nunique()
            conteo_matriculas = st.session_state["anotaciones_df"]['Nro Matrícula'].nunique()

            # Crear métricas con hover
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.markdown(format_metric_with_hover("Valor Acto", f"<div style='font-size: 0.8em;'>{suma_valor_acto:,.0f}</div>", st.session_state["anotaciones_df"]['Valor Acto'].value_counts()), unsafe_allow_html=True)
            col2.markdown(format_metric_with_hover("Especificación", conteo_especificacion, st.session_state["anotaciones_df"]['Descripción Especificación'].value_counts()), unsafe_allow_html=True)
            col3.markdown(format_metric_with_hover("Código (X/I)", conteo_codigo_xi, st.session_state["anotaciones_df"]['Código (X/I)'].value_counts()), unsafe_allow_html=True)
            col4.markdown(format_metric_with_hover("DE", conteo_de, st.session_state["anotaciones_df"]['De'].value_counts()), unsafe_allow_html=True)
            col5.markdown(format_metric_with_hover("A", conteo_a, st.session_state["anotaciones_df"]['A'].value_counts()), unsafe_allow_html=True)
            col6.markdown(format_metric_with_hover("Matrículas", conteo_matriculas, st.session_state["anotaciones_df"]['Nro Matrícula'].value_counts()), unsafe_allow_html=True)

            # Filtrar las filas donde 'Descripción Especificación' comienza con "HIPOTECA ABIERTA"
            hipotecas_abiertas = st.session_state["anotaciones_df"][
                st.session_state["anotaciones_df"]['Descripción Especificación'].str.startswith("HIPOTECA ABIERTA", na=False)
            ]

            # Mostrar tabla si hay coincidencias
            if not hipotecas_abiertas.empty:
                st.markdown("### Anotaciones con 'HIPOTECA ABIERTA'")
                st.dataframe(
                    hipotecas_abiertas[['Nro Matrícula', 'Número de Anotación', 'Descripción Especificación']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No se encontraron anotaciones con 'HIPOTECA ABIERTA'.")

                
        if st.button("Análisis Salvedades"):
            if "final_df" in st.session_state and st.session_state["final_df"] is not None:
                with st.spinner("Procesando salvedades..."):
                    # Asegurar que final_df tiene la columna necesaria
                    st.session_state["final_df"]['Archivo PDF'] = st.session_state["final_df"]['Nro Matrícula'].apply(lambda x: f"{x}.pdf")

                    # Procesar las salvedades
                    salvedades_df = salvedades.procesar_salvedades(st.session_state["final_df"])

                    # Unir con anotaciones_df si existe
                    if "anotaciones_df" in st.session_state and st.session_state["anotaciones_df"] is not None:
                        merged_df = pd.merge(
                            st.session_state["anotaciones_df"],
                            salvedades_df,
                            how="left",
                            left_on=["Nro Matrícula","Número de Anotación"],
                            right_on=["Nro Matrícula","Anotación Nro"]
                        )
                    else:
                        st.error("Primero debes realizar el análisis de anotaciones para generar el merge.")
                        merged_df = salvedades_df

                    # Guardar el resultado del merge en session_state para futuras referencias
                    st.session_state["salvedades_df"] = merged_df

                st.success("¡Análisis de salvedades completado!")

            else:
                st.error("Primero debes procesar los PDFs antes de analizar las salvedades.")

            # Filtrar el DataFrame para mostrar solo cuando 'Descripción Salvedad' no es None
            filtered_salvedades_df = st.session_state["salvedades_df"][
                st.session_state["salvedades_df"]['Descripción Salvedad'].notnull()
            ][['Nro Matrícula', 'Número de Anotación', 'Fecha_x', 'Descripción Salvedad', 'Código Especificación', 'Descripción Especificación']]

            # Mostrar el DataFrame filtrado
            if not filtered_salvedades_df.empty:
                st.markdown("### Martículas y anotaciones con salvedades")
                st.dataframe(filtered_salvedades_df, use_container_width=True)
            else:
                st.info("No hay salvedades con descripción disponible.")
                
                
        if st.button("Análisis de Áreas"):
            if "final_df" in st.session_state and st.session_state["final_df"] is not None:
                with st.spinner("Procesando áreas..."):
                    # Asegurar que final_df contiene las columnas necesarias
                    if "Cabida y Linderos" in st.session_state["final_df"]:
                        # Aplicar el proceso de extracción y conversión
                        st.session_state["final_df"]['Areas_Procesadas'] = areas_cabida.process_areas(st.session_state["final_df"]['Cabida y Linderos'])
                        # Crear la columna 'Area_definitiva'
                        st.session_state["final_df"]['Area_definitiva'] = st.session_state["final_df"]['Areas_Procesadas'].apply(
                            lambda x: x[0] if isinstance(x, list) and x else None
                        )
                        
                        # Guardar métricas en session_state
                        num_matriculas = st.session_state["final_df"]['Nro Matrícula'].nunique()
                        area_total = st.session_state["final_df"]['Area_definitiva'].sum()

                        st.session_state["areas_metrics"] = {
                            "Número de Matrículas": num_matriculas,
                            "Área Total (M2)": area_total
                        }

                        st.success("¡Análisis de áreas completado!")
                    else:
                        st.error("La columna 'Cabidad y Linderos' no se encuentra en los datos procesados.")

        # Mostrar métricas de áreas si existen
        if "areas_metrics" in st.session_state:
            st.markdown("### Resultados del Análisis de Áreas")
            metrics = st.session_state["areas_metrics"]
            col1, col2 = st.columns(2)
            col1.markdown(format_metric_with_hover("Número de Matrículas", metrics["Número de Matrículas"], pd.Series([metrics["Número de Matrículas"]])), unsafe_allow_html=True)
            col2.markdown(format_metric_with_hover("Área Total (M2)", f"{metrics['Área Total (M2)']:.0f}", pd.Series([metrics["Área Total (M2)"]])), unsafe_allow_html=True)

            # Gráficos interactivos
            st.markdown("### Visualización de Áreas")

            # Convertir fechas a formato datetime
            st.session_state["final_df"]['Fecha de apertura'] = pd.to_datetime(st.session_state["final_df"]['Fecha de apertura'], errors='coerce')

            # Agregar datos agrupados por Fecha de Apertura
            apertura_group = st.session_state["final_df"].groupby(["Fecha de apertura", "Nro Matrícula"])['Area_definitiva'].sum().reset_index()
            apertura_group = apertura_group.dropna()

            # Agregar datos agrupados por Matrícula
            matricula_group = st.session_state["final_df"].groupby("Nro Matrícula")['Area_definitiva'].sum().reset_index()
            matricula_group = matricula_group.sort_values(by='Area_definitiva', ascending=False)

            # Crear una fila para las dos gráficas
            col1, col2 = st.columns(2)

            # Gráfico 1: Suma de Áreas por Fecha de Apertura
            #col1.markdown("#### Suma de Áreas por Fecha de Apertura")
            apertura_chart = px.bar(
                apertura_group,
                x='Fecha de apertura',
                y='Area_definitiva',
                color='Nro Matrícula',  # Leyenda por Número de Matrícula
                labels={'Fecha de apertura': 'Fecha de Apertura', 'Area_definitiva': 'Área Total (M2)', 'Nro Matrícula': 'Matrícula'},
                title='Suma de Áreas por Fecha de Apertura'
            )
            apertura_chart.update_layout(
                xaxis=dict(title="Fecha de Apertura"),
                yaxis=dict(title="Área Total (M2)"),
                bargap=0.05,  # Barras más anchas
                legend_title="Matrícula",
            )
            col1.plotly_chart(apertura_chart, use_container_width=True)

            # Gráfico 2: Suma de Áreas por Matrícula en Orden Descendente
            #col2.markdown("#### Suma de Áreas por Matrícula (Orden Descendente)")
            matricula_chart = px.bar(
                matricula_group,
                x='Nro Matrícula',
                y='Area_definitiva',
                labels={'Nro Matrícula': 'Matrícula', 'Area_definitiva': 'Área Total (M2)'},
                title='Suma de Áreas por Matrícula (Orden Descendente)'
            )
            matricula_chart.update_layout(
                xaxis=dict(title="Matrícula"),
                yaxis=dict(title="Área Total (M2)"),
                bargap=0.05,  # Barras más anchas
            )
            col2.plotly_chart(matricula_chart, use_container_width=True)

            # Botón para descargar resultados
            st.download_button(
                "Descargar resultados en CSV",
                st.session_state["final_df"].to_csv(index=False).encode('utf-8'),
                "resultados.csv",
                "text/csv"
            )
    else:
        st.info("Por favor, carga uno o más archivos PDF para comenzar.")


with tabs[2]:  # 3 - Análisis múltiple CTL 1
    st.title("Análisis múltiple de documentos PDF (CTL 1)")

    uploaded_files_ctl1 = st.file_uploader(
        "Selecciona múltiples archivos PDF",
        type="pdf",
        accept_multiple_files=True,
        key="file_uploader_ctl1"
    )

    if uploaded_files_ctl1:
        #st.sidebar.write("Archivos cargados:")
        #st.sidebar.write([file.name for file in uploaded_files_ctl1])

        # Botón para procesar archivos
        if st.button("Procesar PDFs CTL 1", key="process_pdfs1"):
            with st.spinner("Procesando archivos CTL 1..."):
                df_ctl1_list = []
                for file in uploaded_files_ctl1:
                    file.seek(0)  # Reinicia el puntero del archivo
                    try:
                        # Llamar a la función para extraer datos
                        datos_pdf = pdf_extractor1.extraer_datos_pdf(BytesIO(file.read()))
                        # Convertir el diccionario a DataFrame
                        df_ctl1 = pd.DataFrame([datos_pdf])  # Convertir el dict en un DataFrame
                        df_ctl1['Archivo'] = file.name  # Añadir nombre del archivo
                        df_ctl1_list.append(df_ctl1)  # Agregar a la lista
                    except Exception as e:
                        st.error(f"Error procesando {file.name}: {e}")
                
                if df_ctl1_list:
                    # Concatenar todos los DataFrames en uno solo
                    df_ctl1_combined = pd.concat(df_ctl1_list, ignore_index=True)

                    # Modificar la columna 'Tipo de Predio' para mostrar solo el primer carácter
                    if 'Tipo de Predio' in df_ctl1_combined.columns:
                        df_ctl1_combined['Tipo de Predio'] = df_ctl1_combined['Tipo de Predio'].str[0]

                    # Convertir columnas relevantes a numéricas
                    if "Area de terreno Metros" in df_ctl1_combined.columns:
                        df_ctl1_combined['Area de terreno Metros'] = pd.to_numeric(df_ctl1_combined['Area de terreno Metros'], errors='coerce')

                    if "Coeficiente" in df_ctl1_combined.columns:
                        df_ctl1_combined['Coeficiente'] = pd.to_numeric(df_ctl1_combined['Coeficiente'], errors='coerce')

                    # Guardar DataFrame en el estado de sesión
                    st.session_state["ctl1_data"] = df_ctl1_combined

                    # Cálculo de métricas
                    num_matriculas = df_ctl1_combined['N° Matrícula Inmobiliaría'].nunique()
                    direccion_actual = df_ctl1_combined['Dirección Actual del Inmueble'].nunique()
                    estado_folio = df_ctl1_combined['Estado Folio'].nunique()
                    tipo_predio = df_ctl1_combined['Tipo de Predio'].nunique()
                    area_terreno = df_ctl1_combined['Area de terreno Metros'].sum()
                    coeficiente = df_ctl1_combined['Coeficiente'].sum()

                    # Guardar métricas en el estado de sesión
                    st.session_state["ctl1_metrics"] = {
                        "Matrículas": num_matriculas,
                        "Dirección Actual": direccion_actual,
                        "Estado Folio": estado_folio,
                        "Tipo de Predio": tipo_predio,
                        "Área de Terreno (M2)": area_terreno,
                        "Coeficiente (Suma)": coeficiente
                    }

        # Mostrar el DataFrame procesado si está en session_state
        if "ctl1_data" in st.session_state:
            st.markdown("### Datos Procesados (CTL 1)")
            st.dataframe(st.session_state["ctl1_data"], use_container_width=True)

        # Mostrar métricas si están disponibles
        if "ctl1_metrics" in st.session_state:
            #st.markdown("### Métricas del Análisis")
            metrics = st.session_state["ctl1_metrics"]
            col1, col2, col3 = st.columns(3)

            col1.markdown(format_metric_with_hover(
                "Matrículas",
                metrics["Matrículas"],
                st.session_state["ctl1_data"]['N° Matrícula Inmobiliaría'].value_counts()
            ), unsafe_allow_html=True)

            col2.markdown(format_metric_with_hover(
                "Dirección Actual",
                metrics["Dirección Actual"],
                st.session_state["ctl1_data"]['Dirección Actual del Inmueble'].value_counts()
            ), unsafe_allow_html=True)

            col3.markdown(format_metric_with_hover(
                "Estado Folio",
                metrics["Estado Folio"],
                st.session_state["ctl1_data"]['Estado Folio'].value_counts()
            ), unsafe_allow_html=True)

            col4, col5, col6 = st.columns(3)

            col4.markdown(format_metric_with_hover(
                "Tipo de Predio",
                metrics["Tipo de Predio"],
                st.session_state["ctl1_data"]['Tipo de Predio'].value_counts()
            ), unsafe_allow_html=True)

            col5.markdown(format_metric_with_hover(
                "Área de Terreno (M2)",
                f"{metrics['Área de Terreno (M2)']:.0f}",
                pd.Series([metrics["Área de Terreno (M2)"]])
            ), unsafe_allow_html=True)

            col6.markdown(format_metric_with_hover(
                "Coeficiente (Suma)",
                f"{metrics['Coeficiente (Suma)']:.2f}",
                pd.Series([metrics["Coeficiente (Suma)"]])
            ), unsafe_allow_html=True)

        # Botón para realizar el análisis de propiedades horizontales
        if st.button("Análisis de Propiedades Horizontales", key="process_hor"):
            if "ctl1_data" in st.session_state:
                with st.spinner("Analizando propiedades horizontales..."):
                    try:
                        # Aplicar la función para calcular la columna 'Propiedad_Horizontal'
                        st.session_state["ctl1_data"]['Propiedad_Horizontal'] = st.session_state["ctl1_data"][
                            'Dirección Actual del Inmueble'
                        ].apply(prop_horizontal.es_propiedad_horizontal)

                        # Cálculo de métricas
                        num_propiedades_horizontales = st.session_state["ctl1_data"][
                            'Propiedad_Horizontal'
                        ].sum()  # Contar las propiedades horizontales (True)

                        # Actualizar métricas en el estado de sesión
                        st.session_state["ctl1_metrics"]["Propiedades Horizontales"] = num_propiedades_horizontales

                        st.success("¡Análisis de propiedades horizontales completado!")

                    except Exception as e:
                        st.error(f"Error en el análisis: {e}")

        # Mostrar métricas actualizadas si están disponibles
        if "ctl1_metrics" in st.session_state:
            #st.markdown("### Métricas Actualizadas")
            metrics = st.session_state["ctl1_metrics"]

            col1, col2, col3 = st.columns(3)

            col1.markdown(format_metric_with_hover(
                "Matrículas",
                metrics["Matrículas"],
                st.session_state["ctl1_data"]['N° Matrícula Inmobiliaría'].value_counts()
            ), unsafe_allow_html=True)

            col2.markdown(format_metric_with_hover(
                "Propiedades Horizontales",
                metrics.get("Propiedades Horizontales", 0),
                st.session_state["ctl1_data"]['Propiedad_Horizontal'].value_counts()
                if 'Propiedad_Horizontal' in st.session_state["ctl1_data"] else pd.Series([])
            ), unsafe_allow_html=True)

            col3.markdown(format_metric_with_hover(
                "Coeficiente (Suma)",
                f"{metrics['Coeficiente (Suma)']:.2f}",
                pd.Series([metrics['Coeficiente (Suma)']])
            ), unsafe_allow_html=True)
        
        # Botón para realizar el análisis de áreas
        if st.button("Análisis de Áreas", key="process_areas"):
            if "ctl1_data" in st.session_state:
                with st.spinner("Procesando áreas..."):
                    try:
                        # Aplicar el análisis de áreas
                        st.session_state["ctl1_data"]['Areas_Procesadas'] = areas_cabida.process_areas(
                            st.session_state["ctl1_data"]['Cabidad y Linderos']
                        )

                        # Crear columna 'Area_definitiva'
                        st.session_state["ctl1_data"]['Area_definitiva'] = st.session_state["ctl1_data"][
                            'Areas_Procesadas'
                        ].apply(lambda x: x[0] if isinstance(x, list) and x else None)

                        # Identificar la Matrícula Matriz
                        if "Matrícula(s) Matriz" in st.session_state["ctl1_data"].columns:
                            matricula_matriz = (
                                st.session_state["ctl1_data"]['Matrícula(s) Matriz']
                                .mode()
                                .iloc[0]
                                if not st.session_state["ctl1_data"]['Matrícula(s) Matriz'].isnull().all()
                                else None
                            )
                        else:
                            matricula_matriz = None

                        # Calcular métricas relacionadas con áreas
                        if matricula_matriz:
                            area_matriz = st.session_state["ctl1_data"].loc[
                                st.session_state["ctl1_data"]['N° Matrícula Inmobiliaría'] == matricula_matriz,
                                'Area_definitiva'
                            ].sum()

                            suma_areas_resto = st.session_state["ctl1_data"].loc[
                                st.session_state["ctl1_data"]['N° Matrícula Inmobiliaría'] != matricula_matriz,
                                'Area_definitiva'
                            ].sum()

                            porcentaje_area = (area_matriz / suma_areas_resto) * 100 if suma_areas_resto else None

                        else:
                            area_matriz = None
                            suma_areas_resto = st.session_state["ctl1_data"]['Area_definitiva'].sum()
                            porcentaje_area = None

                        # Guardar métricas en el estado de sesión
                        st.session_state["area_metrics"] = {
                            "Matrícula Matriz": matricula_matriz if matricula_matriz else "No disponible",
                            "Área Matrícula Matriz": area_matriz if area_matriz else 0,
                            "Suma Áreas (Resto)": suma_areas_resto,
                            "Porcentaje Área (Matriz/Resto)": f"{porcentaje_area:.2f}%" if porcentaje_area else "No disponible"
                        }

                        st.success("¡Análisis de áreas completado!")

                    except Exception as e:
                        st.error(f"Error procesando áreas: {e}")

        # Mostrar las métricas del análisis de áreas si existen
        if "area_metrics" in st.session_state:
            st.markdown("### Métricas del Análisis de Áreas")
            metrics = st.session_state["area_metrics"]

            col1, col2, col3, col4 = st.columns(4)

            # Mostrar las métricas en el formato deseado
            col1.markdown(format_metric_with_hover(
                "Matrícula Matriz",
                metrics["Matrícula Matriz"],
                pd.Series([metrics["Matrícula Matriz"]])
            ), unsafe_allow_html=True)

            col2.markdown(format_metric_with_hover(
                "Área Matrícula Matriz",
                f"{metrics['Área Matrícula Matriz']:.0f}",
                pd.Series([metrics["Área Matrícula Matriz"]])
            ), unsafe_allow_html=True)

            col3.markdown(format_metric_with_hover(
                "Suma Áreas (Resto)",
                f"{metrics['Suma Áreas (Resto)']:.0f}",
                pd.Series([metrics["Suma Áreas (Resto)"]])
            ), unsafe_allow_html=True)

            col4.markdown(format_metric_with_hover(
                "Porcentaje Área (Matriz/Resto)",
                metrics["Porcentaje Área (Matriz/Resto)"],
                pd.Series([metrics["Porcentaje Área (Matriz/Resto)"]])
            ), unsafe_allow_html=True)

            # Mostrar un comentario si no se encontró la matrícula matriz
            if not st.session_state["area_metrics"]["Matrícula Matriz"]:
                st.info("Nota: La Matrícula Matriz no se encuentra en los datos procesados.")

with tabs[3]:  # 4 - Análisis múltiple CTL 2
    st.title("Análisis múltiple de documentos PDF (CTL 2)")

    # Subir múltiples archivos PDF
    uploaded_files_ctl2 = st.file_uploader(
        "Selecciona múltiples archivos PDF para el análisis CTL 2",
        type="pdf",
        accept_multiple_files=True,
        key="file_uploader_ctl2"
    )

    # Crear una lista para las rutas válidas
    pdf_paths = []

    if uploaded_files_ctl2:
        temp_dir = tempfile.mkdtemp()  # Crear un directorio temporal
        for uploaded_file in uploaded_files_ctl2:
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            pdf_paths.append(temp_path)

        # Botón para procesar las anotaciones
        if st.button("Procesar Anotaciones CTL 2", key="process_annotations2"):
            with st.spinner("Procesando anotaciones de los archivos PDF..."):
                try:
                    # Extraer anotaciones
                    df_annot = annotations2.extract_annotations_from_pdfs(pdf_paths)

                    # Extraer detalles del 'Doc'
                    if 'Doc' in df_annot.columns:
                        df_annot['Doc_val'] = df_annot['Doc'].apply(annotations2.extract_monetary_value)
                        doc_details_df = df_annot['Doc'].apply(annotations2.extract_doc_details).apply(pd.Series)
                        df_annot = pd.concat([df_annot, doc_details_df], axis=1)

                    # Extraer detalles adicionales de la 'Especificacion'
                    if 'Especificacion' in df_annot.columns:
                        especificacion_details_df = df_annot['Especificacion'].apply(
                            annotations2.extract_especificacion_details
                        ).apply(pd.Series)
                        df_annot = pd.concat([df_annot, especificacion_details_df], axis=1)

                        df_annot['cod_descripcion'] = df_annot['Especificacion'].apply(
                            lambda x: re.split(r'\s*\(', x)[0] if pd.notna(x) else None
                        )
                        df_annot['modo_adquisicion'] = df_annot['Especificacion'].apply(
                            lambda x: re.search(r'\((.*?)\)', x).group(1)
                            if pd.notna(x) and re.search(r'\((.*?)\)', x)
                            else None
                        )
                        df_annot['codigo'] = df_annot['cod_descripcion'].apply(
                            lambda x: re.match(r'(\d+)', x).group(1)
                            if pd.notna(x) and re.match(r'(\d+)', x)
                            else None
                        )
                        df_annot['Especificacion_area'] = df_annot['Especificacion'].apply(
                            annotations2.extract_area_from_especificacion
                        )

                    # Crear la columna 'Titular'
                    if 'Personas que intervienen en el acto' in df_annot.columns:
                        df_annot['Titular'] = df_annot['Personas que intervienen en el acto'].apply(
                            lambda x: re.search(r'\b([A-Z])\b$', x).group(1)
                            if pd.notna(x) and re.search(r'\b([A-Z])\b$', x)
                            else None
                        )

                    # Guardar en session_state
                    st.session_state["ctl2_annotations"] = df_annot

                    # Mostrar DataFrame procesado
                    st.markdown("### Anotaciones Procesadas")
                    st.dataframe(df_annot, use_container_width=True)

                    st.success("¡Procesamiento completado!")

                except Exception as e:
                    st.error(f"Error durante el procesamiento de anotaciones: {e}")

        # Botón para mostrar resumen y métricas
        if st.button("Resumen y Métricas"):
            with st.spinner("Calculando resumen y métricas..."):
                try:
                    df_annot = st.session_state["ctl2_annotations"]
                    df_annot['Fecha'] = pd.to_datetime(df_annot['Fecha'], format='%d-%m-%Y', errors='coerce')

                    # Agrupar datos por folio
                    df_grouped = df_annot.groupby('folio').agg({
                        'Especificacion_area': 'sum',
                        'Especificacion_area2': 'sum',
                        'Nro de anotacion': 'count',
                        'Fecha': ['min', 'max']
                    }).reset_index()
                    df_grouped.columns = ['folio', 'Total_Especificacion_area', 'Total_Especificacion_area2',
                                          'Anotaciones_count', 'Fecha_mas_antigua', 'Fecha_mas_reciente']
                    df_grouped['Total_area'] = (
                        df_grouped['Total_Especificacion_area'] + df_grouped['Total_Especificacion_area2']
                    )

                    # Guardar en session_state
                    st.session_state["ctl2_grouped"] = df_grouped

                    # Mostrar métricas
                    st.markdown("### Resumen de Métricas")
                    total_folios = len(df_grouped['folio'].unique())
                    total_anotaciones = df_grouped['Anotaciones_count'].sum()
                    total_area = df_grouped['Total_area'].sum()

                    col1, col2, col3 = st.columns(3)

                    # Cantidad de Folios
                    col1.markdown(format_metric_with_hover(
                        "Cantidad de Folios",
                        total_folios,
                        df_grouped['folio'].value_counts()
                    ), unsafe_allow_html=True)

                    # Cantidad de Anotaciones
                    col2.markdown(format_metric_with_hover(
                        "Cantidad de Anotaciones",
                        total_anotaciones,
                        df_annot['Nro de anotacion'].value_counts()
                    ), unsafe_allow_html=True)

                    # Total Área
                    col3.markdown(format_metric_with_hover(
                        "Total Área",
                        f"{total_area:.2f}",
                        df_grouped['Total_area'].value_counts()
                    ), unsafe_allow_html=True)

                    # Mostrar resumen agrupado
                    st.markdown("### Resumen Agrupado")
                    st.dataframe(df_grouped, use_container_width=True)

                    # Gráfica de barras interactiva
                    st.markdown("### Gráfica de Folios por Total Área")
                    chart_data = df_grouped.sort_values('Total_area', ascending=False)
                    fig = px.bar(
                        chart_data,
                        x='folio',
                        y='Total_area',
                        title='Folios por Total Área',
                        labels={'folio': 'Folio', 'Total_area': 'Total Área'},
                        text='Total_area'
                    )
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Error en el cálculo de métricas: {e}")
