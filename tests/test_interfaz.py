from pathlib import Path

from src.analizador import analizar_unidad
from src.interfaz import mostrar_resumen
from src.interfaz import formatear_tamano

def test_mostrar_resumen_incluye_la_ruta(tmp_path, capsys):
    resultado = analizar_unidad(tmp_path)

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert str(tmp_path) in salida
    assert "RESUMEN DEL ESCANEO" in salida


def test_mostrar_resumen_incluye_todas_las_categorias(
    tmp_path,
    capsys,
):
    resultado = analizar_unidad(tmp_path)

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert "Fotografías:" in salida
    assert "Videos:" in salida
    assert "Documentos:" in salida
    assert "Bases de datos:" in salida
    assert "Sistema:" in salida
    assert "Otros:" in salida


def test_mostrar_resumen_muestra_cantidades(tmp_path, capsys):
    (tmp_path / "foto.jpg").touch()
    (tmp_path / "documento.pdf").touch()

    resultado = analizar_unidad(tmp_path)

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert "Archivos encontrados:" in salida
    assert "Fotografías:" in salida
    assert "Documentos:" in salida
    assert "Errores durante el escaneo: 0" in salida


def test_mostrar_resumen_sin_errores_muestra_mensaje(
    capsys,
    tmp_path,
):
    from src.analizador import analizar_unidad
    from src.interfaz import mostrar_resumen

    resultado = analizar_unidad(tmp_path)

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert "Errores durante el escaneo: 0" in salida
    assert "El escaneo finalizó sin errores." in salida


def test_mostrar_resumen_con_errores_muestra_detalles(
    capsys,
    tmp_path,
):
    from src.analizador import analizar_unidad
    from src.interfaz import mostrar_resumen

    resultado = analizar_unidad(tmp_path)

    resultado["errores"] = [
        {
            "ruta": tmp_path / "carpeta_protegida",
            "error": "Acceso denegado",
        },
        {
            "ruta": tmp_path / "otra_carpeta",
            "error": "Error de entrada/salida",
        },
    ]

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert "Errores durante el escaneo: 2" in salida
    assert "Detalle de los errores:" in salida
    assert "carpeta_protegida" in salida
    assert "Acceso denegado" in salida
    assert "otra_carpeta" in salida
    assert "Error de entrada/salida" in salida   


def test_formatear_tamano_en_bytes():
    assert formatear_tamano(850) == "850 bytes"


def test_formatear_tamano_en_kilobytes():
    assert formatear_tamano(1024) == "1,00 KB"


def test_formatear_tamano_en_megabytes():
    assert formatear_tamano(1572864) == "1,50 MB"


def test_formatear_tamano_en_gigabytes():
    assert formatear_tamano(1073741824) == "1,00 GB"


def test_formatear_tamano_cero():
    assert formatear_tamano(0) == "0 bytes"


def test_mostrar_resumen_incluye_detalle_de_carpetas(
    tmp_path,
    capsys,
):
    carpeta = tmp_path / "fotos"
    carpeta.mkdir()

    (carpeta / "foto1.jpg").touch()
    (carpeta / "foto2.jpg").touch()

    subcarpeta = carpeta / "vacaciones"
    subcarpeta.mkdir()

    resultado = analizar_unidad(tmp_path)

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert "Detalle de carpetas:" in salida
    assert str(carpeta) in salida
    assert "Archivos directos: 2" in salida
    assert "Subdirectorios directos: 1" in salida 


def test_mostrar_resumen_incluye_detalle_de_archivos(
    tmp_path,
    capsys,
):
    carpeta = tmp_path / "fotos"
    carpeta.mkdir()

    foto = carpeta / "paisaje.JPG"
    foto.write_bytes(b"12345")

    resultado = analizar_unidad(tmp_path)

    mostrar_resumen(resultado)

    salida = capsys.readouterr().out

    assert "Detalle de archivos por carpeta:" in salida
    assert str(carpeta) in salida
    assert "paisaje.JPG" in salida
    assert "Fotografías" in salida
    assert "5 bytes" in salida


def test_main_usa_ubicacion_predeterminada_del_informe(
    tmp_path,
    monkeypatch,
):
    import src.main as modulo_main

    ruta_origen = tmp_path / "prueba_escaneo"
    ruta_origen.mkdir()

    resultado_escaneo = {
        "ruta_analizada": str(ruta_origen),
    }

    ubicaciones_informe = []

    monkeypatch.setattr(
        modulo_main,
        "analizar_unidad",
        lambda ruta: resultado_escaneo,
    )
    monkeypatch.setattr(
        modulo_main,
        "mostrar_resumen",
        lambda resultado: None,
    )
    monkeypatch.setattr(
        modulo_main,
        "crear_ruta_informe",
        lambda ubicacion: (
            ubicaciones_informe.append(ubicacion)
            or tmp_path / "informe.xlsx"
        ),
    )
    monkeypatch.setattr(
        modulo_main,
        "generar_informe_excel",
        lambda resultado, ruta: None,
    )
    monkeypatch.setattr(
        modulo_main,
        "validar_ubicacion_informe",
        lambda ruta, ubicacion: True,
    )

    respuestas = iter([
        str(ruta_origen),  # Carpeta que se analizará.
        "n",               # No realizar la copia.
        "",                # Enter: ubicación predeterminada.
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda mensaje: next(respuestas),
    )

    modulo_main.main()

    assert len(ubicaciones_informe) == 1
    assert (
        Path(ubicaciones_informe[0]).resolve()
        == ruta_origen.resolve()
    )     

