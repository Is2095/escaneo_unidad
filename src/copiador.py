
import os
import shutil
from pathlib import Path
import tempfile
import hashlib

from src.errores import registrar_error

TAMANO_MAXIMO_FAT32 = 4_294_967_295


def calcular_sha256(archivo):
    """
    Calcula el hash SHA-256 de un archivo sin cargarlo
    completo en memoria.

    Lee el archivo por bloques para poder procesar archivos grandes.
    No modifica el archivo.
    """

    sha256 = hashlib.sha256()

    with Path(archivo).open("rb") as entrada:
        for bloque in iter(lambda: entrada.read(1024 * 1024), b""):
            sha256.update(bloque)

    return sha256.hexdigest()


def seleccionar_archivo_a_conservar(grupo, errores=None):
    """
    Selecciona el archivo más antiguo de un grupo de duplicados.

    Prioriza la fecha de creación; después, la fecha de última
    modificación y, finalmente, la ruta alfabética.

    Si no se pueden consultar las fechas de algún archivo,
    registra el error y devuelve None.

    No modifica los archivos originales.
    """

    candidatos = []

    for archivo in grupo:
        try:
            informacion = archivo.stat()

        except OSError as error:
            registrar_error(errores, archivo, error)
            return None

        candidatos.append(
            (
                informacion.st_ctime,
                informacion.st_mtime,
                str(archivo).casefold(),
                archivo,
            )
        )

    if not candidatos:
        return None

    candidatos.sort(key=lambda candidato: candidato[:3])

    return candidatos[0][3]


def copiar_sin_duplicados(origen, destino, grupos_duplicados):
    """
    Copia el contenido del origen al destino sin duplicados exactos.

    Mantiene toda la estructura de carpetas, incluidas las vacías.
    No modifica el origen ni sobrescribe archivos del destino.

    Devuelve un resumen de la operación.
    """

    origen = Path(origen).resolve()
    destino = Path(destino).resolve()

    resultado = {
        "archivos_copiados": 0,
        "archivos_verificados": 0,
        "archivos_omitidos_duplicados": 0,
        "errores": [],
        "copia_completa": True,
    }
    if not origen.is_dir():
        raise ValueError(f"El origen no es un directorio válido: {origen}")


    # Impide que origen y destino sean iguales o que uno
    # esté dentro del otro. Así evitamos copiar sobre el origen
    # o incluir el origen dentro del destino.
    if (
        destino == origen
        or origen in destino.parents
        or destino in origen.parents
    ):
        raise ValueError(
            "El destino y el origen no pueden contenerse entre sí."
        )

    if destino.exists():
        raise FileExistsError(
            f"El destino ya existe y no se modificará: {destino}"
        )

    # Determina qué rutas se conservarán y cuáles se omitirán.
    rutas_duplicadas = set()

    for grupo in grupos_duplicados:
        conservado = seleccionar_archivo_a_conservar(
            grupo,
            errores=resultado["errores"],
        )

        if conservado is None:
            # No elegimos un ganador si no se pudieron consultar
            # las fechas. Por seguridad, omitimos todo el grupo.
            rutas_duplicadas.update(
                Path(archivo).resolve() for archivo in grupo
            )
            continue

        for archivo in grupo:
            ruta = Path(archivo).resolve()

            if ruta != conservado.resolve():
                rutas_duplicadas.add(ruta)


    # Registra errores al recorrer carpetas inaccesibles.
    def registrar_error_recorrido(error):
        resultado["copia_completa"] = False

        registrar_error(
            resultado["errores"],
            getattr(error, "filename", None) or origen,
            error,
        )

    # Crea todas las carpetas, incluidas las que queden vacías.
    try:
        for directorio, subdirectorios, archivos in os.walk(
            origen,
            followlinks=False,
            onerror=registrar_error_recorrido,
        ):

            ruta_directorio = Path(directorio)
            ruta_relativa = ruta_directorio.relative_to(origen)
            destino_directorio = destino / ruta_relativa

            try:
                destino_directorio.mkdir(
                    parents=True,
                    exist_ok=True,
                )
            except OSError as error:
                resultado["copia_completa"] = False

                registrar_error(
                    resultado["errores"],
                    destino_directorio,
                    error,
                )

                # No intentamos copiar archivos en una carpeta
                # que no se pudo crear.
                subdirectorios.clear()
                continue

            # No seguimos enlaces simbólicos a directorios.
            subdirectorios[:] = [
                nombre
                for nombre in subdirectorios
                if not (ruta_directorio / nombre).is_symlink()
            ]

            for nombre in archivos:
                archivo = ruta_directorio / nombre

                try:
                    if archivo.is_symlink():
                        registrar_error(
                            resultado["errores"],
                            archivo,
                            "Se omitió un enlace simbólico.",
                        )
                        continue


                    if archivo.resolve() in rutas_duplicadas:
                        resultado["archivos_omitidos_duplicados"] += 1
                        continue

                    try:
                        tamano_archivo = archivo.stat().st_size
                    except OSError as error:
                        registrar_error(
                            resultado["errores"],
                            archivo,
                            error,
                        )
                        continue

                    if tamano_archivo > TAMANO_MAXIMO_FAT32:
                        registrar_error(
                            resultado["errores"],
                            archivo,
                            (
                                "El archivo supera el límite de FAT32 "
                                "de 4 GiB menos 1 byte y se omitió."
                            ),
                        )
                        continue

                    archivo_destino = destino_directorio / nombre

                    archivo_temporal = None
                    destino_creado = False

                    try:
                        # Copia primero a un archivo temporal único.
                        with tempfile.NamedTemporaryFile(
                            mode="wb",
                            prefix=".copia_temporal_",
                            suffix=".tmp",
                            dir=destino_directorio,
                            delete=False,
                        ) as salida:
                            archivo_temporal = Path(salida.name)

                            with archivo.open("rb") as entrada:
                                shutil.copyfileobj(entrada, salida)

                            salida.flush()
                            os.fsync(salida.fileno())

                        # Conserva los metadatos antes de publicar.
                        shutil.copystat(
                            archivo,
                            archivo_temporal,
                            follow_symlinks=False,
                        )


                        # Crea el destino exclusivamente: nunca sobrescribe.
                        with archivo_destino.open("xb") as salida_final:
                            destino_creado = True

                            with archivo_temporal.open("rb") as entrada:
                                shutil.copyfileobj(entrada, salida_final)

                            salida_final.flush()
                            os.fsync(salida_final.fileno())

                        # Conserva los metadatos una vez cerrado el archivo.
                        shutil.copystat(
                            archivo,
                            archivo_destino,
                            follow_symlinks=False,
                        )

                        # Verifica el contenido después de cerrar la copia.
                        hash_original = calcular_sha256(archivo)
                        hash_copia = calcular_sha256(archivo_destino)

                        if hash_original != hash_copia:
                            raise OSError(
                                "La verificación SHA-256 falló: "
                                "el contenido de la copia no coincide "
                                "con el original."
                            )

                        resultado["archivos_verificados"] += 1
                        resultado["archivos_copiados"] += 1

                    except OSError:
                        # Si el destino quedó parcial, intenta eliminarlo.
                        if destino_creado:
                            try:
                                archivo_destino.unlink(missing_ok=True)
                            except OSError as error_limpieza:
                                registrar_error(
                                    resultado["errores"],
                                    archivo_destino,
                                    error_limpieza,
                                )

                        raise

                    finally:
                        # Limpia el temporal tanto en éxito como en error.
                        if archivo_temporal is not None:
                            try:
                                archivo_temporal.unlink(missing_ok=True)
                            except OSError as error_limpieza:
                                registrar_error(
                                    resultado["errores"],
                                    archivo_temporal,
                                    error_limpieza,
                                )


                except FileExistsError as error:
                    resultado["copia_completa"] = False
                    registrar_error(
                        resultado["errores"],
                        archivo_destino,
                        error,
                    )

                except OSError as error:
                    resultado["copia_completa"] = False
                    registrar_error(
                        resultado["errores"],
                        archivo,
                        error,
                    )

    except OSError as error:
        resultado["copia_completa"] = False
        registrar_error(
            resultado["errores"],
            origen,
            error,
        )


    # Si se registró cualquier incidencia, la operación no se
    # considera una copia completa sin incidencias.
    if resultado["errores"]:
        resultado["copia_completa"] = False

    resultado["origen"] = str(origen)
    resultado["destino"] = str(destino)

    return resultado
