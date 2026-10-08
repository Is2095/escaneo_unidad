from src.analizador import analizar_unidad
from pathlib import Path


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

def test_analizar_unidad_calcula_tamanos(tmp_path):
    foto = tmp_path / "foto.jpg"
    video = tmp_path / "video.mp4"
    documento = tmp_path / "documento.pdf"

    foto.write_bytes(b"123")
    video.write_bytes(b"12345678")
    documento.write_bytes(b"12345")

    resultado = analizar_unidad(tmp_path)

    assert resultado["tamano_total_bytes"] == 16

    tamanos = resultado["tamanos_por_categoria_bytes"]

    assert tamanos["fotografias"] == 3
    assert tamanos["videos"] == 8
    assert tamanos["documentos"] == 5
    assert tamanos["otros"] == 0

def test_analizar_unidad_registra_error_al_consultar_tamano(
    tmp_path,
    monkeypatch,
):
    foto = tmp_path / "foto.jpg"
    foto.write_bytes(b"12345")

    stat_original = Path.stat

    def stat_con_error(self, *args, **kwargs):
        if self == foto:
            raise PermissionError("Acceso denegado")

        return stat_original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat_con_error)

    resultado = analizar_unidad(tmp_path)

    assert resultado["total_archivos"] == 1
    assert resultado["tamano_total_bytes"] == 0
    assert resultado["tamanos_por_categoria_bytes"]["fotografias"] == 0

    assert len(resultado["errores"]) == 1
    assert resultado["errores"][0]["ruta"] == foto
    assert "Acceso denegado" in resultado["errores"][0]["error"]  