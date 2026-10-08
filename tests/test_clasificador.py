from pathlib import Path

from src.clasificador import (
    clasificar_archivo,
    clasificar_archivos
)


def test_jpg_es_fotografia():
    assert clasificar_archivo(Path("foto.jpg")) == "fotografias"

def test_jpeg_es_fotografia():
    assert clasificar_archivo(Path("foto.jpeg")) == "fotografias"

def test_png_es_fotografia():
    assert clasificar_archivo(Path("imagen.png")) == "fotografias"

def test_mpg_es_video():
    assert clasificar_archivo(Path("video.mpg")) == "videos"

def test_mp4_es_video():
    assert clasificar_archivo(Path("video.mp4")) == "videos"

def test_mp3_es_audio():
    assert clasificar_archivo(Path("cancion.mp3")) == "audio"

def test_pdf_es_documento():
    assert clasificar_archivo(Path("factura.pdf")) == "documentos"

def test_docx_es_documento():
    assert clasificar_archivo(Path("documento.docx")) == "documentos"

def test_xlsx_es_hoja_de_calculo():
    assert clasificar_archivo(Path("datos.xlsx")) == "hojas_calculo"

def test_csv_es_hoja_de_calculo():
    assert clasificar_archivo(Path("datos.csv")) == "hojas_calculo"

def test_pptx_es_presentacion():
    assert clasificar_archivo(Path("presentacion.pptx")) == "presentaciones"

def test_zip_es_comprimido():
    assert clasificar_archivo(Path("backup.zip")) == "comprimidos"

def test_db_es_base_de_datos():
    assert clasificar_archivo(Path("datos.db")) == "bases_datos"

def test_thumbs_db_es_sistema():
    assert clasificar_archivo(Path("Thumbs.db")) == "sistema"

def test_ds_store_es_sistema():
    assert clasificar_archivo(Path(".DS_Store")) == "sistema"

def test_extension_desconocida_es_otros():
    assert clasificar_archivo(Path("archivo.xyz")) == "otros"

def test_archivo_sin_extension_es_otros():
    assert clasificar_archivo(Path("archivo_sin_extension")) == "otros"

def test_extension_mayuscula():
    assert clasificar_archivo(Path("FOTO.JPG")) == "fotografias"

def test_nombre_de_archivo_no_importa_para_db():
    assert clasificar_archivo(Path("mi_base_de_datos.db")) == "bases_datos"

def test_clasificar_archivos_agrupa_por_categoria(tmp_path):
    archivos = [
        tmp_path / "foto.jpg",
        tmp_path / "video.mp4",
        tmp_path / "cancion.mp3",
        tmp_path / "documento.pdf",
        tmp_path / "datos.xlsx",
        tmp_path / "presentacion.pptx",
        tmp_path / "archivo.zip",
        tmp_path / "base.db",
        tmp_path / "Thumbs.db",
        tmp_path / "archivo.xyz",
    ]

    resultado = clasificar_archivos(archivos)

    assert resultado["fotografias"] == [tmp_path / "foto.jpg"]
    assert resultado["videos"] == [tmp_path / "video.mp4"]
    assert resultado["audio"] == [tmp_path / "cancion.mp3"]
    assert resultado["documentos"] == [tmp_path / "documento.pdf"]
    assert resultado["hojas_calculo"] == [tmp_path / "datos.xlsx"]
    assert resultado["presentaciones"] == [tmp_path / "presentacion.pptx"]
    assert resultado["comprimidos"] == [tmp_path / "archivo.zip"]
    assert resultado["bases_datos"] == [tmp_path / "base.db"]
    assert resultado["sistema"] == [tmp_path / "Thumbs.db"]
    assert resultado["otros"] == [tmp_path / "archivo.xyz"]

def test_clasificar_archivos_devuelve_todas_las_categorias():
    resultado = clasificar_archivos([])

    categorias_esperadas = {
        "fotografias",
        "videos",
        "audio",
        "documentos",
        "hojas_calculo",
        "presentaciones",
        "comprimidos",
        "bases_datos",
        "sistema",
        "otros",
    }

    assert set(resultado.keys()) == categorias_esperadas