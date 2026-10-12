
from pathlib import Path
from types import SimpleNamespace

from src.copiador import (
  seleccionar_archivo_a_conservar,
  copiar_sin_duplicados,
  calcular_sha256
)


def test_selecciona_archivo_con_fecha_de_creacion_mas_antigua(
    tmp_path,
    monkeypatch,
):
    archivo_antiguo = tmp_path / "antiguo.jpg"
    archivo_nuevo = tmp_path / "nuevo.jpg"

    archivo_antiguo.touch()
    archivo_nuevo.touch()

    fechas = {
        archivo_antiguo: SimpleNamespace(
            st_ctime=100,
            st_mtime=300,
        ),
        archivo_nuevo: SimpleNamespace(
            st_ctime=200,
            st_mtime=100,
        ),
    }

    monkeypatch.setattr(
        Path,
        "stat",
        lambda self: fechas[self],
    )

    conservado = seleccionar_archivo_a_conservar(
        [archivo_nuevo, archivo_antiguo]
    )

    assert conservado == archivo_antiguo


def test_desempata_por_fecha_de_modificacion(
    tmp_path,
    monkeypatch,
):
    archivo_antiguo = tmp_path / "a.jpg"
    archivo_nuevo = tmp_path / "b.jpg"

    archivo_antiguo.touch()
    archivo_nuevo.touch()

    fechas = {
        archivo_antiguo: SimpleNamespace(
            st_ctime=100,
            st_mtime=200,
        ),
        archivo_nuevo: SimpleNamespace(
            st_ctime=100,
            st_mtime=300,
        ),
    }

    monkeypatch.setattr(
        Path,
        "stat",
        lambda self: fechas[self],
    )

    conservado = seleccionar_archivo_a_conservar(
        [archivo_nuevo, archivo_antiguo]
    )

    assert conservado == archivo_antiguo


def test_desempata_por_ruta_alfabetica(
    tmp_path,
    monkeypatch,
):
    archivo_a = tmp_path / "a.jpg"
    archivo_b = tmp_path / "b.jpg"

    archivo_a.touch()
    archivo_b.touch()

    fechas = {
        archivo_a: SimpleNamespace(
            st_ctime=100,
            st_mtime=200,
        ),
        archivo_b: SimpleNamespace(
            st_ctime=100,
            st_mtime=200,
        ),
    }

    monkeypatch.setattr(
        Path,
        "stat",
        lambda self: fechas[self],
    )

    conservado = seleccionar_archivo_a_conservar(
        [archivo_b, archivo_a]
    )

    assert conservado == archivo_a


def test_devuelve_none_si_el_grupo_esta_vacio():
    assert seleccionar_archivo_a_conservar([]) is None


def test_registra_error_si_no_puede_consultar_un_archivo(
    tmp_path,
    monkeypatch,
):
    archivo = tmp_path / "archivo.jpg"
    archivo.touch()

    errores = []

    def fallar_stat(self):
        raise PermissionError("Acceso denegado")

    monkeypatch.setattr(Path, "stat", fallar_stat)

    conservado = seleccionar_archivo_a_conservar(
        [archivo],
        errores=errores,
    )

    assert conservado is None
    assert len(errores) == 1
    assert errores[0]["error"] == "Acceso denegado"


def test_copia_archivos_y_mantiene_carpetas_vacias(tmp_path):
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"

    carpeta_vacia = origen / "fotos" / "vacias"
    carpeta_vacia.mkdir(parents=True)

    archivo = origen / "documento.txt"
    archivo.write_text("contenido original", encoding="utf-8")

    resultado = copiar_sin_duplicados(origen, destino, [])

    assert (destino / "documento.txt").read_text(
        encoding="utf-8"
    ) == "contenido original"

    assert (destino / "fotos" / "vacias").is_dir()
    assert resultado["archivos_copiados"] == 1
    assert resultado["archivos_omitidos_duplicados"] == 0
    assert resultado["errores"] == []

    # El original sigue intacto.
    assert archivo.read_text(encoding="utf-8") == "contenido original"


def test_copia_un_solo_archivo_de_un_grupo_duplicado(tmp_path):
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"

    carpeta_fotos = origen / "fotos"
    carpeta_fotos.mkdir(parents=True)

    antiguo = origen / "informe.txt"
    reciente = carpeta_fotos / "informe_copia.txt"

    antiguo.write_bytes(b"contenido identico")
    reciente.write_bytes(b"contenido identico")

    # En esta prueba, se fija la fecha de modificación.
    # El archivo raíz tiene la ruta alfabética prioritaria.
    import os

    os.utime(antiguo, (1000000000, 1000000000))
    os.utime(reciente, (1100000000, 1100000000))

    resultado = copiar_sin_duplicados(
        origen,
        destino,
        [[antiguo, reciente]],
    )

    assert (destino / "informe.txt").exists()
    assert not (destino / "fotos" / "informe_copia.txt").exists()
    assert (destino / "fotos").is_dir()

    assert resultado["archivos_copiados"] == 1
    assert resultado["archivos_omitidos_duplicados"] == 1

    # Ambos archivos originales permanecen intactos.
    assert antiguo.read_bytes() == b"contenido identico"
    assert reciente.read_bytes() == b"contenido identico"


def test_no_copia_si_el_destino_ya_existe(tmp_path):
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"

    origen.mkdir()
    destino.mkdir()

    archivo_origen = origen / "documento.txt"
    archivo_origen.write_text("original", encoding="utf-8")

    archivo_existente = destino / "documento.txt"
    archivo_existente.write_text("contenido previo", encoding="utf-8")

    import pytest

    with pytest.raises(FileExistsError):
        copiar_sin_duplicados(origen, destino, [])

    assert archivo_existente.read_text(encoding="utf-8") == "contenido previo"
    assert archivo_origen.read_text(encoding="utf-8") == "original"


def test_limpia_archivo_temporal_si_falla_la_copia(tmp_path, monkeypatch):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo = origen / "documento.txt"
    archivo.write_text("contenido original", encoding="utf-8")

    def simular_error(entrada, salida):
        salida.write(b"contenido parcial")
        raise OSError("Error simulado durante la copia")

    monkeypatch.setattr(copiador.shutil, "copyfileobj", simular_error)

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert not (destino / "documento.txt").exists()
    assert list(destino.glob("*.copia_temporal")) == []
    assert not list(destino.glob(".copia_temporal_*"))
    assert resultado["archivos_copiados"] == 0
    assert len(resultado["errores"]) == 1
    assert archivo.read_text(encoding="utf-8") == "contenido original"


def test_rechaza_destino_que_contiene_al_origen(tmp_path):
    import pytest

    origen = tmp_path / "carpeta_padre" / "origen"
    destino = tmp_path / "carpeta_padre"

    origen.mkdir(parents=True)
    archivo = origen / "documento.txt"
    archivo.write_text("original", encoding="utf-8")

    with pytest.raises(ValueError, match="no pueden contenerse entre sí"):
        copiar_sin_duplicados(origen, destino, [])

    assert archivo.read_text(encoding="utf-8") == "original"
    assert list(origen.iterdir()) == [archivo]


def test_continua_copiando_si_un_archivo_falla(tmp_path, monkeypatch):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_problematico = origen / "a_problematico.txt"
    archivo_correcto = origen / "b_correcto.txt"

    archivo_problematico.write_text("contenido A", encoding="utf-8")
    archivo_correcto.write_text("contenido B", encoding="utf-8")

    copiar_original = copiador.shutil.copyfileobj

    def simular_error_selectivo(entrada, salida, *args, **kwargs):
        if Path(entrada.name).name == archivo_problematico.name:
            salida.write(b"contenido parcial")
            raise OSError("Error simulado de lectura o escritura")

        return copiar_original(entrada, salida, *args, **kwargs)

    monkeypatch.setattr(
        copiador.shutil,
        "copyfileobj",
        simular_error_selectivo,
    )

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert not (destino / archivo_problematico.name).exists()
    assert (
        destino / archivo_correcto.name
    ).read_text(encoding="utf-8") == "contenido B"

    assert resultado["archivos_copiados"] == 1
    assert len(resultado["errores"]) == 1
    assert archivo_problematico.read_text(encoding="utf-8") == "contenido A"


def test_omite_archivo_mayor_al_limite_fat32_y_continua(
    tmp_path,
    monkeypatch,
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_grande = origen / "archivo_grande.bin"
    archivo_correcto = origen / "archivo_correcto.txt"

    archivo_grande.write_bytes(b"contenido simulado")
    archivo_correcto.write_text("contenido correcto", encoding="utf-8")

    stat_original = Path.stat

    def simular_tamano_grande(ruta, *args, **kwargs):
        if ruta == archivo_grande:
            informacion = stat_original(ruta, *args, **kwargs)

            class StatSimulado:
                def __getattr__(self, atributo):
                    return getattr(informacion, atributo)

                @property
                def st_size(self):
                    return copiador.TAMANO_MAXIMO_FAT32 + 1

            return StatSimulado()

        return stat_original(ruta, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", simular_tamano_grande)

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert not (destino / archivo_grande.name).exists()
    assert (
        destino / archivo_correcto.name
    ).read_text(encoding="utf-8") == "contenido correcto"

    assert resultado["archivos_copiados"] == 1
    assert len(resultado["errores"]) == 1
    assert "FAT32" in resultado["errores"][0]["error"]

    assert archivo_grande.read_bytes() == b"contenido simulado"


def test_calcular_sha256_devuelve_el_hash_correcto(tmp_path):
    import hashlib

    archivo = tmp_path / "original.txt"
    contenido = b"Contenido de prueba para SHA-256."
    archivo.write_bytes(contenido)

    resultado = calcular_sha256(archivo)
    esperado = hashlib.sha256(contenido).hexdigest()

    assert resultado == esperado
    assert len(resultado) == 64


def test_calcular_sha256_detecta_contenidos_diferentes(tmp_path):
    archivo_original = tmp_path / "original.txt"
    archivo_copia = tmp_path / "copia.txt"

    archivo_original.write_bytes(b"Contenido original")
    archivo_copia.write_bytes(b"Contenido modificado")

    hash_original = calcular_sha256(archivo_original)
    hash_copia = calcular_sha256(archivo_copia)

    assert hash_original != hash_copia


def test_elimina_copia_si_falla_verificacion_sha256(tmp_path, monkeypatch):
    from src import copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_original = origen / "documento.txt"
    archivo_original.write_bytes(b"Contenido original")

    hash_real = copiador.calcular_sha256
    llamadas = 0

    def hash_alterado(archivo):
        nonlocal llamadas
        llamadas += 1

        if llamadas == 2:
            return "0" * 64

        return hash_real(archivo)

    monkeypatch.setattr(copiador, "calcular_sha256", hash_alterado)

    resultado = copiador.copiar_sin_duplicados(
        origen,
        destino,
        [],
    )

    assert not (destino / "documento.txt").exists()
    assert resultado["archivos_copiados"] == 0
    assert len(resultado["errores"]) == 1
    assert "SHA-256" in resultado["errores"][0]["error"]
    assert archivo_original.read_bytes() == b"Contenido original"


def test_continua_copiando_si_falla_la_creacion_de_una_carpeta(
    tmp_path,
    monkeypatch,
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"

    (origen / "a_problemática").mkdir(parents=True)
    (origen / "b_correcta").mkdir()

    archivo_problematico = (
        origen / "a_problemática" / "foto.txt"
    )
    archivo_correcto = origen / "b_correcta" / "documento.txt"

    archivo_problematico.write_text(
        "contenido A",
        encoding="utf-8",
    )
    archivo_correcto.write_text(
        "contenido B",
        encoding="utf-8",
    )

    mkdir_original = Path.mkdir

    def simular_error_selectivo(
        ruta,
        *args,
        **kwargs,
    ):
        if ruta == destino / "a_problemática":
            raise OSError("Error simulado al crear la carpeta")

        return mkdir_original(ruta, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", simular_error_selectivo)

    resultado = copiador.copiar_sin_duplicados(
        origen,
        destino,
        [],
    )

    assert not (
        destino / "a_problemática" / "foto.txt"
    ).exists()

    assert (
        destino / "b_correcta" / "documento.txt"
    ).read_text(encoding="utf-8") == "contenido B"

    assert resultado["archivos_copiados"] == 1
    assert resultado["copia_completa"] is False
    assert resultado["errores"]

    assert archivo_problematico.read_text(
        encoding="utf-8"
    ) == "contenido A"

    assert archivo_correcto.read_text(
        encoding="utf-8"
    ) == "contenido B"


def test_continua_copiando_si_hay_una_carpeta_del_origen_inaccesible(
    tmp_path,
    monkeypatch,
):
    import os
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"

    carpeta_problemática = origen / "a_inaccesible"
    carpeta_correcta = origen / "b_correcta"

    carpeta_problemática.mkdir(parents=True)
    carpeta_correcta.mkdir()

    archivo_problematico = carpeta_problemática / "foto.txt"
    archivo_correcto = carpeta_correcta / "documento.txt"

    archivo_problematico.write_text(
        "contenido A",
        encoding="utf-8",
    )
    archivo_correcto.write_text(
        "contenido B",
        encoding="utf-8",
    )

    walk_original = os.walk

    def simular_error_recorrido(
        ruta,
        *args,
        **kwargs,
    ):
        onerror = kwargs.get("onerror")

        def recorrer_con_error(directorio, *args_recorrido, **kwargs_recorrido):
            if onerror is not None:
                onerror(
                    PermissionError(
                        13,
                        "Acceso denegado simulado",
                        str(carpeta_problemática),
                    )
                )

            yield from walk_original(
                directorio,
                *args_recorrido,
                **kwargs_recorrido,
            )

        return recorrer_con_error(ruta, *args, **kwargs)

    monkeypatch.setattr(os, "walk", simular_error_recorrido)

    resultado = copiador.copiar_sin_duplicados(
        origen,
        destino,
        [],
    )

    assert (
        destino / "b_correcta" / "documento.txt"
    ).read_text(encoding="utf-8") == "contenido B"

    assert resultado["copia_completa"] is False
    assert resultado["errores"]
    assert any(
        "Acceso denegado simulado" in error["error"]
        for error in resultado["errores"]
    )

    assert archivo_problematico.read_text(
        encoding="utf-8"
    ) == "contenido A"

    assert archivo_correcto.read_text(
        encoding="utf-8"
    ) == "contenido B"


def test_omite_todo_el_grupo_si_no_puede_consultar_fechas(
    tmp_path,
    monkeypatch,
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_a = origen / "a.txt"
    archivo_b = origen / "b.txt"

    archivo_a.write_bytes(b"contenido duplicado")
    archivo_b.write_bytes(b"contenido duplicado")

    stat_original = Path.stat

    def simular_error_selectivo(ruta, *args, **kwargs):
        if ruta == archivo_a:
            raise PermissionError("Acceso denegado simulado")

        return stat_original(ruta, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", simular_error_selectivo)

    resultado = copiador.copiar_sin_duplicados(
        origen,
        destino,
        [[archivo_a, archivo_b]],
    )

    assert not (destino / "a.txt").exists()
    assert not (destino / "b.txt").exists()

    assert resultado["archivos_copiados"] == 0
    assert resultado["copia_completa"] is False
    assert resultado["errores"]

    assert archivo_a.read_bytes() == b"contenido duplicado"
    assert archivo_b.read_bytes() == b"contenido duplicado"


def test_detecta_cambio_del_original_durante_la_copia(
    tmp_path,
    monkeypatch,
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_original = origen / "documento.txt"
    archivo_original.write_bytes(b"Contenido original")

    hash_real = copiador.calcular_sha256
    llamadas = 0

    def cambiar_original_antes_de_verificar(archivo):
        nonlocal llamadas
        llamadas += 1

        if llamadas == 1:
            # Simula que otro proceso cambia el original
            # después de que se haya preparado la copia.
            archivo_original.write_bytes(b"Contenido modificado")

        return hash_real(archivo)

    monkeypatch.setattr(
        copiador,
        "calcular_sha256",
        cambiar_original_antes_de_verificar,
    )

    resultado = copiador.copiar_sin_duplicados(
        origen,
        destino,
        [],
    )

    assert not (destino / "documento.txt").exists()
    assert resultado["archivos_copiados"] == 0
    assert resultado["copia_completa"] is False
    assert any(
        "SHA-256" in error["error"]
        for error in resultado["errores"]
    )

    # El cambio fue provocado por la prueba; la función de copia
    # no debe restaurar ni modificar el contenido del original.
    assert archivo_original.read_bytes() == b"Contenido modificado"


def test_registra_error_si_falla_la_limpieza_del_temporal(tmp_path, monkeypatch):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo = origen / "documento.txt"
    archivo.write_text("contenido original", encoding="utf-8")

    unlink_original = Path.unlink

    def simular_error_de_limpieza(self, *args, **kwargs):
        if self.name.startswith(".copia_temporal_"):
            raise OSError("Error simulado al eliminar el temporal")

        return unlink_original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", simular_error_de_limpieza)

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert (destino / "documento.txt").read_text(encoding="utf-8") == (
        "contenido original"
    )
    assert archivo.read_text(encoding="utf-8") == "contenido original"
    assert resultado["archivos_copiados"] == 1
    assert resultado["errores"]
    assert resultado["copia_completa"] is False
    assert any(
        "Error simulado al eliminar el temporal" in error["error"]
        for error in resultado["errores"]
    )


def test_no_sobrescribe_archivo_que_aparece_durante_la_copia(
    tmp_path, monkeypatch
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    (origen / "documento.txt").write_text(
        "contenido original", encoding="utf-8"
    )
    (origen / "otro.txt").write_text(
        "segundo archivo", encoding="utf-8"
    )

    abrir_original = Path.open
    archivo_creado = False

    def simular_archivo_existente(self, mode="r", *args, **kwargs):
        nonlocal archivo_creado

        if (
            self == destino / "documento.txt"
            and mode == "xb"
            and not archivo_creado
        ):
            archivo_creado = True
            self.write_text("contenido preexistente", encoding="utf-8")

        return abrir_original(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", simular_archivo_existente)

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert (destino / "documento.txt").read_text(
        encoding="utf-8"
    ) == "contenido preexistente"

    assert (destino / "otro.txt").read_text(
        encoding="utf-8"
    ) == "segundo archivo"

    assert (origen / "documento.txt").read_text(
        encoding="utf-8"
    ) == "contenido original"

    assert resultado["archivos_copiados"] == 1
    assert resultado["copia_completa"] is False
    assert resultado["errores"]
    assert any(
        error["ruta"] == destino / "documento.txt"
        for error in resultado["errores"]
    )


def test_elimina_copia_incompleta_si_falla_la_escritura(
    tmp_path, monkeypatch
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo = origen / "documento.txt"
    archivo.write_text("contenido original", encoding="utf-8")

    (origen / "otro.txt").write_text(
        "segundo archivo", encoding="utf-8"
    )

    abrir_original = Path.open
    escritura_fallida = False

    class ArchivoConFallo:
        def __init__(self, archivo):
            self.archivo = archivo

        def __enter__(self):
            self.contexto = abrir_original(self.archivo, "xb")
            self.contexto.__enter__()
            return self

        def __exit__(self, tipo, valor, traceback):
            return self.contexto.__exit__(tipo, valor, traceback)

        def write(self, contenido):
            nonlocal escritura_fallida

            if (
                self.archivo.name == "documento.txt"
                and not escritura_fallida
            ):
                escritura_fallida = True
                self.contexto.write(contenido[:3])
                raise OSError("Error simulado durante la escritura")

            return self.contexto.write(contenido)

        def __getattr__(self, nombre):
            return getattr(self.contexto, nombre)


    def abrir_con_fallo(self, mode="r", *args, **kwargs):
        if mode == "xb" and self.name == "documento.txt":
            return ArchivoConFallo(self)

        return abrir_original(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", abrir_con_fallo)

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert not (destino / "documento.txt").exists()
    assert (destino / "otro.txt").read_text(
        encoding="utf-8"
    ) == "segundo archivo"
    assert archivo.read_text(encoding="utf-8") == "contenido original"
    assert resultado["archivos_copiados"] == 1
    assert resultado["copia_completa"] is False
    assert resultado["errores"]
    assert escritura_fallida


def test_limpieza_por_error_no_elimina_otros_archivos_del_destino(
    tmp_path, monkeypatch
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_original = origen / "documento.txt"
    archivo_original.write_text("contenido original", encoding="utf-8")

    copiar_archivo_original = copiador.shutil.copyfileobj
    archivo_ajeno = destino / "archivo_importante.txt"

    def simular_error_de_copia(entrada, salida):
        # Simula que otro proceso crea un archivo ajeno en el destino.
        archivo_ajeno.write_text("no eliminar", encoding="utf-8")

        # Simula una escritura parcial antes del error.
        salida.write(b"contenido parcial")
        raise OSError("Error simulado durante la copia")

    monkeypatch.setattr(
        copiador.shutil, "copyfileobj", simular_error_de_copia
    )

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert archivo_original.read_text(encoding="utf-8") == (
        "contenido original"
    )
    assert not (destino / "documento.txt").exists()
    assert archivo_ajeno.read_text(encoding="utf-8") == "no eliminar"
    assert resultado["archivos_copiados"] == 0
    assert resultado["copia_completa"] is False
    assert resultado["errores"]


def test_continua_si_falla_la_consulta_del_tamano_de_un_archivo(
    tmp_path, monkeypatch
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_problematico = origen / "restringido.txt"
    archivo_problematico.write_text(
        "contenido restringido", encoding="utf-8"
    )

    archivo_valido = origen / "valido.txt"
    archivo_valido.write_text("contenido valido", encoding="utf-8")

    stat_original = Path.stat

    def simular_error_de_stat(self, *args, **kwargs):
        if self == archivo_problematico:
            raise PermissionError("Permiso denegado al consultar el tamaño")

        return stat_original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", simular_error_de_stat)

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert not (destino / "restringido.txt").exists()
    assert (destino / "valido.txt").read_text(
        encoding="utf-8"
    ) == "contenido valido"

    assert archivo_problematico.read_text(
        encoding="utf-8"
    ) == "contenido restringido"

    assert resultado["archivos_copiados"] == 1
    assert resultado["copia_completa"] is False
    assert resultado["errores"]
    assert any(
        "Permiso denegado al consultar el tamaño" in error["error"]
        for error in resultado["errores"]
    )


def test_continua_si_falla_la_lectura_de_un_archivo_para_sha256(
    tmp_path, monkeypatch
):
    import src.copiador as copiador

    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()

    archivo_problematico = origen / "restringido.txt"
    archivo_problematico.write_text(
        "contenido restringido", encoding="utf-8"
    )

    archivo_valido = origen / "valido.txt"
    archivo_valido.write_text("contenido valido", encoding="utf-8")

    calcular_sha256_original = copiador.calcular_sha256

    def simular_error_de_lectura(archivo):
        if Path(archivo) == archivo_problematico:
            raise PermissionError("Permiso denegado al leer el archivo")

        return calcular_sha256_original(archivo)

    monkeypatch.setattr(
        copiador, "calcular_sha256", simular_error_de_lectura
    )

    resultado = copiador.copiar_sin_duplicados(origen, destino, [])

    assert not (destino / "restringido.txt").exists()
    assert (destino / "valido.txt").read_text(
        encoding="utf-8"
    ) == "contenido valido"

    assert archivo_problematico.read_text(
        encoding="utf-8"
    ) == "contenido restringido"

    assert resultado["archivos_copiados"] == 1
    assert resultado["copia_completa"] is False
    assert resultado["errores"]
    assert any(
        "Permiso denegado al leer el archivo" in error["error"]
        for error in resultado["errores"]
    )
    