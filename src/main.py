from src.analizador import analizar_unidad
from src.interfaz import mostrar_resumen


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


if __name__ == "__main__":
    main()