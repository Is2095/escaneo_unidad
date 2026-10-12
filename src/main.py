from src.analizador import analizar_unidad
from src.interfaz import mostrar_resumen
from src.copiador import copiar_sin_duplicados


def main():
    """
    Ejecuta el análisis de un directorio.
    """

    ruta = input("Ingrese la ruta de la unidad o carpeta a analizar: ").strip()

    if not ruta:
        print("No se indicó ninguna ruta.")
        return

    try:
        resultado = analizar_unidad(ruta)
    except ValueError as error:
        print(f"\nError: {error}")
        return


    mostrar_resumen(resultado)

    respuesta = input(
        "\n¿Desea copiar los archivos sin duplicados? (s/n): "
    ).strip().lower()

    if respuesta != "s":
        print("No se realizará ninguna copia.")
        return


    ruta_destino = input(
        "Ingrese la ruta de destino "
        "(Enter para usar la carpeta de origen): "
    ).strip()

    if not ruta_destino:
        from pathlib import Path

        ruta_origen = Path(ruta).resolve()
        ruta_destino = str(
            ruta_origen.parent
            / f"{ruta_origen.name}_sin_duplicados"
        )

        print(f"Se utilizará esta carpeta de destino: {ruta_destino}")

    
    try:
        resultado_copia = copiar_sin_duplicados(
            ruta,
            ruta_destino,
            resultado["grupos_duplicados"],
        )

    except (ValueError, FileExistsError) as error:
        print(f"\nNo se pudo iniciar la copia: {error}")
        return

    print("\n--- RESUMEN DE LA COPIA ---")
    print(f"Origen: {resultado_copia['origen']}")
    print(f"Destino: {resultado_copia['destino']}")
    print(
        "Archivos copiados: "
        f"{resultado_copia['archivos_copiados']}"
    )
    print(
        "Archivos omitidos por duplicados: "
        f"{resultado_copia['archivos_omitidos_duplicados']}"
    )    
    print(
        "Archivos verificados mediante SHA-256: "
        f"{resultado_copia['archivos_verificados']}"
)
    print(f"Errores durante la copia: {len(resultado_copia['errores'])}")
    
    if resultado_copia["copia_completa"]:
        print("Estado de la copia: COMPLETA")
    else:
        print("Estado de la copia: INCOMPLETA; revisar los errores.")

    if resultado_copia["errores"]:
        print("\nDetalle de errores:")

        for error in resultado_copia["errores"]:
            print(f"- Archivo o ruta: {error['ruta']}")
            print(f"  Motivo: {error['error']}")


if __name__ == "__main__":
    main()