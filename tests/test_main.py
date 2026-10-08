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
