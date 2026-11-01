
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from src.interfaz import formatear_tamano



def validar_ubicacion_informe(
    ruta_analizada,
    ubicacion_informe,
):
    """
    Comprueba que el informe se guarde fuera de la
    carpeta analizada y, si se analiza una unidad
    completa, fuera de esa unidad.
    """
    ruta_analizada = Path(ruta_analizada).resolve()
    ubicacion_informe = Path(ubicacion_informe).resolve()

    if ruta_analizada == Path(ruta_analizada.anchor):
        # Al analizar una unidad completa, el informe
        # debe guardarse en otra unidad.
        if (
            ubicacion_informe.drive.lower()
            == ruta_analizada.drive.lower()
        ):
            raise ValueError(
                "La ubicación del informe debe estar "
                "fuera de la unidad analizada."
            )
    else:
        # Al analizar una carpeta, el informe no puede
        # guardarse dentro de ella.
        try:
            ubicacion_informe.relative_to(ruta_analizada)
        except ValueError:
            pass
        else:
            raise ValueError(
                "La ubicación del informe debe estar "
                "fuera de la carpeta analizada."
            )

    return True


def crear_ruta_informe(ubicacion_base, momento=None):
    """
    Crea una carpeta para el informe junto a la ubicación indicada
    y devuelve la ruta del archivo Excel con fecha y hora.

    No modifica el contenido de la ubicación base.
    """

    base = Path(ubicacion_base).resolve()

    if not base.exists() or not base.is_dir():
        raise ValueError(
            "La ubicación base debe ser una carpeta existente."
        )

    fecha = momento or datetime.now()

    marca_tiempo = fecha.strftime("%Y-%m-%d_%H-%M-%S")
    fecha_carpeta = fecha.strftime("%Y-%m-%d")

    carpeta_base = base.parent
    nombre_carpeta = f"Informes_escaneo_{fecha_carpeta}"
    carpeta_informes = carpeta_base / nombre_carpeta

    sufijo = 1

    while carpeta_informes.exists():
        carpeta_informes = (
            carpeta_base / f"{nombre_carpeta}_{sufijo:02d}"
        )
        sufijo += 1

    carpeta_informes.mkdir()

    ruta_excel = (
        carpeta_informes
        / f"informe_escaneo_{marca_tiempo}.xlsx"
    )

    return ruta_excel


def generar_informe_excel(resultado, ruta_excel):
    """
    Genera un archivo Excel con el resumen del análisis.
    """

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Resumen"

    hoja.append(["INFORME DE ESCANEO"])
    hoja.append(["Fecha de generación", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    hoja.append([])
    hoja.append(["Indicador", "Resultado exacto", "Tamaño legible"])

    datos = [
        ("Ruta analizada", resultado["ruta_analizada"]),
        ("Directorios encontrados", resultado["total_directorios"]),
        ("Archivos encontrados", resultado["total_archivos"]),
        ("Tamaño total (bytes)", resultado["tamano_total_bytes"], formatear_tamano(resultado["tamano_total_bytes"])),
        ("Grupos de duplicados", resultado["cantidad_grupos_duplicados"]),
        ("Archivos en grupos duplicados", resultado["cantidad_archivos_duplicados"]),
        ("Espacio potencialmente recuperable (bytes)", resultado["espacio_duplicado_bytes"], formatear_tamano(resultado["espacio_duplicado_bytes"])),
        ("Errores durante el análisis", len(resultado["errores"])),
    ]

    for fila in datos:
      hoja.append(list(fila))

    hoja["A1"].font = Font(bold=True, size=16)
    hoja["A4"].font = Font(bold=True, color="FFFFFF")
    hoja["B4"].font = Font(bold=True, color="FFFFFF")
    hoja["A4"].fill = PatternFill("solid", fgColor="1F4E78")
    hoja["B4"].fill = PatternFill("solid", fgColor="1F4E78")

    for celda in hoja["C"]:
      celda.alignment = Alignment(horizontal="right")

    hoja.freeze_panes = "A5"
    hoja.auto_filter.ref = f"A4:B{hoja.max_row}"

    for columna in hoja.columns:
        letra = get_column_letter(columna[0].column)
        ancho = max(
            len(str(celda.value or ""))
            for celda in columna
        )
        hoja.column_dimensions[letra].width = min(ancho + 2, 70)

    ruta_excel = Path(ruta_excel)
    ruta_excel.parent.mkdir(parents=True, exist_ok=True)

    if ruta_excel.exists():
        raise FileExistsError(
            f"El informe ya existe y no se sobrescribirá: {ruta_excel}"
        )


    inventario = libro.create_sheet("Inventario de archivos")

    inventario.append([
        "Nombre",
        "Ruta completa",
        "Directorio",
        "Extensión",
        "Categoría",
        "Tamaño (bytes)",
        "Tamaño legible",
    ])

    for archivo in resultado["detalle_archivos"]:
        tamano_bytes = archivo["tamano_bytes"]

        if tamano_bytes is None:
            tamano_legible = "No disponible"
        else:
            tamano_legible = formatear_tamano(tamano_bytes)

        inventario.append([
            archivo["nombre"],
            str(archivo["ruta"]),
            str(archivo["directorio"]),
            archivo["extension"],
            archivo["categoria"],
            tamano_bytes,
            tamano_legible,
        ])

    inventario.freeze_panes = "A2"
    inventario.auto_filter.ref = inventario.dimensions

    for columna in inventario.columns:
        letra = get_column_letter(columna[0].column)
        ancho = max(
            len(str(celda.value or ""))
            for celda in columna
        )
        inventario.column_dimensions[letra].width = min(ancho + 2, 70)

    
    carpetas = libro.create_sheet("Carpetas")

    carpetas.append([
        "Ruta del directorio",
        "Archivos directos",
        "Subdirectorios directos",
    ])

    for directorio in resultado["directorios"]:
        detalle = resultado["detalle_directorios"].get(
            directorio,
            {},
        )

        carpetas.append([
            str(directorio),
            detalle.get("archivos"),
            detalle.get("subdirectorios"),
        ])

    carpetas.freeze_panes = "A2"
    carpetas.auto_filter.ref = carpetas.dimensions

    for columna in carpetas.columns:
        letra = get_column_letter(columna[0].column)
        ancho = max(
            len(str(celda.value or ""))
            for celda in columna
        )
        carpetas.column_dimensions[letra].width = min(ancho + 2, 70)

    
    duplicados = libro.create_sheet("Duplicados")

    duplicados.append([
        "Grupo",
        "Archivos en el grupo",
        "Ruta del archivo",
    ])

    for numero_grupo, grupo in enumerate(
        resultado["grupos_duplicados"],
        start=1,
    ):
        for archivo in grupo:
            duplicados.append([
                numero_grupo,
                len(grupo),
                str(archivo),
            ])

    duplicados.freeze_panes = "A2"
    duplicados.auto_filter.ref = duplicados.dimensions

    for columna in duplicados.columns:
        letra = get_column_letter(columna[0].column)
        ancho = max(
            len(str(celda.value or ""))
            for celda in columna
        )
        duplicados.column_dimensions[letra].width = min(ancho + 2, 70)

    
    errores = libro.create_sheet("Errores")

    errores.append([
        "Ruta afectada",
        "Motivo del error",
    ])

    for error in resultado["errores"]:
        errores.append([
            str(error["ruta"]),
            str(error["error"]),
        ])

    errores.freeze_panes = "A2"
    errores.auto_filter.ref = errores.dimensions

    for columna in errores.columns:
        letra = get_column_letter(columna[0].column)
        ancho = max(
            len(str(celda.value or ""))
            for celda in columna
        )
        errores.column_dimensions[letra].width = min(ancho + 2, 70)

    
    copia = libro.create_sheet("Resultado de copia")

    copia.append(["RESULTADO DE LA COPIA"])
    copia.append([])

    copia.append(["Indicador", "Resultado"])

    resultado_copia = resultado.get("resultado_copia")

    if resultado_copia is None:
        datos_copia = [
          ("Estado", "No se realizó la copia"),
          ("Origen", "No disponible"),
          ("Destino", "No disponible"),
          ("Archivos copiados", 0),
          ("Archivos verificados mediante SHA-256", 0),
          ("Archivos omitidos por duplicados", 0),
          ("Errores durante la copia", 0),
          ("Motivo", "El usuario decidió no realizar la copia"),
        ]
    elif "error_inicio" in resultado_copia:
        datos_copia = [
            ("Estado", "No se pudo iniciar la copia"),
            ("Origen", resultado["ruta_analizada"]),
            ("Destino", "No disponible"),
            ("Archivos copiados", 0),
            ("Archivos verificados mediante SHA-256", 0),
            ("Archivos omitidos por duplicados", 0),
            ("Errores durante la copia", 1),
            ("Motivo", resultado_copia["error_inicio"]),
        ]
    else:
        datos_copia = [
            (
                "Estado",
                "COMPLETA"
                if resultado_copia["copia_completa"]
                else "INCOMPLETA",
            ),
            ("Origen", resultado_copia["origen"]),
            ("Destino", resultado_copia["destino"]),
            ("Archivos copiados", resultado_copia["archivos_copiados"]),
            (
                "Archivos verificados mediante SHA-256",
                resultado_copia["archivos_verificados"],
            ),
            (
                "Archivos omitidos por duplicados",
                resultado_copia["archivos_omitidos_duplicados"],
            ),
            (
                "Errores durante la copia",
                len(resultado_copia["errores"]),
            ),
        ]

    for indicador, valor in datos_copia:
        copia.append([indicador, valor])

    copia["A1"].font = Font(bold=True, size=16)
    copia["A3"].font = Font(bold=True, color="FFFFFF")
    copia["B3"].font = Font(bold=True, color="FFFFFF")
    copia["A3"].fill = PatternFill("solid", fgColor="1F4E78")
    copia["B3"].fill = PatternFill("solid", fgColor="1F4E78")

    copia.freeze_panes = "A4"

    for columna in copia.columns:
        letra = get_column_letter(columna[0].column)
        ancho = max(
            len(str(celda.value or ""))
            for celda in columna
        )
        copia.column_dimensions[letra].width = min(ancho + 2, 70)

    libro.save(ruta_excel)

    return ruta_excel

