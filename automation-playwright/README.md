# automation-playwright

Baseline A — Suite de automatización UI construida con **Python 3.12 + Playwright (sync) + Pytest**.  
Apunta a los tres frontends locales (React, Angular, Svelte) del proyecto e-commerce Automation Lab.

---

## Stack

| Herramienta | Versión | Rol |
|---|---|---|
| Python | 3.12 | Runtime |
| Playwright | 1.62 | Automatización de browser (API síncrona) |
| pytest | 9.1 | Test runner |
| pytest-playwright | 0.8 | Integración de fixtures con Playwright |

---

## Prerrequisitos

- Docker corriendo con los servicios de `automation-lab` levantados (`docker compose up -d`)
- Entorno virtual creado en la raíz del repo con las dependencias instaladas

```bash
# Desde la raíz del repo
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
```

---

## Ejecución de Tests

Todos los comandos se ejecutan desde `automation-playwright/` con el venv activo.

```bash
# Un entorno específico
pytest --env=react
pytest --env=angular
pytest --env=svelte

# Solo smoke tests
pytest --env=react -m smoke

# Solo regression
pytest --env=react -m regression

# Matriz completa (los tres frontends)
pytest --env=react ; pytest --env=angular ; pytest --env=svelte
```

### Mapeo de entorno → puerto

| `--env` | URL |
|---|---|
| `react` | http://localhost:3000 |
| `angular` | http://localhost:4200 |
| `svelte` | http://localhost:5173 |

### Usuarios de prueba

| Email | Contraseña | Rol |
|---|---|---|
| admin@test.com | 123456 | Admin |
| user@test.com | 123456 | Usuario estándar |

---

## Estructura del Proyecto

```
automation-playwright/
├── conftest.py          # Fixtures de sesión: browser, page, base_url, selectors, auth_page
├── pytest.ini           # testpaths, definición de markers, addopts por defecto
├── pages/
│   ├── base_page.py     # BasePage: navigate(), get_title(), timeout compartido
│   ├── login_page.py    # LoginPage: fill_credentials(), submit(), is_redirected_to_home()
│   ├── home_page.py     # HomePage: is_loaded(), go_to_products()
│   ├── products_page.py # ProductsPage: get_product_cards(), add_to_cart()
│   └── cart_page.py     # CartPage: get_items(), remove_item(), clear_cart(), is_empty()
├── tests/
│   ├── test_login.py    # Login exitoso, credenciales inválidas, guard de redirección
│   ├── test_products.py # Lista de productos, navegación desde home, flujo add-to-cart
│   └── test_cart.py     # Item en carrito, quitar item, vaciar carrito
└── utils/
    └── selectors.py     # Mapas de locators por frontend, indexados por nombre de env
```

---

## Arquitectura

### Page Object Model (POM)

Todos los page objects heredan de `BasePage` y reciben `(page, base_url, selectors)` en su construcción.  
Ningún page object hardcodea un locator — todos los selectores se resuelven en runtime desde `utils/selectors.py`.

```
BasePage
  ├── LoginPage
  ├── HomePage
  ├── ProductsPage
  └── CartPage
```

### Estrategia de selectores

Cada frontend tiene su propio mapa de locators en `utils/selectors.py`.  
Las claves son nombres lógicos (ej. `login_submit`, `cart_item`); los valores son selectores CSS apropiados para ese frontend.

| Clave | React | Angular | Svelte |
|---|---|---|---|
| `login_submit` | `[data-testid=login-button-visible]` | `[data-testid=login-submit]` | `button[type=submit]` |
| `add_to_cart` | `.product-card button.button-primary` | `.catalog-card .add` | `.product-card button` |
| `clear_cart` | `[data-testid=clear-cart-button]` | `[data-testid=cart-clear]` | `None` *(skip)* |

Cuando un selector es `None`, el test correspondiente ejecuta `pytest.skip()` en runtime.

Nota sobre la estrategia `get_by`:
- `BasePage._get_locator_by` soporta dos formatos en `utils/selectors_get_by.py`:
  - un `dict` con `{"role": "...", "name": "..."}` → usa `page.get_by_role(...)` (con opción de `child` para locators hijos).
  - un `string` → intenta `page.get_by_test_id(...)` y hace fallback a `page.locator(...)` (CSS). También hay un fallback adicional que busca `data-testid^="..."` cuando es necesario.

Para ejecutar los tests que usan la estrategia `get_by` (marcados `getby`):

```bash
pytest --env=angular -m getby
```

### Jerarquía de fixtures

```
session scope
  browser  →  base_url  →  selectors
               ↑
              env  ←  opción CLI --env

function scope
  page          ← Page nueva por test (aislamiento total)
  auth_page     ← page con login completado (fixture compuesto)
  base_selectors ← mapa de selectores (estrategia base, strings/CSS)
  getby_selectors ← mapa de selectores para `get_by_*` (dict con role/name o test id)
```

## Reports

- El proyecto genera reportes HTML y JUnit XML automáticamente usando `pytest-html` y la opción `--html`/`--self-contained-html` (configurada en `pytest.ini`).
- Las capturas de pantalla de fallos se adjuntan al reporte HTML mediante el hook `pytest_runtest_makereport` (ver `conftest.py`). Cuando una prueba falla, se toma `page.screenshot(full_page=True)` y se incrusta en el HTML.
- Comandos útiles:

```bash
# Ejecuta la suite y genera un reporte HTML autocontenido y JUnit XML
pytest --env=react

# Forzar ruta de salida del reporte (sobrescribe la opción de pytest.ini)
pytest --env=react --html=reports/report.html --self-contained-html
```

- Archivos generados (por defecto, según `pytest.ini`):
  - `reports/report.html` — reporte HTML con capturas embebidas.
  - `reports/report.xml` — JUnit XML para integraciones CI.

- Nota: `pytest-html` ya está listado en `requirements.txt`. Asegúrate de crear la carpeta `reports/` si tu entorno CI no la crea automáticamente.

---

## Limitaciones Conocidas

- **React add-to-cart** dispara `alert()` — se maneja con `page.once("dialog", ...)` en `ProductsPage.add_to_cart()`.
- **Angular add-to-cart** usa un `div[role=button]` en lugar de `<button>` — sin `data-testid`; el selector apunta a `.catalog-card .add`.
- **Svelte** no tiene atributos `data-testid` — los selectores se basan en HTML semántico y clases CSS.
- **Svelte clear cart** no existe en la UI — `test_clear_cart` se auto-omite con `--env=svelte`.
- El estado del carrito **no se resetea entre tests**. Para aislamiento total, agregar un fixture de teardown que llame a `DELETE /api/cart` en el backend.

---

## Cómo Extender el Framework

### Agregar un nuevo Page Object

1. Crear `pages/new_page.py` heredando de `BasePage`.
2. Agregar las claves de locators necesarias en los tres mapas de `utils/selectors.py`.
3. Importar e instanciar en el test correspondiente — no se requieren cambios en `conftest.py`.

### Agregar un nuevo test

```python
# tests/test_example.py
import pytest
from pages.products_page import ProductsPage

@pytest.mark.smoke
def test_example(page, base_url, selectors):
    products = ProductsPage(page, base_url, selectors)
    products.goto()
    assert products.get_product_cards().count() > 0
```

### Agregar un nuevo entorno

1. Agregar la entrada en `ENV_URLS` dentro de `conftest.py`.
2. Agregar el mapa de selectores en `utils/selectors.py`.
3. Actualizar las `choices` de `--env` en `pytest_addoption`.
