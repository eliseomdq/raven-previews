import pytest
from unittest.mock import patch, MagicMock
from workers.auditor import check_site_exists, audit_with_claude


def test_check_site_exists_no_url():
    assert check_site_exists("") is False
    assert check_site_exists(None) is False


def test_check_site_exists_bad_url():
    with patch("workers.auditor.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        assert check_site_exists("http://sitio-que-no-existe-123.com") is False


def test_check_site_exists_200():
    with patch("workers.auditor.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        assert check_site_exists("http://ejemplo.com") is True


def test_audit_with_claude_parses_response():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="NOTA: D | RAZON: Sitio desactualizado sin version mobile")]
    )

    with patch("workers.auditor.client", mock_client):
        nota, razon = audit_with_claude("Test SA", "Plomero", "http://test.com")

    assert nota == "D"
    assert "desactualizado" in razon
