import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Business, Campaign


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def test_create_campaign(db):
    c = Campaign(nombre="Test", ciudad="Mar del Plata", rubros='["plomero"]')
    db.add(c)
    db.commit()
    assert c.id is not None


def test_create_business(db):
    b = Business(nombre="Plomeria Test", ciudad="Mar del Plata", estado="scraped")
    db.add(b)
    db.commit()
    assert b.id is not None
    assert b.estado == "scraped"


def test_business_default_estado(db):
    b = Business(nombre="Test SRL")
    db.add(b)
    db.commit()
    assert b.estado == "scraped"
