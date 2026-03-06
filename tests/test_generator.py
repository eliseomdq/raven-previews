import pytest
from unittest.mock import patch, MagicMock
from workers.generator import generate_html, save_preview
import os
import tempfile


def test_generate_html_cleans_markdown():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="```html\n<!DOCTYPE html><html></html>\n```")]
    )

    with patch("workers.generator.client", mock_client):
        html = generate_html("Test SA", "Plomero", "MdP", "223000", "F")

    assert html.startswith("<!DOCTYPE html>")
    assert "```" not in html


def test_generate_html_returns_doctype():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="<!DOCTYPE html><html><head></head><body></body></html>")]
    )

    with patch("workers.generator.client", mock_client):
        html = generate_html("Restaurante El Gaucho", "Restaurante", "Mendoza", "261000", "D")

    assert "<!DOCTYPE html>" in html


def test_save_preview_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("workers.generator.PREVIEWS_DIR", tmpdir):
            path = save_preview(999, "<html>test</html>")
            assert os.path.exists(path)
            with open(path) as f:
                assert f.read() == "<html>test</html>"
