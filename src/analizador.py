from src.escaneo import escanear_directorio
from src.clasificador import clasificar_archivos
from src.duplicados import encontrar_duplicados
from src.errores import registrar_error


def analizar_unidad(ruta):
    """
    Escanea una unidad o directorio y clasifica sus archivos.

    Calcula el tamaño de los archivos sin abrir su contenido.
    Cuenta los archivos y subdirectorios directos de cada carpeta.
    No modifica archivos ni directorios de origen.
    """

    resultado_escaneo = escanear_directorio(ruta)

    errores = list(resultado_escaneo["errores"])

    archivos_por_categoria = clasificar_archivos(
        resultado_escaneo["archivos"]
    )

    cantidad_archivos = len(resultado_escaneo["archivos"])

    grupos_duplicados = encontrar_duplicados(
        resultado_escaneo["archivos"],
        errores=errores,
    )

    cantidad_grupos_duplicados = len(grupos_duplicados)

    cantidad_archivos_duplicados = sum(
        len(grupo)
        for grupo in grupos_duplicados
    )

    cantidad_directorios = len(resultado_escaneo["directorios"])

    espacio_duplicado_bytes = 0

    for grupo in grupos_duplicados:
        try:
            tamano = grupo[0].stat().st_size

        except OSError as error:
            registrar_error(errores, grupo[0], error)
            continue

        espacio_duplicado_bytes += tamano * (len(grupo) - 1)

    detalle_directorios = {}

    for directorio in resultado_escaneo["directorios"]:
        try:
            elementos = list(directorio.iterdir())

            archivos_directos = 0
            subdirectorios_directos = 0

            for elemento in elementos:
                try:
                    if elemento.is_file():
                        archivos_directos += 1
                    elif elemento.is_dir():
                        subdirectorios_directos += 1

                except OSError as error:
                    registrar_error(errores, elemento, error)

            detalle_directorios[directorio] = {
                "archivos": archivos_directos,
                "subdirectorios": subdirectorios_directos,
            }

        except OSError as error:
            registrar_error(errores, directorio, error)

    cantidades_por_categoria = {
        categoria: len(archivos)
        for categoria, archivos in archivos_por_categoria.items()
    }

    tamanos_por_categoria = {
        categoria: 0
        for categoria in archivos_por_categoria
    }

    tamano_total_bytes = 0
    detalle_archivos = []

    for categoria, archivos in archivos_por_categoria.items():
        for archivo in archivos:
            detalle = {
                "ruta": archivo,
                "nombre": archivo.name,
                "extension": archivo.suffix.lower(),
                "directorio": archivo.parent,
                "tamano_bytes": None,
                "categoria": categoria,
            }

            try:
                tamano = archivo.stat().st_size

            except OSError as error:
                registrar_error(errores, archivo, error)

                detalle_archivos.append(detalle)
                continue

            detalle["tamano_bytes"] = tamano
            detalle_archivos.append(detalle)

            tamanos_por_categoria[categoria] += tamano
            tamano_total_bytes += tamano
    
    inventario_por_tamano = sorted(
        detalle_archivos,
        key=lambda archivo: (
            archivo["tamano_bytes"] is not None,
            archivo["tamano_bytes"] or 0,
        ),
        reverse=True,
    )

    return {
        "ruta_analizada": str(ruta),
        "directorios": resultado_escaneo["directorios"],
        "detalle_directorios": detalle_directorios,
        "archivos": resultado_escaneo["archivos"],
        "detalle_archivos": detalle_archivos,
        "inventario_por_tamano": inventario_por_tamano,
        "errores": errores,
        "archivos_por_categoria": archivos_por_categoria,
        "cantidades_por_categoria": cantidades_por_categoria,
        "total_directorios": cantidad_directorios,
        "total_archivos": cantidad_archivos,
        "tamano_total_bytes": tamano_total_bytes,
        "tamanos_por_categoria_bytes": tamanos_por_categoria,
        "grupos_duplicados": grupos_duplicados,
        "cantidad_grupos_duplicados": cantidad_grupos_duplicados,
        "cantidad_archivos_duplicados": cantidad_archivos_duplicados,
        "espacio_duplicado_bytes": espacio_duplicado_bytes,
    }
