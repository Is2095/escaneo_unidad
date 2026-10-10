from src.analizador import (
    analizar_unidad
)
from src.errores import registrar_error

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

def test_analizar_unidad_ordena_archivos_por_tamano(
    tmp_path,
):
    from src.analizador import analizar_unidad

    (tmp_path / "pequeno.txt").write_bytes(b"123")
    (tmp_path / "grande.txt").write_bytes(b"1234567890")
    (tmp_path / "mediano.txt").write_bytes(b"123456")

    resultado = analizar_unidad(tmp_path)

    inventario = sorted(
        resultado["detalle_archivos"],
        key=lambda archivo: (
            archivo["tamano_bytes"] is not None,
            archivo["tamano_bytes"] or 0,
        ),
        reverse=True,
    )

    nombres = [
        archivo["nombre"]
        for archivo in inventario
    ]

    assert nombres == [
        "grande.txt",
        "mediano.txt",
        "pequeno.txt",
    ]

def test_analizar_unidad_identifica_archivos_duplicados(tmp_path):
    foto_original = tmp_path / "foto_original.jpg"
    foto_copia = tmp_path / "foto_copia.jpg"

    contenido = b"contenido identico de prueba"

    foto_original.write_bytes(contenido)
    foto_copia.write_bytes(contenido)

    resultado = analizar_unidad(tmp_path)

    assert resultado["cantidad_grupos_duplicados"] == 1
    assert resultado["cantidad_archivos_duplicados"] == 2

    grupos = resultado["grupos_duplicados"]

    assert len(grupos) == 1
    assert set(grupos[0]) == {foto_original, foto_copia}

    assert resultado["espacio_duplicado_bytes"] == len(contenido)

def test_analizar_unidad_no_identifica_archivos_distintos_como_duplicados(
    tmp_path,
):
    archivo_a = tmp_path / "archivo_a.txt"
    archivo_b = tmp_path / "archivo_b.txt"

    archivo_a.write_bytes(b"contenido A")
    archivo_b.write_bytes(b"contenido B diferente")

    resultado = analizar_unidad(tmp_path)

    assert resultado["grupos_duplicados"] == []
    assert resultado["cantidad_grupos_duplicados"] == 0
    assert resultado["cantidad_archivos_duplicados"] == 0
    assert resultado["espacio_duplicado_bytes"] == 0

def test_analizar_unidad_registra_error_al_calcular_espacio_duplicado(
    tmp_path,
    monkeypatch,
):
    from src import analizador

    foto_a = tmp_path / "foto_a.jpg"
    foto_b = tmp_path / "foto_b.jpg"

    contenido = b"contenido duplicado"
    foto_a.write_bytes(contenido)
    foto_b.write_bytes(contenido)

    stat_original = Path.stat
    calculo_duplicados_iniciado = False

    def encontrar_duplicados_simulado(archivos, errores=None):
        nonlocal calculo_duplicados_iniciado
        calculo_duplicados_iniciado = True
        return [[foto_a, foto_b]]

    def stat_con_error(self, *args, **kwargs):
        if calculo_duplicados_iniciado and self == foto_a:
            raise PermissionError(
                "Acceso denegado al calcular duplicados"
            )

        return stat_original(self, *args, **kwargs)

    monkeypatch.setattr(
        analizador,
        "encontrar_duplicados",
        encontrar_duplicados_simulado,
    )

    monkeypatch.setattr(
        Path,
        "stat",
        stat_con_error,
    )

    resultado = analizar_unidad(tmp_path)

    assert resultado["cantidad_grupos_duplicados"] == 1
    assert resultado["cantidad_archivos_duplicados"] == 2
    assert resultado["espacio_duplicado_bytes"] == 0

    errores_duplicados = [
        error
        for error in resultado["errores"]
        if "calcular duplicados" in error["error"]
    ]

    assert len(errores_duplicados) >= 1
    assert all(
        error["ruta"] == foto_a
        for error in errores_duplicados
    )

def test_registrar_error_evitar_repetidos_y_conservar_distintos(
    tmp_path,
):
    errores = []
    archivo = tmp_path / "foto.jpg"

    registrar_error(errores, archivo, "Acceso denegado")
    registrar_error(errores, archivo, "Acceso denegado")
    registrar_error(errores, archivo, "Archivo no disponible")

    assert len(errores) == 2

    assert errores[0] == {
        "ruta": archivo,
        "error": "Acceso denegado",
    }

    assert errores[1] == {
        "ruta": archivo,
        "error": "Archivo no disponible",
    }

def test_analizar_unidad_registra_error_al_buscar_duplicados(
    tmp_path,
    monkeypatch,
):
    from src import duplicados

    archivo_a = tmp_path / "archivo_a.txt"
    archivo_b = tmp_path / "archivo_b.txt"
    archivo_c = tmp_path / "archivo_c.txt"

    contenido = b"contenido identico para la prueba"

    archivo_a.write_bytes(contenido)
    archivo_b.write_bytes(contenido)
    archivo_c.write_bytes(contenido)

    calcular_original = duplicados.calcular_sha256

    def calcular_con_error(ruta, tamano_bloque=1024 * 1024):
        if ruta == archivo_c:
            raise OSError("Acceso denegado durante el hash")

        return calcular_original(ruta, tamano_bloque)

    monkeypatch.setattr(
        duplicados,
        "calcular_sha256",
        calcular_con_error,
    )

    resultado = analizar_unidad(tmp_path)

    assert resultado["cantidad_grupos_duplicados"] == 1
    assert resultado["cantidad_archivos_duplicados"] == 2

    errores_duplicados = [
        error
        for error in resultado["errores"]
        if error["ruta"] == archivo_c
        and error["error"] == "Acceso denegado durante el hash"
    ]

    assert len(errores_duplicados) == 1
