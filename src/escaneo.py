import os
from pathlib import Path


def escanear_directorio(ruta):
    """
    Recorre recursivamente un directorio y devuelve
    las rutas de los directorios, archivos y errores encontrados.

    No modifica ningún archivo ni directorio.
    """

    ruta = Path(ruta)

    if not ruta.exists():
        raise ValueError(f"La ruta indicada no existe: {ruta}")

    if not ruta.is_dir():
        raise ValueError(f"La ruta indicada no es un directorio: {ruta}")

    directorios = []
    archivos = []
    errores = []

    def manejar_error(error):
        errores.append(
            {
                "ruta": Path(error.filename) if error.filename else None,
                "error": str(error),
            }
        )

    for directorio_actual, nombres_directorios, nombres_archivos in os.walk(
        ruta,
        topdown=True,
        onerror=manejar_error,
        followlinks=False
    ):
        directorio_actual = Path(directorio_actual)

        for nombre_directorio in nombres_directorios:
            directorios.append(directorio_actual / nombre_directorio)

        for nombre_archivo in nombres_archivos:
            archivos.append(directorio_actual / nombre_archivo)

    return {
        "directorios": directorios,
        "archivos": archivos,
        "errores": errores,
    }