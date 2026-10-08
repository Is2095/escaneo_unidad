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

    print("\nArchivos por categoría:")
    print("-" * 50)

    for categoria, nombre in nombres_categorias.items():
        cantidad = resultado["cantidades_por_categoria"][categoria]

        cantidad_formateada = f"{cantidad:,}".replace(",", ".")

        print(f"{nombre + ':':<27}{cantidad_formateada:>10}")

    print("-" * 50)
    print(f"Errores durante el escaneo: {len(resultado['errores'])}")
    print("=" * 50)

    