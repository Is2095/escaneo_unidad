from src.analizador import analizar_unidad


def test_analizar_unidad_cuenta_archivos_y_directorios(tmp_path):
    (tmp_path / "foto.jpg").touch()
    (tmp_path / "documento.pdf").touch()

    subdirectorio = tmp_path / "carpeta"
    subdirectorio.mkdir()
    (subdirectorio / "video.mp4").touch()

    resultado = analizar_unidad(tmp_path)

    assert resultado["total_archivos"] == 3
    assert resultado["total_directorios"] == 1


def test_analizar_unidad_clasifica_archivos(tmp_path):
    (tmp_path / "foto.jpg").touch()
    (tmp_path / "documento.pdf").touch()
    (tmp_path / "desconocido.xyz").touch()

    resultado = analizar_unidad(tmp_path)

    categorias = resultado["archivos_por_categoria"]

    assert len(categorias["fotografias"]) == 1
    assert len(categorias["documentos"]) == 1
    assert len(categorias["otros"]) == 1


def test_analizar_unidad_incluye_todas_las_categorias(tmp_path):
    resultado = analizar_unidad(tmp_path)

    assert len(resultado["cantidades_por_categoria"]) == 10
    assert resultado["total_archivos"] == 0
    assert resultado["errores"] == []


def test_analizar_unidad_conserva_la_ruta_analizada(tmp_path):
    resultado = analizar_unidad(tmp_path)

    assert resultado["ruta_analizada"] == str(tmp_path)


def test_analizar_unidad_rechaza_ruta_inexistente(tmp_path):
    ruta_inexistente = tmp_path / "no_existe"

    try:
        analizar_unidad(ruta_inexistente)
    except ValueError as error:
        assert "no existe" in str(error)
    else:
        raise AssertionError("Se esperaba un ValueError")

    