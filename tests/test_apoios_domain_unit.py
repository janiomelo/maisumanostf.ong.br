import pytest

from app.dados.protocolo import abreviar_protocolo, gerar_protocolo_apoio


@pytest.mark.unit
def test_gerar_protocolo_apoio_retorna_hash_hexadecimal_64():
    protocolo = gerar_protocolo_apoio()

    assert len(protocolo) == 64
    assert all(c in "0123456789abcdef" for c in protocolo)


@pytest.mark.unit
def test_abreviar_protocolo_retorna_prefixo_no_tamanho_padrao():
    protocolo = "abcdef0123456789" * 4

    assert abreviar_protocolo(protocolo) == "abcdef012345"
