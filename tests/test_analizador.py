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
    assert len(resultado["detalle_archivos"]) == 1
    assert resultado["detalle_archivos"][0]["nombre"] == "foto.jpg"
    assert resultado["detalle_archivos"][0]["tamano_bytes"] is None

def test_analizar_unidad_cuenta_contenido_directo_de_directorios(
    tmp_path,
):
    carpeta_a = tmp_path / "carpeta_a"
    carpeta_a.mkdir()

    (carpeta_a / "foto.jpg").touch()
    (carpeta_a / "documento.pdf").touch()

    subcarpeta = carpeta_a / "subcarpeta"
    subcarpeta.mkdir()
    (subcarpeta / "video.mp4").touch()

    resultado = analizar_unidad(tmp_path)

    detalle = resultado["detalle_directorios"]

    assert detalle[carpeta_a]["archivos"] == 2
    assert detalle[carpeta_a]["subdirectorios"] == 1

    assert detalle[subcarpeta]["archivos"] == 1
    assert detalle[subcarpeta]["subdirectorios"] == 0

def test_analizar_unidad_incluye_detalle_de_archivos(tmp_path):
    foto = tmp_path / "foto.jpg"
    foto.write_bytes(b"12345")

    resultado = analizar_unidad(tmp_path)

    detalle_archivos = resultado["detalle_archivos"]

    assert len(detalle_archivos) == 1

    detalle = detalle_archivos[0]

    assert detalle["ruta"] == foto
    assert detalle["nombre"] == "foto.jpg"
    assert detalle["extension"] == ".jpg"
    assert detalle["directorio"] == tmp_path
    assert detalle["tamano_bytes"] == 5
    assert detalle["categoria"] == "fotografias"

def test_analizar_unidad_detalla_archivos_de_distintas_categorias(
    tmp_path,
):
    foto = tmp_path / "foto.JPG"
    documento = tmp_path / "documento.pdf"
    archivo_desconocido = tmp_path / "datos.xyz"

    foto.write_bytes(b"123")
    documento.write_bytes(b"12345")
    archivo_desconocido.write_bytes(b"1234567")

    resultado = analizar_unidad(tmp_path)

    detalles = {
        detalle["nombre"]: detalle
        for detalle in resultado["detalle_archivos"]
    }

    assert len(detalles) == 3

    assert detalles["foto.JPG"]["extension"] == ".jpg"
    assert detalles["foto.JPG"]["categoria"] == "fotografias"
    assert detalles["foto.JPG"]["tamano_bytes"] == 3

    assert detalles["documento.pdf"]["categoria"] == "documentos"
    assert detalles["documento.pdf"]["tamano_bytes"] == 5

    assert detalles["datos.xyz"]["categoria"] == "otros"
    assert detalles["datos.xyz"]["tamano_bytes"] == 7
    