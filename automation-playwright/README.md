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
├── ci/                  # Pipelines de Jenkins y generadores de reportes HTML/científicos
│   ├── Jenkinsfile.harvest          # Pipeline Job 1: Cosecha de plantillas UI y galería
│   ├── Jenkinsfile.test             # Pipeline Job 2: Ejecución E2E, JUnit y auditoría visual
│   ├── Jenkinsfile.historical       # Pipeline Job 3: Consolidación histórica y 5 gráficos
│   ├── Jenkinsfile                  # Pipeline monolítico original (benchmark)
│   ├── wait_for_services.py         # Sonda de disponibilidad HTTP (/health) de los 5 servicios
│   ├── build_templates_gallery.py   # Generador de reports/templates_gallery.html
│   ├── build_vision_audit.py        # Generador de reports/vision_audit.html + sync a metrics-history/
│   ├── build_historical_dashboard.py# Generador de reports/historical_dashboard.html (ventana K)
│   ├── build_dashboard.py           # Generador de reports/dashboard.html (corrida única)
│   └── reporting/                   # Paquete compartido (Template Method + gráficos Pillow)
│       ├── base_report.py           # Clase abstracta BaseHTMLReport (CSS común y estructura HTML5)
│       ├── charts.py                # Motor de gráficos científicos en PNG Base64 (Pillow)
│       ├── constants.py             # Rutas, estrategias, frontends, colores y esquemas CSV
│       └── telemetry_io.py          # Estadísticas (mediana, p95, DE), lectura JSONL/CSV y agregación
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

## CI/CD con Jenkins y Reportes (`ci/`)

La suite se integra con el servidor **Jenkins LTS** (`http://localhost:8088`, usuario `admin` / `admin123`) definido en `automation-lab/docker-compose.yml`.

### 1. Conexión obligatoria del Agente Local (`pw-agent`) en Windows
Para que los jobs de Jenkins ejecuten Playwright sobre el entorno `.venv` local de Windows —garantizando el mismo renderizado tipográfico del sistema operativo durante el Template Matching (`TM_CCOEFF_NORMED`) y permitiendo abrir el navegador en pantalla cuando `HEADED=true`—, **se debe dejar corriendo el script del agente local** en una ventana de PowerShell antes de lanzar un build:

```powershell
# Desde la raíz del repositorio
.\automation-lab\jenkins\start-local-agent.ps1
```

### 2. Flujo Modular de 3 Jobs en Jenkins
1. **`harvest-templates` (`ci/Jenkinsfile.harvest`):**
   - Ejecuta `utils/harvest_templates.py` para capturar las plantillas UI 1:1 (`templates/{env}/`) en React, Angular y Svelte, archiva los recortes PNG y publica el catálogo auditable **`Templates Gallery (OpenVisor)`** (`reports/templates_gallery.html`).
2. **`run-e2e-tests` (`ci/Jenkinsfile.test`):**
   - Permite ejecutar cualquier combinación de `STRATEGY` (`base`, `getby`, `opencv`, `getby_full`, `opencv_full`, `ALL`), `FRONTEND` (`react`, `angular`, `svelte`, `ALL`), repeticiones (`REPEAT`), precalentamiento de EasyOCR (`WARMUP`) y modo visual (`HEADED`).
   - Publica resultados JUnit, genera el reporte **`OpenVisor Visual Audit`** (`reports/vision_audit.html`) agrupado por test con capturas anotadas (*Bounding Boxes*, *Center Point* y metadatos de tiempo/confianza por paso) y sincroniza la telemetría de texto en `metrics-history/`.
3. **`historical-dashboard` (`ci/Jenkinsfile.historical`):**
   - Consolida las últimas `K` ejecuciones históricas (`WINDOW_SIZE`, por defecto `5`) desde `metrics-history/` sin abrir el navegador ni duplicar imágenes pesadas.
   - Publica el **`Historical Benchmark Dashboard`** (`reports/historical_dashboard.html`) con la tabla experimental consolidada, el desglose paso a paso (`getby_full` vs `opencv_full`) y **5 gráficos científicos embebidos en Base64 PNG**.

### 3. Arquitectura del Paquete de Reportes (`ci/reporting/`)
Todos los generadores (`build_templates_gallery.py`, `build_vision_audit.py`, `build_historical_dashboard.py` y `build_dashboard.py`) heredan de la clase abstracta **`BaseHTMLReport`** (`ci/reporting/base_report.py`) siguiendo el patrón **Template Method**, reutilizando la hoja de estilos común compatible con Jenkins CSP, el motor de gráficos con Pillow (`ci/reporting/charts.py`) y el agregador estadístico (`ci/reporting/telemetry_io.py`).

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
