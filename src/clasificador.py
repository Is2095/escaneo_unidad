from pathlib import Path


EXTENSIONES_FOTOGRAFIAS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tif",
    ".tiff",
}

EXTENSIONES_VIDEOS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".wmv",
    ".3gp",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".mts",
    ".m2ts",
}

EXTENSIONES_AUDIO = {
    ".mp3",
    ".wav",
    ".flac",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
}

EXTENSIONES_DOCUMENTOS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".rtf",
    ".odt",
}

EXTENSIONES_HOJAS_CALCULO = {
    ".xls",
    ".xlsx",
    ".csv",
    ".ods",
}

EXTENSIONES_PRESENTACIONES = {
    ".ppt",
    ".pptx",
    ".odp",
}

EXTENSIONES_COMPRIMIDOS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
}

EXTENSIONES_BASES_DATOS = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".mdb",
    ".accdb",
}


ARCHIVOS_SISTEMA = {
    "thumbs.db",
    "desktop.ini",
    ".ds_store",
}


def clasificar_archivo(ruta):
    """
    Clasifica un archivo según su nombre y extensión.

    No modifica ni abre el archivo.
    """

    ruta = Path(ruta)

    nombre = ruta.name.lower()

    if nombre in ARCHIVOS_SISTEMA:
        return "sistema"

    extension = ruta.suffix.lower()

    if extension in EXTENSIONES_FOTOGRAFIAS:
        return "fotografias"

    if extension in EXTENSIONES_VIDEOS:
        return "videos"

    if extension in EXTENSIONES_AUDIO:
        return "audio"

    if extension in EXTENSIONES_DOCUMENTOS:
        return "documentos"

    if extension in EXTENSIONES_HOJAS_CALCULO:
        return "hojas_calculo"

    if extension in EXTENSIONES_PRESENTACIONES:
        return "presentaciones"

    if extension in EXTENSIONES_COMPRIMIDOS:
        return "comprimidos"

    if extension in EXTENSIONES_BASES_DATOS:
        return "bases_datos"

    return "otros"