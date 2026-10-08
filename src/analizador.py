from src.escaneo import escanear_directorio
from src.clasificador import clasificar_archivos


def analizar_unidad(ruta):
    """
    Escanea una unidad o directorio y clasifica sus archivos.

    No modifica archivos ni directorios de origen.
    """

    resultado_escaneo = escanear_directorio(ruta)

    archivos_por_categoria = clasificar_archivos(
        resultado_escaneo["archivos"]
    )

    cantidad_archivos = len(resultado_escaneo["archivos"])
    cantidad_directorios = len(resultado_escaneo["directorios"])

    cantidades_por_categoria = {
        categoria: len(archivos)
        for categoria, archivos in archivos_por_categoria.items()
    }

    return {
        "ruta_analizada": str(ruta),
        "directorios": resultado_escaneo["directorios"],
        "archivos": resultado_escaneo["archivos"],
        "errores": resultado_escaneo["errores"],
        "archivos_por_categoria": archivos_por_categoria,
        "cantidades_por_categoria": cantidades_por_categoria,
        "total_directorios": cantidad_directorios,
        "total_archivos": cantidad_archivos,
    }