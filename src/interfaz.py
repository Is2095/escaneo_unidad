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
    tamano_total_mb = tamano_total_bytes / (1024 ** 2)

    print(
        f"Tamaño total de archivos: "
        f"{tamano_total_mb:,.2f} MB".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    print("\nArchivos por categoría:")
    print("-" * 70)

    for categoria, nombre in nombres_categorias.items():
        cantidad = resultado["cantidades_por_categoria"][categoria]

        cantidad_formateada = f"{cantidad:,}".replace(",", ".")

        tamano_bytes = resultado["tamanos_por_categoria_bytes"][categoria]
        tamano_mb = tamano_bytes / (1024 ** 2)

        print(
            f"{nombre + ':':<25}"
            f"{cantidad_formateada:>10} archivos"
            f"{tamano_mb:>12.2f} MB"
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
        