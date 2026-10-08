from pathlib import Path

import pytest

from src.escaneo import escanear_directorio


def test_escanear_directorio_vacio(tmp_path):
    resultado = escanear_directorio(tmp_path)

    assert resultado["directorios"] == []
    assert resultado["archivos"] == []

def test_escanear_directorio_encuentra_archivo(tmp_path):
    archivo = tmp_path / "foto.jpg"
    archivo.touch()

    resultado = escanear_directorio(tmp_path)

    assert resultado["archivos"] == [archivo]
    assert resultado["directorios"] == []

def test_escanear_directorio_encuentra_subdirectorio(tmp_path):
    subdirectorio = tmp_path / "fotos"
    subdirectorio.mkdir()

    resultado = escanear_directorio(tmp_path)

    assert resultado["directorios"] == [subdirectorio]
    assert resultado["archivos"] == []

def test_escanear_directorio_es_recursivo(tmp_path):
    subdirectorio = tmp_path / "fotos"
    subdirectorio.mkdir()

    subsubdirectorio = subdirectorio / "2026"
    subsubdirectorio.mkdir()

    archivo = subsubdirectorio / "foto.jpg"
    archivo.touch()

    resultado = escanear_directorio(tmp_path)

    assert subdirectorio in resultado["directorios"]
    assert subsubdirectorio in resultado["directorios"]
    assert archivo in resultado["archivos"]

def test_escanear_directorio_encuentra_varios_archivos(tmp_path):
    archivo1 = tmp_path / "foto.jpg"
    archivo2 = tmp_path / "video.mp4"
    archivo3 = tmp_path / "documento.pdf"

    archivo1.touch()
    archivo2.touch()
    archivo3.touch()

    resultado = escanear_directorio(tmp_path)

    assert len(resultado["archivos"]) == 3
    assert archivo1 in resultado["archivos"]
    assert archivo2 in resultado["archivos"]
    assert archivo3 in resultado["archivos"]

def test_escanear_directorio_incluye_archivo_sin_extension(tmp_path):
    archivo = tmp_path / "archivo_sin_extension"
    archivo.touch()

    resultado = escanear_directorio(tmp_path)

    assert archivo in resultado["archivos"]

def test_escanear_directorio_incluye_archivos_ocultos_o_especiales(tmp_path):
    archivo = tmp_path / "Thumbs.db"
    archivo.touch()

    resultado = escanear_directorio(tmp_path)

    assert archivo in resultado["archivos"]

def test_escanear_directorio_no_incluye_la_raiz(tmp_path):
    resultado = escanear_directorio(tmp_path)

    assert tmp_path not in resultado["directorios"]

def test_escanear_directorio_ruta_inexistente():
    ruta = Path("C:/esta_ruta_no_deberia_existir_123456")

    with pytest.raises(ValueError, match="no existe"):
        escanear_directorio(ruta)

def test_escanear_directorio_recibe_archivo_en_lugar_de_directorio(tmp_path):
    archivo = tmp_path / "foto.jpg"
    archivo.touch()

    with pytest.raises(ValueError, match="no es un directorio"):
        escanear_directorio(archivo)

def test_escanear_directorio_incluye_lista_de_errores(tmp_path):
    resultado = escanear_directorio(tmp_path)

    assert "errores" in resultado
    assert resultado["errores"] == []
    
def test_escanear_directorio_registra_errores(tmp_path, monkeypatch):
    ruta_protegida = tmp_path / "carpeta_protegida"

    error = PermissionError(
        13,
        "Acceso denegado",
        str(ruta_protegida),
    )

    def os_walk_con_error(*args, **kwargs):
        onerror = kwargs["onerror"]
        onerror(error)

        yield (
            str(tmp_path),
            [],
            [],
        )

    monkeypatch.setattr(
        "src.escaneo.os.walk",
        os_walk_con_error,
    )

    resultado = escanear_directorio(tmp_path)

    assert len(resultado["errores"]) == 1
    assert resultado["errores"][0]["ruta"] == ruta_protegida
    assert "Acceso denegado" in resultado["errores"][0]["error"]