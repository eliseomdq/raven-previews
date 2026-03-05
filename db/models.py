from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)
    rubros = Column(String)  # JSON string list
    cantidad_diaria = Column(Integer, default=50)
    activa = Column(Boolean, default=True)
    creada_en = Column(DateTime, default=datetime.utcnow)


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    campana_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Datos scrapeados
    nombre = Column(String, nullable=False)
    categoria = Column(String)
    ciudad = Column(String)
    telefono = Column(String)
    email = Column(String)
    whatsapp = Column(String)
    url_sitio_actual = Column(String)
    rating = Column(String)
    direccion = Column(String)

    # Auditoria
    nota_auditoria = Column(String)  # F, D, C, B, A
    screenshot_actual = Column(String)  # path local

    # Preview generado
    html_generado = Column(Text)
    url_preview = Column(String)

    # Pipeline state
    estado = Column(String, default="scraped")
    # Estados: scraped, audited, skipped, generated, deployed,
    #          outreach_email, outreach_whatsapp, follow_up,
    #          responded, converted, lost

    # Outreach tracking
    email_enviado = Column(Boolean, default=False)
    whatsapp_enviado = Column(Boolean, default=False)
    respondio = Column(Boolean, default=False)
    convertido = Column(Boolean, default=False)

    fecha_scraping = Column(DateTime, default=datetime.utcnow)
    fecha_ultimo_contacto = Column(DateTime)
    notas = Column(Text)
