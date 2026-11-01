from pathlib import Path
from src.analizador import analizar_unidad
from src.interfaz import mostrar_resumen
from src.copiador import copiar_sin_duplicados
from src.informe_excel import (
    crear_ruta_informe, 
    generar_informe_excel,
    validar_ubicacion_informe
)


def main():
    """
    Ejecuta el análisis de un directorio.
    """

    ruta = input("Ingrese la ruta de la unidad o carpeta a analizar: ").strip()

    if not ruta:
        print("No se indicó ninguna ruta.")
        return

    resultado_copia = None

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
        resultado["resultado_copia"] = None
    else:
        ruta_destino = input(
            "Ingrese la ruta de destino "
            "(Enter para usar la carpeta de origen): "
        ).strip()

        if not ruta_destino:
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

            resultado["resultado_copia"] = resultado_copia

        except (ValueError, FileExistsError) as error:
            print(f"\nNo se pudo iniciar la copia: {error}")
            resultado["resultado_copia"] = {
                "error_inicio": str(error)
            }

        else:
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
                f"Errores durante la copia: "
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


  
    # if (
    #     resultado_copia is not None
    #     and "destino" in resultado_copia
    # ):
    #     ubicacion_informe = resultado_copia["destino"]
    # else:
    #     ubicacion_informe = resultado["ruta_analizada"]

    # print("\nUbicación del informe Excel")
    # print("Presioná Enter para usar la ubicación predeterminada.")
    # carpeta_informe = input(
    #     "Carpeta donde guardar el informe: "
    # ).strip()

    # if carpeta_informe:
    #     ubicacion_informe = carpeta_informe

    # try:
    #     ruta_excel = crear_ruta_informe(ubicacion_informe)
    #     generar_informe_excel(resultado, ruta_excel)
    #     print(f"\nInforme Excel generado: {ruta_excel}")
    # except (OSError, ValueError, FileExistsError) as error:
    #     print(f"\nNo se pudo generar el informe Excel: {error}")
    
    # Generar el informe Excel al finalizar el proceso.
    # if (
    #     resultado_copia is not None
    #     and "destino" in resultado_copia
    # ):
    #     ubicacion_informe = resultado_copia["destino"]
    # else:
    #     ubicacion_informe = resultado["ruta_analizada"]

    

    # Generar el informe Excel al finalizar el proceso.
    if (
        resultado_copia is not None
        and "destino" in resultado_copia
    ):
        ubicacion_informe = resultado_copia["destino"]
    else:
        ubicacion_informe = resultado["ruta_analizada"]

    ruta_analizada = Path(
        resultado["ruta_analizada"]
    ).resolve()

    es_raiz_unidad = (
        ruta_analizada == Path(ruta_analizada.anchor)
    )

    print("\nUbicación del informe Excel")

    if es_raiz_unidad:
        print(
            "Estás analizando una unidad completa."
        )
        print(
            "Indicá una carpeta ubicada fuera de esa unidad."
        )
        carpeta_informe = input(
            "Carpeta donde guardar el informe: "
        ).strip()

        if not carpeta_informe:
            print(
                "No se generó el informe: "
                "debes indicar una ubicación externa."
            )
            return

        ubicacion_informe = carpeta_informe

    else:
        print(
            "Presioná Enter para usar la ubicación predeterminada."
        )
        carpeta_informe = input(
            "Carpeta donde guardar el informe: "
        ).strip()

        if carpeta_informe:
            ubicacion_informe = carpeta_informe

    try:
        # La carpeta de informes se crea junto a esta ubicación.
        carpeta_destino_informe = (
            Path(ubicacion_informe).resolve().parent
        )

        validar_ubicacion_informe(
            ruta_analizada,
            carpeta_destino_informe,
        )

        ruta_excel = crear_ruta_informe(
            ubicacion_informe
        )

        generar_informe_excel(
            resultado,
            ruta_excel,
        )

        print(f"\nInforme Excel generado: {ruta_excel}")

    except (OSError, ValueError, FileExistsError) as error:
        print(f"\nNo se pudo generar el informe Excel: {error}")
if __name__ == "__main__":
    main()