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

### Generación de Plantillas Visuales (`templates/`)

Para ejecutar los tests basados en **Percepción Visual (`opencv` y `opencv_full`)**, primero se debe correr el recolector automatizado de plantillas (`utils/harvest_templates.py`) con los contenedores de `automation-lab` levantados. Este script navega automáticamente por los 3 frontends (`react`, `angular`, `svelte`) y genera las capturas 1:1 en `automation-playwright/templates/` (directorio ignorado en Git):

```bash
cd automation-playwright
python utils/harvest_templates.py --env all
```

---

## Ejecución de Tests

Todos los comandos se ejecutan desde `automation-playwright/` con el venv activo.

```bash
# Un entorno específico
pytest --env=react
pytest --env=angular
pytest --env=svelte

# Flujos E2E comparativos 1:1 (Full GetBy vs Full Vision)
pytest tests/test_full_getby_flow.py --env=react -v
pytest tests/test_full_vision_flow.py --env=react -v

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
│   ├── base_page.py     # BasePage: navigate(), get_title(), helpers visuales y get_by
│   ├── login_page.py    # LoginPage: fill_credentials(), submit(), is_redirected_to_home()
│   ├── home_page.py     # HomePage: is_loaded(), go_to_products()
│   ├── products_page.py # ProductsPage: get_product_cards(), add_to_cart(), auditorías E2E
│   └── cart_page.py     # CartPage: get_items(), remove_item(), auditorías E2E de carrito
├── tests/
│   ├── test_login.py            # Login exitoso, credenciales inválidas, guard de redirección
│   ├── test_products.py         # Flujo add-to-cart con estrategias base, getby y opencv
│   ├── test_full_getby_flow.py  # Flujo E2E completo de 5 etapas con selectores semánticos (getby_full)
│   ├── test_full_vision_flow.py # Flujo E2E completo de 5 etapas con visión artificial (opencv_full)
│   └── test_cart.py             # Item en carrito, quitar item, vaciar carrito
└── utils/
    ├── harvest_templates.py     # Generador automatizado de plantillas UI 1:1 en templates/<env>/
    ├── openvisor_helper.py      # Cliente de vision-service y renderizado de auditoría visual
    ├── telemetry.py             # Recolector de métricas por paso y por test en JSONL
    └── selectors.py             # Mapas de locators por frontend, indexados por nombre de env
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

- El proyecto genera reportes JUnit XML (`reports/report.xml`) enriquecidos con propiedades y adjuntos visuales (`junit-attachments`) y telemetría estructurada en JSONL (`step_metrics.jsonl` y `test_summary.jsonl`).
- Las capturas de pantalla de fallos y las escenas anotadas con *Bounding Boxes* de los flujos visuales (`opencv` y `opencv_full`) se guardan en `reports/<strategy>/<env>/vision_audit/` y `reports/screenshots/`.

---

## Limitaciones Conocidas

- **React add-to-cart** dispara `alert()` — se maneja con `page.once("dialog", ...)` en `ProductsPage.add_to_cart()`.
- **Angular add-to-cart** usa un `div[role=button]` en lugar de `<button>` — sin `data-testid`; el selector apunta a `.catalog-card .add`.
- **Svelte** no tiene atributos `data-testid` — los selectores se basan en HTML semántico y clases CSS.
- **Svelte clear cart** no existe en la UI — `test_clear_cart` se auto-omite con `--env=svelte`.

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
