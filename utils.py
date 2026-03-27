import os
import zipfile
import wget
import shutil  # <-- Necesario para borrar carpetas enteras
from unidecode import unidecode
import matplotlib.pyplot as plt
import contextily as ctx


# -----------------------------------------------------------------------------------------------


def descargar_recurso(url, nombre_archivo=None, carpeta="datasets"):

    error = False
    formatos_protegidos = (
    '.ods', '.odt', '.odp', '.odg',        # OpenDocument
    '.xlsx', '.xlsm', '.xltx', '.xltm',    # Excel
    '.docx', '.docm', '.dotx',             # Word
    '.pptx', '.pptm', '.potx',             # PowerPoint
    '.kmz',                                # Google Earth
    '.epub'                                # E-books
)

    # Si no se pasa un nombre, dejamos que wget lo deduzca de la URL
    if nombre_archivo is None:
        nombre_archivo = wget.filename_from_url(url)
    
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    
    # --- Descarga directa (eliminamos la verificación de si el archivo existe) ---
    print(f"Descargando: {nombre_archivo}...")
    try:
        # wget descarga en la ruta especificada
        archivo_descargado = wget.download(url, out=ruta_completa)
        
        # --- COMPROBACIÓN ESTRUCTURAL DEL ZIP ---
        
        if zipfile.is_zipfile(archivo_descargado) and not archivo_descargado.lower().endswith(formatos_protegidos):
            with zipfile.ZipFile(archivo_descargado, 'r') as zip_ref:
                zip_ref.extractall(carpeta)
            
            os.remove(archivo_descargado)
            
        print(f"✅ {nombre_archivo} guardado.\n")

    except Exception as e:
        print(f"❌ Error con {nombre_archivo}: {e}\n")
        error = True
    
    return ruta_completa, error



# -----------------------------------------------------------------------------------------------



def descargar_datasets(datasets = "All", carpeta="datasets"):
    """
    Descarga los datasets necesarios para el proyecto.

    Args:
        datasets (str o list): Lista de datasets a descargar. Por defecto, "All" (todos).
        carpeta (str): Carpeta donde se descargan los datasets. Por defecto, "datasets". Dentro 
                       de esta carpeta se crearan subcarpetas con los nombres de los datasets
                       y dentro de estas se guardaran los archivos correspondientes.
    """

    dict_datasets = {
        "siniestros": ["https://ckan-data.montevideo.gub.uy/dataset/d8b39296-5fcf-4a8e-ac9f-d02a24698b97/resource/f1157e84-9577-4d8f-b2f3-92c1d720ae93/download/siniestros2022.csv", "https://ckan-data.montevideo.gub.uy/dataset/d8b39296-5fcf-4a8e-ac9f-d02a24698b97/resource/e26fc1e0-63d7-4d94-9321-31a2e0080c37/download/metadata-siniestros.txt"],
        "viajes": ["https://ckan-data.montevideo.gub.uy/dataset/1205fc5c-b1b5-4478-b43e-c7411949ff15/resource/17b4b443-274d-420c-9ae6-8cff56647294/download/viajes_stm_092022.zip", "https://ckan-data.montevideo.gub.uy/dataset/1205fc5c-b1b5-4478-b43e-c7411949ff15/resource/83bc8b63-553e-4cc4-9061-d4a9b1e04f56/download/descripcion_de_los_atributos-1.ods"],
        "paradas": ["http://intgis.montevideo.gub.uy/sit/tmp/v_uptu_paradas.zip"]
    }
# https://imnube.montevideo.gub.uy/share/s/u0u-R-HUTN2ws0st23-2ow
    algun_error = False
    if datasets == "All":
        datasets = dict_datasets.keys()
    elif isinstance(datasets, str):
        datasets = [datasets]

    for dataset in datasets:
        if dataset not in dict_datasets:
            print(f"Error: El dataset '{dataset}' no es válido. Las opciones válidas son: {list(dict_datasets.keys())}")
            return  


    for dataset in datasets:

        subcarpeta = os.path.join(carpeta, dataset)

        if os.path.exists(subcarpeta):
            # print(f"🧹 Limpiando carpeta existente: {subcarpeta}...")
            shutil.rmtree(subcarpeta) # Borra la carpeta y todo lo que tenga adentro
        os.makedirs(subcarpeta) # La crea de nuevo, totalmente vacía

        for url in dict_datasets[dataset]:
            _, error = descargar_recurso(url, carpeta=subcarpeta)
            algun_error = algun_error or error

    if algun_error:
        print("\nHubo errores al descargar uno o más datasets.")
    else:
        print("\nLos datasets se encuentran disponibles en la ruta: ", os.path.join(os.getcwd(), carpeta)) 



# -----------------------------------------------------------------------------------------------



def corregir_tildes(dataframe):

    df=dataframe.copy()

    # 1. Corregir los encabezados
    df.columns = [unidecode(col).strip().lower() for col in df.columns]


    # 2. Sacar tildes a los datos (solo columnas con texto)
    df = df.map(lambda x: unidecode(str(x)) if isinstance(x, str) else x)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: unidecode(x) if isinstance(x, str) else x)
    
    return df



# -----------------------------------------------------------------------------------------------



def graficar_sobre_mapa(gdf, titulo="Mapa de colisiones", color='blue', save=False):
    """
    Toma un GeoDataFrame (gdf) y lo grafica sobre un mapa base usando contextily.
    """
    # 1. Para que el mapa de fondo (contextily) encaje perfecto, necesita estar en Web Mercator (3857).
    # Usamos to_crs para asegurar la proyección, creando una copia temporal para el mapa
    # sin alterar el gdf original que le pasaste a la función.
    gdf_proyectado = gdf.copy().to_crs(epsg=3857)

    # Graficamos
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf_proyectado.plot(ax=ax, alpha=0.5, markersize=10, color=color)

    # Agregamos el mapa de fondo
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    # Detalles
    plt.title(titulo, fontsize=15)
    ax.set_axis_off() 
    if save:
        plt.savefig(f"{titulo}.pdf")
        
    plt.show()
    
    return fig, ax