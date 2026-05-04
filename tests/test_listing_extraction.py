"""
Tests for listing-level extraction (`_extract_property_data`) and spec parsing
(`_extract_all_specs`).

These tests drive the methods with inline HTML fixtures to avoid network and
Selenium dependencies.
"""

from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from scraper_selenium import PortalInmobiliarioSeleniumScraper


LISTING_HTML = """
<li class="ui-search-layout__item" data-id="MLC2345678">
  <div class="poly-component__highlight">OPORTUNIDAD</div>
  <a class="poly-component__title" href="https://www.portalinmobiliario.com/MLC-2345678-depto">
    Lindo depto en Las Condes
  </a>
  <span class="poly-component__headline">Departamento en Venta</span>
  <div class="poly-price__current">
    <span class="andes-money-amount__currency-symbol">UF</span>
    <span class="andes-money-amount__fraction">5.500</span>
  </div>
  <s class="andes-money-amount--previous">
    <span class="andes-money-amount__fraction">6.000</span>
  </s>
  <span class="poly-component__location">Las Condes, Metropolitana</span>
  <ul class="poly-attributes_list">
    <li class="poly-attributes_list__item">80 m² útiles</li>
    <li class="poly-attributes_list__item">3 dormitorios</li>
    <li class="poly-attributes_list__item">2 baños</li>
  </ul>
  <img class="poly-component__picture"
       data-src="https://http2.mlstatic.com/D_NQ_NP_123-MLC.webp"/>
  <span class="ui-search-result__image-counter">12 fotos</span>
</li>
"""


SPECS_HTML = """
<html><body>
  <div class="ui-vpp-striped-specs__table">
    <table><tbody>
      <tr>
        <th class="ui-pdp-specs__table__column-title">Superficie total</th>
        <td class="ui-pdp-specs__table__column-value">120 m²</td>
      </tr>
      <tr>
        <th class="ui-pdp-specs__table__column-title">Dormitorios</th>
        <td class="ui-pdp-specs__table__column-value">3</td>
      </tr>
      <tr>
        <th class="ui-pdp-specs__table__column-title">Año de construcción</th>
        <td class="ui-pdp-specs__table__column-value">2015</td>
      </tr>
      <tr>
        <th class="ui-pdp-specs__table__column-title">Orientación</th>
        <td class="ui-pdp-specs__table__column-value">Norte</td>
      </tr>
      <tr>
        <th class="ui-pdp-specs__table__column-title">Gastos comunes</th>
        <td class="ui-pdp-specs__table__column-value">$ 180.000</td>
      </tr>
    </tbody></table>
  </div>
  <ul class="ui-vpp-amenities__list">
    <li>Piscina</li>
    <li>Gimnasio</li>
    <li>Quincho</li>
  </ul>
</body></html>
"""


@pytest.fixture
def scraper(monkeypatch):
    """Build a scraper instance without initializing Selenium."""
    # Skip __init__ to avoid Selenium/Chrome startup
    scr = PortalInmobiliarioSeleniumScraper.__new__(PortalInmobiliarioSeleniumScraper)
    scr.operacion = 'venta'
    scr.tipo_propiedad = 'departamentos'
    scr.driver = MagicMock()
    return scr


def test_extract_property_data_captures_extended_fields(scraper):
    listing = BeautifulSoup(LISTING_HTML, 'lxml').select_one('li')
    data = scraper._extract_property_data(listing)

    assert data is not None
    assert data['id'] == 'MLC-2345678'
    assert 'Lindo depto' in data['titulo']
    assert data['headline'] == 'Departamento en Venta'
    assert 'UF' in data['precio']
    assert '5.500' in data['precio']
    assert data['precio_anterior'] == 6000
    assert data['ubicacion'] == 'Las Condes, Metropolitana'
    assert 'OPORTUNIDAD' in data['tags']
    assert data['thumbnail_url'] and 'mlstatic' in data['thumbnail_url']
    assert data['num_fotos'] == 12


def test_extract_all_specs_maps_typed_fields_and_keeps_raw(scraper):
    soup = BeautifulSoup(SPECS_HTML, 'lxml')
    raw, typed = scraper._extract_all_specs(soup)

    # Raw features contain all 5 specs
    raw_keys = [f['key'] for f in raw]
    assert 'Superficie total' in raw_keys
    assert 'Año de construcción' in raw_keys
    assert 'Gastos comunes' in raw_keys

    # Typed mapping
    assert typed['superficie_total'] == 120.0
    assert typed['dormitorios'] == 3
    assert typed['ano_construccion'] == 2015
    assert typed['orientacion'] == 'Norte'
    assert typed['gastos_comunes'] == 180000


def test_extract_amenities_from_list(scraper):
    soup = BeautifulSoup(SPECS_HTML, 'lxml')
    raw, _ = scraper._extract_all_specs(soup)
    amenities, servicios = scraper._extract_amenities_services(soup, raw)

    assert 'Piscina' in amenities
    assert 'Gimnasio' in amenities
    assert 'Quincho' in amenities
    assert servicios == []  # none of these are services
