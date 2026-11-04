
import src.main as modulo_main
from src.main import main


def configurar_proyecto_temporal(monkeypatch, tmp_path):
    """
    Configura un proyecto temporal para que los informes
    de las pruebas no se guarden en el proyecto real.
    """
    proyecto = tmp_path / "proyecto"
    carpeta_src = proyecto / "src"
    carpeta_src.mkdir(parents=True)

    monkeypatch.setattr(
        modulo_main,
        "__file__",
        str(carpeta_src / "main.py"),
    )

    return proyecto


def obtener_carpeta_escaneo(ubicacion):
    carpetas = list(
        (ubicacion / "Informes_escaneo").glob("ESCANEO_*")
    )

    assert len(carpetas) == 1

    return carpetas[0]


def test_main_con_ruta_vacia(capsys, monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    main()

    salida = capsys.readouterr().out

    assert "No se indicó ninguna ruta." in salida


def test_main_con_ruta_inexistente(capsys, monkeypatch, tmp_path):
    ruta_inexistente = tmp_path / "no_existe"

    monkeypatch.setattr(
        "builtins.input",
        lambda _: str(ruta_inexistente),
    )

    main()

    salida = capsys.readouterr().out

    assert "Error durante el análisis:" in salida
    assert "no existe" in salida


def test_main_con_ruta_que_es_un_archivo(
    capsys,
    monkeypatch,
    tmp_path,
):
    archivo = tmp_path / "archivo.txt"
    archivo.touch()

    monkeypatch.setattr(
        "builtins.input",
        lambda _: str(archivo),
    )

    main()

    salida = capsys.readouterr().out

    assert "Error durante el análisis:" in salida
    assert "no es un directorio" in salida


def test_main_con_ruta_valida(
    capsys,
    monkeypatch,
    tmp_path,
):
    proyecto = configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto.jpg").write_bytes(b"foto original")

    respuestas = iter([
        str(origen),
        "n",
        "",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "RESUMEN DEL ESCANEO" in salida
    assert "Archivos encontrados:" in salida
    assert "Fotografías:" in salida
    assert "No se realizará ninguna copia." in salida
    assert "Informe Excel generado:" in salida

    carpeta_escaneo = obtener_carpeta_escaneo(proyecto)

    assert list(
        carpeta_escaneo.glob("informe_escaneo_*.xlsx")
    )

    assert not (carpeta_escaneo / "Archivos").exists()

    assert (origen / "foto.jpg").read_bytes() == b"foto original"


def test_main_ignora_espacios_alrededor_de_la_ruta(
    capsys,
    monkeypatch,
    tmp_path,
):
    proyecto = configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "documento.pdf").touch()

    ruta_con_espacios = f"   {origen}   "

    respuestas = iter([
        ruta_con_espacios,
        "n",
        "",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "RESUMEN DEL ESCANEO" in salida
    assert "Documentos:" in salida

    carpeta_escaneo = obtener_carpeta_escaneo(proyecto)

    assert list(
        carpeta_escaneo.glob("informe_escaneo_*.xlsx")
    )


def test_main_copia_archivos_sin_modificar_el_origen(
    capsys,
    monkeypatch,
    tmp_path,
):
    proyecto = configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()

    contenido = b"foto original"
    (origen / "foto.jpg").write_bytes(contenido)

    respuestas = iter([
        str(origen),
        "s",
        "",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "RESUMEN DE LA COPIA" in salida
    assert "Archivos copiados:" in salida
    assert "Informe Excel generado:" in salida

    carpeta_escaneo = obtener_carpeta_escaneo(proyecto)
    carpeta_archivos = carpeta_escaneo / "Archivos"

    assert carpeta_archivos.is_dir()
    assert (carpeta_archivos / "foto.jpg").read_bytes() == contenido

    assert list(
        carpeta_escaneo.glob("informe_escaneo_*.xlsx")
    )

    assert (origen / "foto.jpg").read_bytes() == contenido


def test_main_usa_ubicacion_personalizada(
    capsys,
    monkeypatch,
    tmp_path,
):
    configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto.jpg").write_bytes(b"foto original")

    ubicacion_personalizada = tmp_path / "resultados"
    ubicacion_personalizada.mkdir()

    respuestas = iter([
        str(origen),
        "n",
        str(ubicacion_personalizada),
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "Informe Excel generado:" in salida

    carpeta_escaneo = obtener_carpeta_escaneo(
        ubicacion_personalizada
    )

    assert list(
        carpeta_escaneo.glob("informe_escaneo_*.xlsx")
    )

    assert (origen / "foto.jpg").read_bytes() == b"foto original"


def test_main_rechaza_ubicacion_personalizada_inexistente(
    capsys,
    monkeypatch,
    tmp_path,
):
    configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto.jpg").touch()

    ubicacion_inexistente = tmp_path / "no_existe"

    respuestas = iter([
        str(origen),
        "n",
        str(ubicacion_inexistente),
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "La ubicación indicada no existe" in salida
    assert not ubicacion_inexistente.exists()


def test_main_rechaza_ubicacion_personalizada_dentro_del_origen(
    capsys,
    monkeypatch,
    tmp_path,
):
    configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto.jpg").write_bytes(b"foto original")

    ubicacion_interna = origen / "informes"

    ubicacion_interna.mkdir()

    respuestas = iter([
        str(origen),
        "n",
        str(ubicacion_interna),
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "La ubicación elegida no es válida" in salida
    
    # La carpeta original debe conservarse.
    assert ubicacion_interna.exists()

    # No deben generarse resultados dentro del origen.
    assert not (ubicacion_interna / "Informes_escaneo").exists()

    assert (origen / "foto.jpg").read_bytes() == b"foto original"


def test_main_no_sobrescribe_contenido_de_ubicacion_personalizada(
    capsys,
    monkeypatch,
    tmp_path,
):
    configurar_proyecto_temporal(
        monkeypatch,
        tmp_path,
    )

    origen = tmp_path / "origen"
    origen.mkdir()

    contenido_original = b"foto original"
    (origen / "foto.jpg").write_bytes(contenido_original)

    ubicacion_personalizada = tmp_path / "resultados"
    ubicacion_personalizada.mkdir()

    archivo_existente = ubicacion_personalizada / "documento.txt"
    archivo_existente.write_text(
        "contenido previo",
        encoding="utf-8",
    )

    respuestas = iter([
        str(origen),
        "s",
        str(ubicacion_personalizada),
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "RESUMEN DE LA COPIA" in salida
    assert "Informe Excel generado:" in salida

    carpeta_escaneo = obtener_carpeta_escaneo(
        ubicacion_personalizada
    )

    carpeta_archivos = carpeta_escaneo / "Archivos"

    assert (carpeta_archivos / "foto.jpg").read_bytes() == contenido_original

    assert archivo_existente.read_text(
        encoding="utf-8"
    ) == "contenido previo"

    assert (origen / "foto.jpg").read_bytes() == contenido_original
