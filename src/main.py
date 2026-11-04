
from pathlib import Path

from src.analizador import analizar_unidad
from src.interfaz import mostrar_resumen
from src.copiador import copiar_sin_duplicados
from src.informe_excel import (
    crear_ruta_informe,
    generar_informe_excel,
    validar_ubicacion_informe,
)


def main():
    """
    Ejecuta el análisis de una carpeta o unidad.

    Los resultados de cada ejecución se guardan en una
    carpeta independiente dentro de Informes_escaneo.
    """

    ruta = input(
        "Ingrese la ruta de la unidad o carpeta a analizar: "
    ).strip()

    if not ruta:
        print("No se indicó ninguna ruta.")
        return

    # Analizar el origen.
    try:
        resultado = analizar_unidad(ruta)

    except (ValueError, OSError) as error:
        print(f"\nError durante el análisis: {error}")
        return

    mostrar_resumen(resultado)

    # Preguntar si se desea copiar los archivos.
    respuesta = input(
        "\n¿Desea copiar los archivos sin duplicados? (s/n): "
    ).strip().lower()

    # Determinar la ubicación base de los resultados.
    ruta_proyecto = Path(__file__).resolve().parent.parent

    print(
        "\n¿Dónde desea guardar los resultados del escaneo?"
    )
    print("Presione Enter para utilizar la ubicación predeterminada:")
    print(ruta_proyecto)

    ruta_personalizada = input(
        "\nRuta: "
    ).strip()

    if ruta_personalizada:
        ubicacion_resultados = Path(
            ruta_personalizada
        ).resolve()

        if (
            not ubicacion_resultados.exists()
            or not ubicacion_resultados.is_dir()
        ):
            print(
                "\nLa ubicación indicada no existe "
                "o no es una carpeta."
            )
            return

    else:
        ubicacion_resultados = ruta_proyecto

    # Crear la carpeta Informes_escaneo dentro de la ubicación elegida.
    ubicacion_base = ubicacion_resultados / "Informes_escaneo"

    ruta_analizada = Path(
        resultado["ruta_analizada"]
    ).resolve()

    # Comprobar que los resultados no se guarden dentro
    # del origen analizado.
    try:
        validar_ubicacion_informe(
            ruta_analizada,
            ubicacion_base,
        )

    except ValueError as error:
        print(
            "\nLa ubicación elegida no es válida para guardar "
            "los resultados."
        )
        print(f"Motivo: {error}")

        if not ruta_personalizada:
            print(
                "\nIndicá una carpeta existente ubicada fuera "
                "del origen analizado."
            )

            ruta_alternativa = input(
                "Carpeta donde guardar los resultados: "
            ).strip()

            if not ruta_alternativa:
                print(
                    "\nNo se indicó una ubicación alternativa. "
                    "No se generaron resultados."
                )
                return

            ubicacion_resultados = Path(
                ruta_alternativa
            ).resolve()

            if (
                not ubicacion_resultados.exists()
                or not ubicacion_resultados.is_dir()
            ):
                print(
                    "\nLa ubicación indicada no existe "
                    "o no es una carpeta."
                )
                return

            ubicacion_base = (
                ubicacion_resultados / "Informes_escaneo"
            )

            try:
                validar_ubicacion_informe(
                    ruta_analizada,
                    ubicacion_base,
                )

            except ValueError as error:
                print(f"\nUbicación no válida: {error}")
                return

        else:
            return

    # Crear la carpeta base si todavía no existe.
    try:
        ubicacion_base.mkdir(parents=True, exist_ok=True)

    except OSError as error:
        print(
            f"\nNo se pudo crear la carpeta de resultados: {error}"
        )
        return

    # Crear una carpeta exclusiva para esta ejecución.
    try:
        ruta_excel = crear_ruta_informe(ubicacion_base)

    except (OSError, ValueError) as error:
        print(
            f"\nNo se pudo crear la carpeta de esta ejecución: {error}"
        )
        return

    carpeta_escaneo = ruta_excel.parent

    print(
        "\nCarpeta de resultados de esta ejecución:"
    )
    print(carpeta_escaneo)

    resultado_copia = None

    if respuesta != "s":
        print("\nNo se realizará ninguna copia.")

    else:
        # El destino debe ser una carpeta inexistente.
        ruta_destino = carpeta_escaneo / "Archivos"

        try:
            resultado_copia = copiar_sin_duplicados(
                ruta_analizada,
                ruta_destino,
                resultado["grupos_duplicados"],
            )

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

            print(
                "Errores durante la copia: "
                f"{len(resultado_copia['errores'])}"
            )

            if resultado_copia["copia_completa"]:
                print("Estado de la copia: COMPLETA")
            else:
                print(
                    "Estado de la copia: INCOMPLETA; "
                    "revisar los errores."
                )

            if resultado_copia["errores"]:
                print("\nDetalle de errores:")

                for error in resultado_copia["errores"]:
                    print(f"- Archivo o ruta: {error['ruta']}")
                    print(f"  Motivo: {error['error']}")

        except (ValueError, FileExistsError, OSError) as error:
            print(f"\nNo se pudo iniciar la copia: {error}")

            resultado_copia = {
                "error_inicio": str(error)
            }

    # Incorporar el resultado de la copia al informe.
    resultado["resultado_copia"] = resultado_copia

    # Generar el informe Excel dentro de la carpeta de ejecución.
    try:
        generar_informe_excel(
            resultado,
            ruta_excel,
        )

        print("\n--- RESULTADOS DEL ESCANEO ---")
        print(f"Carpeta de resultados: {carpeta_escaneo}")
        print(f"Informe Excel generado: {ruta_excel}")

        if resultado_copia is not None and "destino" in resultado_copia:
            print(
                f"Archivos copiados en: {resultado_copia['destino']}"
            )

    except (OSError, ValueError, FileExistsError) as error:
        print(f"\nNo se pudo generar el informe Excel: {error}")


if __name__ == "__main__":
    main()
