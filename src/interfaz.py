
def formatear_tamano(tamano_bytes):
    """
    Convierte un tamaño en bytes a una unidad legible.

    Utiliza bytes, KB, MB, GB o TB según corresponda.
    """

    unidades = ["bytes", "KB", "MB", "GB", "TB"]
    tamano = float(tamano_bytes)

    for unidad in unidades:
        if tamano < 1024 or unidad == "TB":
            if unidad == "bytes":
                return f"{int(tamano)} bytes"

            return f"{tamano:.2f} {unidad}".replace(".", ",")

        tamano /= 1024

    return f"{tamano:.2f} TB".replace(".", ",")

def mostrar_resumen(resultado):
    """
    Muestra por pantalla el resumen de un análisis.

    No realiza el escaneo ni modifica archivos.
    """

    nombres_categorias = {
        "fotografias": "Fotografías",
        "videos": "Videos",
        "audio": "Audio",
        "documentos": "Documentos",
        "hojas_calculo": "Hojas de cálculo",
        "presentaciones": "Presentaciones",
        "comprimidos": "Comprimidos",
        "bases_datos": "Bases de datos",
        "sistema": "Sistema",
        "otros": "Otros",
    }

    print("=" * 50)
    print("             RESUMEN DEL ESCANEO")
    print("=" * 50)

    print(f"\nRuta analizada: {resultado['ruta_analizada']}")

    print(
        f"\nDirectorios encontrados: "
        f"{resultado['total_directorios']:,}".replace(",", ".")
    )

    print(
        f"Archivos encontrados:    "
        f"{resultado['total_archivos']:,}".replace(",", ".")
    )

    tamano_total_bytes = resultado["tamano_total_bytes"]

    print(
        f"Tamaño total de archivos: "
        f"{formatear_tamano(tamano_total_bytes)}"
    )

    
    directorios = resultado["directorios"]
    limite_directorios = 20

    print("\nDirectorios encontrados:")

    if directorios:
        for numero, directorio in enumerate(
            directorios[:limite_directorios],
            start=1
        ):
            print(f"  {numero}. {directorio}")

        restantes = len(directorios) - limite_directorios

        if restantes > 0:
            print(
                f"  ... y {restantes} directorios más "
                f"que no se muestran."
            )

    else:
        print("  No se encontraron subdirectorios.")

    detalle_directorios = resultado["detalle_directorios"]

    if directorios:
        print("\nDetalle de carpetas:")
        print("-" * 70)

        for numero, directorio in enumerate(
            directorios[:limite_directorios],
            start=1
        ):
            detalle = detalle_directorios.get(directorio)

            if detalle is None:
                continue

            print(f"\n{numero}. {directorio}")
            print(f"   Archivos directos: {detalle['archivos']}")
            print(
                "   Subdirectorios directos: "
                f"{detalle['subdirectorios']}"
            )

        if len(directorios) > limite_directorios:
            print(
                f"\nSe omitieron {len(directorios) - limite_directorios} "
                "carpetas del detalle."
            )

    print("\nArchivos por categoría:")
    print("-" * 70)

    for categoria, nombre in nombres_categorias.items():
        cantidad = resultado["cantidades_por_categoria"][categoria]

        cantidad_formateada = f"{cantidad:,}".replace(",", ".")

        tamano_bytes = resultado["tamanos_por_categoria_bytes"][categoria]
        tamano_formateado = formatear_tamano(tamano_bytes)

        etiqueta_archivos = "archivo" if cantidad == 1 else "archivos"

        print(
            f"{nombre + ':':<25}"
            f"{cantidad_formateada:>7} {etiqueta_archivos:<9}"
            f"{tamano_formateado:>16}"
        )

    print("-" * 50)

    errores = resultado["errores"]

    print(f"Errores durante el escaneo: {len(errores)}")

    if errores:
        print("\nDetalle de los errores:")

        for numero, error in enumerate(errores, start=1):
            ruta = error["ruta"]
            mensaje = error["error"]

            print(f"\n{numero}. Ruta: {ruta or 'No disponible'}")
            print(f"   Motivo: {mensaje}")
    else:
        print("El escaneo finalizó sin errores.")

    print("=" * 50)
        