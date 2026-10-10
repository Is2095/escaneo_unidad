
from src.duplicados import encontrar_duplicados


def test_encontrar_duplicados_identifica_archivos_identicos(
    tmp_path,
):
    carpeta_a = tmp_path / "carpeta_a"
    carpeta_b = tmp_path / "carpeta_b"

    carpeta_a.mkdir()
    carpeta_b.mkdir()

    archivo_a = carpeta_a / "foto_original.jpg"
    archivo_b = carpeta_b / "foto_copia.jpg"

    contenido = b"contenido de prueba para duplicados"

    archivo_a.write_bytes(contenido)
    archivo_b.write_bytes(contenido)

    grupos = encontrar_duplicados([archivo_a, archivo_b])

    assert len(grupos) == 1
    assert set(grupos[0]) == {archivo_a, archivo_b}


def test_encontrar_duplicados_ignora_archivos_distintos(
    tmp_path,
):
    archivo_a = tmp_path / "archivo_a.txt"
    archivo_b = tmp_path / "archivo_b.txt"

    archivo_a.write_bytes(b"contenido A")
    archivo_b.write_bytes(b"contenido B")

    grupos = encontrar_duplicados([archivo_a, archivo_b])

    assert grupos == []


def test_encontrar_duplicados_reconoce_archivos_vacios(
    tmp_path,
):
    archivo_a = tmp_path / "vacio_a.txt"
    archivo_b = tmp_path / "vacio_b.txt"

    archivo_a.write_bytes(b"")
    archivo_b.write_bytes(b"")

    grupos = encontrar_duplicados([archivo_a, archivo_b])

    assert len(grupos) == 1
    assert set(grupos[0]) == {archivo_a, archivo_b}


def test_encontrar_duplicados_ignora_archivo_inaccesible(
    tmp_path,
    monkeypatch,
):
    from src import duplicados

    archivo_a = tmp_path / "archivo_a.txt"
    archivo_b = tmp_path / "archivo_b.txt"
    archivo_c = tmp_path / "archivo_c.txt"

    archivo_a.write_bytes(b"contenido repetido")
    archivo_b.write_bytes(b"contenido repetido")
    archivo_c.write_bytes(b"contenido repetido")

    calcular_original = duplicados.calcular_sha256

    def calcular_con_error(ruta, tamano_bloque=1024 * 1024):
        if ruta == archivo_c:
            raise OSError("Acceso denegado")

        return calcular_original(ruta, tamano_bloque)

    monkeypatch.setattr(
        duplicados,
        "calcular_sha256",
        calcular_con_error,
    )

    grupos = duplicados.encontrar_duplicados(
        [archivo_a, archivo_b, archivo_c]
    )

    assert len(grupos) == 1
    assert set(grupos[0]) == {archivo_a, archivo_b}


def test_encontrar_duplicados_registra_error_de_archivo_inaccesible(
    tmp_path,
    monkeypatch,
):
    from src import duplicados

    archivo_a = tmp_path / "archivo_a.txt"
    archivo_b = tmp_path / "archivo_b.txt"
    archivo_c = tmp_path / "archivo_c.txt"

    archivo_a.write_bytes(b"contenido repetido")
    archivo_b.write_bytes(b"contenido repetido")
    archivo_c.write_bytes(b"contenido repetido")

    calcular_original = duplicados.calcular_sha256

    def calcular_con_error(ruta, tamano_bloque=1024 * 1024):
        if ruta == archivo_c:
            raise OSError("Acceso denegado")

        return calcular_original(ruta, tamano_bloque)

    monkeypatch.setattr(
        duplicados,
        "calcular_sha256",
        calcular_con_error,
    )

    errores = []

    grupos = duplicados.encontrar_duplicados(
        [archivo_a, archivo_b, archivo_c],
        errores=errores,
    )

    assert len(grupos) == 1
    assert set(grupos[0]) == {archivo_a, archivo_b}

    assert errores == [
        {
            "ruta": archivo_c,
            "error": "Acceso denegado",
        }
    ]


def test_encontrar_duplicados_registra_error_al_consultar_tamano(
    tmp_path,
    monkeypatch,
):
    from pathlib import Path
    from src import duplicados

    archivo_a = tmp_path / "archivo_a.txt"
    archivo_b = tmp_path / "archivo_b.txt"
    archivo_c = tmp_path / "archivo_c.txt"

    contenido = b"contenido identico"

    archivo_a.write_bytes(contenido)
    archivo_b.write_bytes(contenido)
    archivo_c.write_bytes(contenido)

    stat_original = Path.stat

    def stat_con_error(self, *args, **kwargs):
        if self == archivo_c:
            raise PermissionError("Acceso denegado al consultar tamano")

        return stat_original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat_con_error)

    errores = []

    grupos = duplicados.encontrar_duplicados(
        [archivo_a, archivo_b, archivo_c],
        errores=errores,
    )

    assert len(grupos) == 1
    assert set(grupos[0]) == {archivo_a, archivo_b}

    assert errores == [
        {
            "ruta": archivo_c,
            "error": "Acceso denegado al consultar tamano",
        }
    ]
