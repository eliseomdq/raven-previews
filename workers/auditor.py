import anthropic
import httpx
from workers.celery_app import app
from db.database import get_session
from db.models import Business
from config import CLAUDE_API_KEY
import logging

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

AUDIT_PROMPT = """Eres un experto en diseño web y UX. Analiza este sitio web de un negocio local.

URL: {url}
Nombre del negocio: {nombre}
Categoria: {categoria}

Basandote en lo que sabes sobre sitios web de negocios locales en Argentina, evalua:
1. Diseno visual (moderno vs desactualizado)
2. Adaptacion mobile (responsive o no)
3. Claridad del mensaje y CTA
4. Velocidad percibida (uso de recursos pesados)
5. Informacion de contacto visible

Responde SOLO con una linea en este formato exacto:
NOTA: [F/D/C/B/A] | RAZON: [una frase corta explicando la nota principal]

F = sin sitio web
D = sitio muy malo (desactualizado, no mobile, sin CTA)
C = sitio regular (funciona pero poco profesional)
B = sitio bueno pero mejorable
A = sitio excelente, no contactar
"""


def check_site_exists(url: str) -> bool:
    """Verifica si el sitio web existe y responde."""
    if not url:
        return False
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def audit_with_claude(nombre: str, categoria: str, url: str) -> tuple[str, str]:
    """Llama a Claude para auditar el sitio. Retorna (nota, razon)."""
    prompt = AUDIT_PROMPT.format(url=url, nombre=nombre, categoria=categoria or "negocio local")

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text.strip()

    # Parsear respuesta: "NOTA: D | RAZON: Sitio desactualizado sin mobile"
    nota = "D"
    razon = ""
    if "NOTA:" in response and "|" in response:
        parts = response.split("|")
        nota = parts[0].replace("NOTA:", "").strip()
        razon = parts[1].replace("RAZON:", "").strip() if len(parts) > 1 else ""

    return nota, razon


@app.task(name="workers.auditor.audit_business")
def audit_business(business_id: int):
    """Audita un negocio y encola generacion si la nota es C, D o F."""
    from workers.generator import generate_website

    with get_session() as session:
        b = session.get(Business, business_id)
        if not b:
            return {"error": "Business not found"}

        # Sin sitio web -> nota F directo
        if not b.url_sitio_actual:
            b.nota_auditoria = "F"
            b.notas = "Sin sitio web"
            b.estado = "audited"
            session.commit()
            generate_website.delay(business_id)
            return {"id": business_id, "nota": "F"}

        # Verificar si el sitio existe
        site_exists = check_site_exists(b.url_sitio_actual)
        if not site_exists:
            b.nota_auditoria = "F"
            b.notas = "Sitio no responde"
            b.estado = "audited"
            session.commit()
            generate_website.delay(business_id)
            return {"id": business_id, "nota": "F"}

        # Auditar con Claude
        nota, razon = audit_with_claude(b.nombre, b.categoria, b.url_sitio_actual)
        b.nota_auditoria = nota
        b.notas = razon
        b.estado = "audited"
        session.commit()

        # Solo contactar si nota es C, D o F
        if nota in ("C", "D", "F"):
            generate_website.delay(business_id)
            return {"id": business_id, "nota": nota, "accion": "generando sitio"}
        else:
            b.estado = "skipped"
            session.commit()
            return {"id": business_id, "nota": nota, "accion": "skipped"}
