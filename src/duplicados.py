import hashlib
from collections import defaultdict
from src.errores import registrar_error


def calcular_sha256(ruta, tamano_bloque=1024 * 1024):
    """
    Calcula el hash SHA-256 de un archivo leyendo por bloques.

    No modifica el archivo original.
    """

    hash_sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:
        while True:
            bloque = archivo.read(tamano_bloque)

            if not bloque:
                break

            hash_sha256.update(bloque)

    return hash_sha256.hexdigest()


def encontrar_duplicados(archivos, errores=None):
    """
    Encuentra grupos de archivos con contenido idéntico.

    Primero agrupa por tamaño y después compara sus hashes SHA-256.
    Devuelve una lista de grupos, cada uno con las rutas de los
    archivos duplicados.

    Registra los errores de acceso cuando se proporciona una lista
    de errores. No modifica, elimina ni mueve archivos.
    """

    archivos_por_tamano = defaultdict(list)

    for archivo in archivos:
        try:
            tamano = archivo.stat().st_size

        except OSError as error:
            registrar_error(errores, archivo, error)
            continue

        archivos_por_tamano[tamano].append(archivo)

    grupos_por_hash = defaultdict(list)

    for archivos_mismo_tamano in archivos_por_tamano.values():
        if len(archivos_mismo_tamano) < 2:
            continue

        for archivo in archivos_mismo_tamano:
            try:
                tamano_actual = archivo.stat().st_size
                hash_archivo = calcular_sha256(archivo)

            except OSError as error:
                registrar_error(errores, archivo, error)
                continue

            grupos_por_hash[
                (tamano_actual, hash_archivo)
            ].append(archivo)

    return [
        grupo
        for grupo in grupos_por_hash.values()
        if len(grupo) > 1
    ]
