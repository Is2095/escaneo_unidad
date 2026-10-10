def registrar_error(errores, ruta, error):
    """Registra un error sin repetir la misma ruta y mensaje."""

    if errores is None:
        return

    registro = {
        "ruta": ruta,
        "error": str(error),
    }

    if registro not in errores:
        errores.append(registro)
