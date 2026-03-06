import pytest
from workers.outreach import get_problema, WA_TEMPLATE


def test_get_problema_F():
    assert "no tiene sitio web" in get_problema("F")


def test_get_problema_D():
    assert "desactualizado" in get_problema("D")


def test_get_problema_C():
    assert "mejorar" in get_problema("C")


def test_wa_template_format():
    msg = WA_TEMPLATE.format(nombre="Juan", url_preview="https://preview.com")
    assert "Juan" in msg
    assert "https://preview.com" in msg
