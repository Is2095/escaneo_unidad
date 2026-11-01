from src.main import main


def test_main_con_ruta_vacia(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")

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

    assert "Error:" in salida
    assert "no existe" in salida


def test_main_con_ruta_que_es_un_archivo(capsys, monkeypatch, tmp_path):
    archivo = tmp_path / "archivo.txt"
    archivo.touch()

    monkeypatch.setattr(
        "builtins.input",
        lambda _: str(archivo),
    )

    main()

    salida = capsys.readouterr().out

    assert "Error:" in salida
    assert "no es un directorio" in salida


def test_main_con_ruta_valida(capsys, monkeypatch, tmp_path):
    archivo = tmp_path / "foto.jpg"
    archivo.touch()

    monkeypatch.setattr(
        "builtins.input",
        lambda _: str(tmp_path),
    )

    main()

    salida = capsys.readouterr().out

    assert "RESUMEN DEL ESCANEO" in salida
    assert "Archivos encontrados:" in salida
    assert "Fotografías:" in salida


def test_main_ignora_espacios_alrededor_de_la_ruta(
    capsys,
    monkeypatch,
    tmp_path,
):
    archivo = tmp_path / "documento.pdf"
    archivo.touch()

    ruta_con_espacios = f"   {tmp_path}   "

    monkeypatch.setattr(
        "builtins.input",
        lambda _: ruta_con_espacios,
    )

    main()

    salida = capsys.readouterr().out

    assert "RESUMEN DEL ESCANEO" in salida
    assert "Documentos:" in salida


def test_main_no_copia_si_el_destino_ya_existe(
    capsys,
    monkeypatch,
    tmp_path,
):
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"

    origen.mkdir()
    (origen / "foto.jpg").write_bytes(b"foto original")

    destino.mkdir()
    archivo_existente = destino / "documento.txt"
    archivo_existente.write_text(
        "contenido previo",
        encoding="utf-8",
    )

    respuestas = iter([
        str(origen),  # Ruta que se va a analizar
        "s",           # Aceptar la copia
        str(destino),  # Destino que ya existe
        "",            # Usar ubicación predeterminada del informe
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "No se pudo iniciar la copia:" in salida
    assert archivo_existente.read_text(encoding="utf-8") == "contenido previo"
    assert (origen / "foto.jpg").read_bytes() == b"foto original"
    assert not (destino / "foto.jpg").exists()


def test_main_informa_error_si_la_ubicacion_del_informe_no_existe(
    capsys,
    monkeypatch,
    tmp_path,
):
    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto.jpg").write_bytes(b"foto original")

    ubicacion_inexistente = tmp_path / "carpeta_inexistente"

    respuestas = iter([
        str(origen),                 # Ruta que se va a analizar
        "n",                          # No realizar la copia
        str(ubicacion_inexistente),  # Ubicación del informe
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "No se pudo generar el informe Excel:" in salida
    assert not ubicacion_inexistente.exists()
    assert (origen / "foto.jpg").read_bytes() == b"foto original"


def test_main_rechaza_ubicacion_del_informe_dentro_del_origen(
    capsys,
    monkeypatch,
    tmp_path,
):
    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "foto.jpg").write_bytes(b"foto original")

    ubicacion_interna = origen / "informes"

    respuestas = iter([
        str(origen),                 # Ruta que se va a analizar
        "n",                          # No realizar la copia
        str(ubicacion_interna),      # Ubicación dentro del origen
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(respuestas),
    )

    main()

    salida = capsys.readouterr().out

    assert "La ubicación del informe debe estar fuera" in salida
    assert not ubicacion_interna.exists()
    assert (origen / "foto.jpg").read_bytes() == b"foto original"
    