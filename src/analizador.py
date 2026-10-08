from src.escaneo import escanear_directorio
from src.clasificador import clasificar_archivos

from pathlib import Path

from src.escaneo import escanear_directorio
from src.clasificador import clasificar_archivos

def analizar_unidad(ruta):
    """
    Escanea una unidad o directorio y clasifica sus archivos.

    Calcula el tamaño de los archivos sin abrir su contenido.
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

    tamanos_por_categoria = {
        categoria: 0
        for categoria in archivos_por_categoria
    }

    errores = list(resultado_escaneo["errores"])
    tamano_total_bytes = 0

    for categoria, archivos in archivos_por_categoria.items():
        for archivo in archivos:
            try:
                tamano = archivo.stat().st_size

            except OSError as error:
                errores.append(
                    {
                        "ruta": archivo,
                        "error": str(error),
                    }
                )
                continue

            tamanos_por_categoria[categoria] += tamano
            tamano_total_bytes += tamano

    return {
        "ruta_analizada": str(ruta),
        "directorios": resultado_escaneo["directorios"],
        "archivos": resultado_escaneo["archivos"],
        "errores": errores,
        "archivos_por_categoria": archivos_por_categoria,
        "cantidades_por_categoria": cantidades_por_categoria,
        "total_directorios": cantidad_directorios,
        "total_archivos": cantidad_archivos,
        "tamano_total_bytes": tamano_total_bytes,
        "tamanos_por_categoria_bytes": tamanos_por_categoria,
    }