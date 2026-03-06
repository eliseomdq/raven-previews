import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
import requests
from workers.celery_app import app
from db.database import get_session
from db.models import Business
from config import GMAIL_USER, GMAIL_APP_PASSWORD, EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE
import logging

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #1a1a2e;">Hola, {nombre}</h2>
  <p>Somos <strong>RAVEN</strong>, una agencia de automatizacion digital de Argentina.</p>
  <p>Notamos que {problema}, por eso preparamos una <strong>muestra gratuita</strong> de como podria verse tu sitio web:</p>
  <p style="text-align: center; margin: 30px 0;">
    <a href="{url_preview}"
       style="background: #00d4ff; color: #000; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
      Ver mi sitio web gratis
    </a>
  </p>
  <p>Si te interesa, respondenos este mail o escribinos al WhatsApp.</p>
  <p>Saludos,<br><strong>Equipo RAVEN</strong><br>
  <a href="https://raven.com.ar">raven.com.ar</a></p>
</body>
</html>
"""

WA_TEMPLATE = """Hola {nombre}! Soy de RAVEN, agencia de automatizacion digital.

Preparamos una muestra gratuita de tu nuevo sitio web:
{url_preview}

Entras y lo ves, sin compromiso. Si te copa, coordinamos.

Saludos!"""


def get_problema(nota: str) -> str:
    mapping = {
        "F": "tu negocio no tiene sitio web todavia",
        "D": "tu sitio web actual esta bastante desactualizado",
        "C": "tu sitio web puede mejorar bastante para atraer mas clientes",
    }
    return mapping.get(nota, "tu sitio web puede mejorar")


def send_email(to: str, nombre: str, url_preview: str, nota: str) -> bool:
    """Envia email via Gmail SMTP. Retorna True si exitoso."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Hola {nombre} — preparamos algo para vos"
        msg["From"] = GMAIL_USER
        msg["To"] = to

        html_body = EMAIL_TEMPLATE.format(
            nombre=nombre,
            problema=get_problema(nota),
            url_preview=url_preview,
        )
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to, msg.as_string())

        return True
    except Exception as e:
        logger.error(f"Error enviando email a {to}: {e}")
        return False


def send_whatsapp(phone: str, nombre: str, url_preview: str) -> bool:
    """Envia WhatsApp via Evolution API. Retorna True si exitoso."""
    try:
        phone_clean = "".join(filter(str.isdigit, phone))
        if not phone_clean.startswith("54"):
            phone_clean = "54" + phone_clean

        message = WA_TEMPLATE.format(nombre=nombre, url_preview=url_preview)

        r = requests.post(
            f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}",
            headers={"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"},
            json={"number": phone_clean, "text": message},
            timeout=15,
        )
        return r.status_code == 201
    except Exception as e:
        logger.error(f"Error enviando WhatsApp a {phone}: {e}")
        return False


@app.task(name="workers.outreach.send_outreach")
def send_outreach(business_id: int):
    """Envia email si hay email, WhatsApp si hay telefono."""
    with get_session() as session:
        b = session.get(Business, business_id)
        if not b or not b.url_preview:
            return {"error": "Business or preview not found"}

        enviado = False

        if b.email:
            ok = send_email(b.email, b.nombre, b.url_preview, b.nota_auditoria)
            if ok:
                b.email_enviado = True
                enviado = True

        if b.telefono:
            ok = send_whatsapp(b.telefono, b.nombre, b.url_preview)
            if ok:
                b.whatsapp_enviado = True
                enviado = True

        if b.email_enviado:
            b.estado = "outreach_email"
        elif b.whatsapp_enviado:
            b.estado = "outreach_whatsapp"

        b.fecha_ultimo_contacto = datetime.now(timezone.utc)
        session.commit()

        result = {"id": business_id, "email": b.email_enviado, "whatsapp": b.whatsapp_enviado}
        should_followup = enviado

    if should_followup:
        send_followup.apply_async(args=[business_id], countdown=259200)

    return result


@app.task(name="workers.outreach.send_followup")
def send_followup(business_id: int):
    """Seguimiento si no respondio."""
    with get_session() as session:
        b = session.get(Business, business_id)
        if not b or b.respondio:
            return {"skipped": True}

        if b.telefono and b.url_preview:
            send_whatsapp(b.telefono, b.nombre, b.url_preview)

        b.estado = "follow_up"
        b.fecha_ultimo_contacto = datetime.now(timezone.utc)
        session.commit()
        return {"id": business_id, "followup": True}
