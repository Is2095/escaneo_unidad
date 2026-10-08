from src.analizador import analizar_unidad
from src.interfaz import mostrar_resumen


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
    