import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Business
from workers.scraper import save_businesses
from contextlib import contextmanager


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    engine.dispose()


def test_save_businesses_creates_records(db_session):
    businesses = [
        {"nombre": "Plomeria Juan", "ciudad": "MdP", "telefono": "223000",
         "url_sitio_actual": "", "categoria": "Plomero", "rating": "4.5"},
    ]

    @contextmanager
    def mock_session():
        yield db_session

    with patch("workers.scraper.get_session", mock_session):
        ids = save_businesses(businesses)

    assert len(ids) == 1
    b = db_session.query(Business).first()
    assert b.nombre == "Plomeria Juan"
    assert b.estado == "scraped"


def test_save_businesses_no_duplicates(db_session):
    businesses = [
        {"nombre": "Plomeria Juan", "ciudad": "MdP", "telefono": "223000",
         "url_sitio_actual": "", "categoria": "Plomero", "rating": ""},
    ]

    @contextmanager
    def mock_session():
        yield db_session

    with patch("workers.scraper.get_session", mock_session):
        ids1 = save_businesses(businesses)
        ids2 = save_businesses(businesses)

    assert len(ids1) == 1
    assert len(ids2) == 0
