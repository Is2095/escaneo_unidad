
from datetime import datetime
from openpyxl import load_workbook
import pytest

from src.informe_excel import (
    crear_ruta_informe,
    generar_informe_excel,
    validar_ubicacion_informe,
  )



def test_crea_carpeta_y_nombre_del_informe(tmp_path):
    ubicacion_base = tmp_path / "Informes_escaneo"
    ubicacion_base.mkdir()

    momento = datetime(2026, 10, 12, 15, 30, 45)

    ruta = crear_ruta_informe(ubicacion_base, momento)

    assert ruta.parent.is_dir()
    assert ruta.parent.parent == ubicacion_base
    assert ruta.parent.name == "ESCANEO_2026-10-12_15-30-45"
    assert ruta.name == "informe_escaneo_2026-10-12_15-30-45.xlsx"
    assert not ruta.exists()


def test_no_sobrescribe_una_carpeta_de_informes_existente(tmp_path):
    ubicacion_base = tmp_path / "Informes_escaneo"
    ubicacion_base.mkdir()

    momento = datetime(2026, 10, 12, 15, 30, 45)

    primera_ruta = crear_ruta_informe(ubicacion_base, momento)
    segunda_ruta = crear_ruta_informe(ubicacion_base, momento)

    assert primera_ruta.parent.name == "ESCANEO_2026-10-12_15-30-45"
    assert segunda_ruta.parent.name == "ESCANEO_2026-10-12_15-30-45_01"
    assert primera_ruta.parent != segunda_ruta.parent

    assert primera_ruta.parent.is_dir()
    assert segunda_ruta.parent.is_dir()
    assert not primera_ruta.exists()
    assert not segunda_ruta.exists()


def test_rechaza_una_ruta_inexistente(tmp_path):
    origen = tmp_path / "No_existe"

    with pytest.raises(ValueError):
        crear_ruta_informe(origen)

    assert not origen.exists()


def test_rechaza_una_ruta_que_es_un_archivo(tmp_path):
    archivo = tmp_path / "archivo.txt"
    archivo.write_text("contenido", encoding="utf-8")

    with pytest.raises(ValueError):
        crear_ruta_informe(archivo)


def test_genera_excel_con_resumen_del_analisis(tmp_path):
    origen = tmp_path / "Fotos"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 3,
        "total_archivos": 12,
        "tamano_total_bytes": 2048,
        "cantidad_grupos_duplicados": 2,
        "cantidad_archivos_duplicados": 5,
        "espacio_duplicado_bytes": 1024,
        "grupos_duplicados": [],
        "detalle_archivos": [],
        "directorios": [],
        "detalle_directorios": {},
        "errores": [],
    }

    generar_informe_excel(resultado, ruta_excel)

    assert ruta_excel.is_file()

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Resumen"]

    assert hoja["A1"].value == "INFORME DE ESCANEO"
    assert hoja["A5"].value == "Ruta analizada"
    assert hoja["B5"].value == str(origen)
    assert hoja["B6"].value == 3
    assert hoja["B7"].value == 12
    assert hoja["B8"].value == 2048
    assert hoja["B9"].value == 2
    assert hoja["B10"].value == 5
    assert hoja["B11"].value == 1024
    assert hoja["B12"].value == 0

    libro.close()


def test_no_sobrescribe_un_excel_existente(tmp_path):
    origen = tmp_path / "Fotos"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    ruta_excel.write_text("contenido original", encoding="utf-8")

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 0,
        "total_archivos": 0,
        "tamano_total_bytes": 0,
        "cantidad_grupos_duplicados": 0,
        "cantidad_archivos_duplicados": 0,
        "espacio_duplicado_bytes": 0,
        "errores": [],
    }

    with pytest.raises(FileExistsError):
        generar_informe_excel(resultado, ruta_excel)

    assert ruta_excel.read_text(encoding="utf-8") == "contenido original"


def test_inventario_excel_incluye_datos_de_archivos(tmp_path):
    origen = tmp_path / "Fotos"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 1,
        "total_archivos": 2,
        "tamano_total_bytes": 100,
        "cantidad_grupos_duplicados": 0,
        "cantidad_archivos_duplicados": 0,
        "espacio_duplicado_bytes": 0,
        "grupos_duplicados": [],
        "errores": [],
        "directorios": [],
        "detalle_directorios": {},
        "detalle_archivos": [
            {
                "nombre": "foto.jpg",
                "ruta": origen / "foto.jpg",
                "directorio": origen,
                "extension": ".jpg",
                "categoria": "fotografias",
                "tamano_bytes": 100,
            },
            {
                "nombre": "sin_tamano.pdf",
                "ruta": origen / "sin_tamano.pdf",
                "directorio": origen,
                "extension": ".pdf",
                "categoria": "documentos",
                "tamano_bytes": None,
            },
        ],
    }

    generar_informe_excel(resultado, ruta_excel)

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Inventario de archivos"]

    assert hoja.max_row == 3
    assert hoja["A1"].value == "Nombre"
    assert hoja["A2"].value == "foto.jpg"
    assert hoja["D2"].value == ".jpg"
    assert hoja["E2"].value == "fotografias"
    assert hoja["F2"].value == 100
    assert hoja["A3"].value == "sin_tamano.pdf"
    assert hoja["F3"].value is None
    assert hoja["G3"].value == "No disponible"

    libro.close()


def test_hoja_carpetas_incluye_cantidades_correctas(tmp_path):
    origen = tmp_path / "Fotos"
    subcarpeta = origen / "Vacaciones"
    subcarpeta.mkdir(parents=True)

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 1,
        "total_archivos": 2,
        "tamano_total_bytes": 100,
        "cantidad_grupos_duplicados": 0,
        "cantidad_archivos_duplicados": 0,
        "espacio_duplicado_bytes": 0,
        "grupos_duplicados": [],
        "errores": [],
        "detalle_archivos": [],
        "directorios": [subcarpeta],
        "detalle_directorios": {
            subcarpeta: {
                "archivos": 2,
                "subdirectorios": 1,
            },
        },
    }

    generar_informe_excel(resultado, ruta_excel)

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Carpetas"]

    assert hoja["A1"].value == "Ruta del directorio"
    assert hoja["A2"].value == str(subcarpeta)
    assert hoja["B2"].value == 2
    assert hoja["C2"].value == 1

    libro.close()


def test_hoja_duplicados_incluye_grupos_y_rutas(tmp_path):
    origen = tmp_path / "Fotos"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    archivo_a = origen / "foto_a.jpg"
    archivo_b = origen / "foto_b.jpg"
    archivo_c = origen / "documento_a.pdf"
    archivo_d = origen / "documento_b.pdf"
    archivo_e = origen / "documento_c.pdf"

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 1,
        "total_archivos": 5,
        "tamano_total_bytes": 500,
        "cantidad_grupos_duplicados": 2,
        "cantidad_archivos_duplicados": 5,
        "espacio_duplicado_bytes": 200,
        "errores": [],
        "detalle_archivos": [],
        "directorios": [],
        "detalle_directorios": {},
        "grupos_duplicados": [
            [archivo_a, archivo_b],
            [archivo_c, archivo_d, archivo_e],
        ],
    }

    generar_informe_excel(resultado, ruta_excel)

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Duplicados"]

    assert hoja["A1"].value == "Grupo"
    assert hoja["B1"].value == "Archivos en el grupo"
    assert hoja["C1"].value == "Ruta del archivo"

    assert hoja["A2"].value == 1
    assert hoja["B2"].value == 2
    assert hoja["C2"].value == str(archivo_a)

    assert hoja["A3"].value == 1
    assert hoja["B3"].value == 2
    assert hoja["C3"].value == str(archivo_b)

    assert hoja["A4"].value == 2
    assert hoja["B4"].value == 3
    assert hoja["C4"].value == str(archivo_c)

    assert hoja["A5"].value == 2
    assert hoja["B5"].value == 3
    assert hoja["C5"].value == str(archivo_d)

    assert hoja["A6"].value == 2
    assert hoja["B6"].value == 3
    assert hoja["C6"].value == str(archivo_e)

    libro.close()


def test_hoja_errores_incluye_ruta_y_motivo(tmp_path):
    origen = tmp_path / "Fotos"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    ruta_afectada = origen / "foto_danada.jpg"

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 1,
        "total_archivos": 1,
        "tamano_total_bytes": 0,
        "cantidad_grupos_duplicados": 0,
        "cantidad_archivos_duplicados": 0,
        "espacio_duplicado_bytes": 0,
        "detalle_archivos": [],
        "directorios": [],
        "detalle_directorios": {},
        "grupos_duplicados": [],
        "errores": [
            {
                "ruta": ruta_afectada,
                "error": "Permiso denegado",
            },
        ],
    }

    generar_informe_excel(resultado, ruta_excel)

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Errores"]

    assert hoja["A1"].value == "Ruta afectada"
    assert hoja["B1"].value == "Motivo del error"
    assert hoja["A2"].value == str(ruta_afectada)
    assert hoja["B2"].value == "Permiso denegado"

    libro.close()


def test_hoja_resultado_copia_indica_cuando_no_se_realiza(
    tmp_path,
):
    origen = tmp_path / "Fotos"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 1,
        "total_archivos": 0,
        "tamano_total_bytes": 0,
        "cantidad_grupos_duplicados": 0,
        "cantidad_archivos_duplicados": 0,
        "espacio_duplicado_bytes": 0,
        "detalle_archivos": [],
        "directorios": [],
        "detalle_directorios": {},
        "grupos_duplicados": [],
        "errores": [],
    }

    generar_informe_excel(resultado, ruta_excel)

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Resultado de copia"]

    assert hoja["A1"].value == "RESULTADO DE LA COPIA"
    assert hoja["A3"].value == "Indicador"
    assert hoja["B3"].value == "Resultado"
    assert hoja["A4"].value == "Estado"
    assert hoja["B4"].value == "No se realizó la copia"
    assert hoja["A5"].value == "Origen"
    assert hoja["B5"].value == "No disponible"
    assert hoja["A7"].value == "Archivos copiados"
    assert hoja["B7"].value == 0

    libro.close()


def test_hoja_resultado_copia_muestra_resumen_correcto(tmp_path):
    origen = tmp_path / "Fotos"
    destino = tmp_path / "Fotos_sin_duplicados"
    origen.mkdir()

    ruta_excel = crear_ruta_informe(
        origen,
        datetime(2026, 10, 12, 15, 30, 45),
    )

    resultado = {
        "ruta_analizada": str(origen),
        "total_directorios": 1,
        "total_archivos": 4,
        "tamano_total_bytes": 1000,
        "cantidad_grupos_duplicados": 1,
        "cantidad_archivos_duplicados": 2,
        "espacio_duplicado_bytes": 250,
        "detalle_archivos": [],
        "directorios": [],
        "detalle_directorios": {},
        "grupos_duplicados": [],
        "errores": [],
        "resultado_copia": {
            "origen": str(origen),
            "destino": str(destino),
            "archivos_copiados": 3,
            "archivos_verificados": 3,
            "archivos_omitidos_duplicados": 1,
            "errores": [],
            "copia_completa": True,
        },
    }

    generar_informe_excel(resultado, ruta_excel)

    libro = load_workbook(ruta_excel, data_only=True)
    hoja = libro["Resultado de copia"]

    assert hoja["B4"].value == "COMPLETA"
    assert hoja["B5"].value == str(origen)
    assert hoja["B6"].value == str(destino)
    assert hoja["B7"].value == 3
    assert hoja["B8"].value == 3
    assert hoja["B9"].value == 1
    assert hoja["B10"].value == 0

    libro.close()


def test_validar_ubicacion_informe_acepta_una_carpeta_externa(
    tmp_path,
):
    origen = tmp_path / "origen"
    origen.mkdir()

    ubicacion_informe = tmp_path / "informes"
    ubicacion_informe.mkdir()

    assert validar_ubicacion_informe(
        origen,
        ubicacion_informe,
    ) is True


def test_validar_ubicacion_informe_rechaza_una_carpeta_interna(
    tmp_path,
):
    origen = tmp_path / "origen"
    origen.mkdir()

    ubicacion_informe = origen / "informes"
    ubicacion_informe.mkdir()

    with pytest.raises(
        ValueError,
        match="fuera de la carpeta analizada",
    ):
        validar_ubicacion_informe(
            origen,
            ubicacion_informe,
        )


def test_validar_ubicacion_informe_no_crea_carpetas(
    tmp_path,
):
    origen = tmp_path / "origen"
    origen.mkdir()

    ubicacion_informe = origen / "informes"

    with pytest.raises(ValueError):
        validar_ubicacion_informe(
            origen,
            ubicacion_informe,
        )

    assert not ubicacion_informe.exists()   
    