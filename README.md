# Trabajo Final — QA Automation & Computer Vision

**Estrategias de mantenimiento de localizadores en pruebas automatizadas de software utilizando herramientas basadas en visión computacional e inteligencia artificial.**

---

## Estructura del Proyecto

El repositorio se divide en dos módulos principales:

| Módulo | Descripción | Documentación |
| :--- | :--- | :--- |
| **[`automation-lab/`](automation-lab/)** | Entorno de pruebas contenerizado (Backend FastAPI, Frontends en React, Angular y Svelte, y microservicio **`vision-service`** con OpenCV + OCR). | [Ver README](automation-lab/README.md) |
| **[`automation-playwright/`](automation-playwright/)** | Framework de automatización E2E con Playwright y Pytest para evaluar estrategias de localización tradicional vs. percepción visual. | [Ver README](automation-playwright/README.md) |

---

## Inicio Rápido 📋🔧

### 1. Levantar el entorno (`automation-lab`)
```bash
cd automation-lab
docker compose up -d --build --wait
```

### 2. Configurar el entorno virtual de pruebas (Raíz)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Conectar el agente local de Jenkins (`pw-agent`) y ejecutar pipelines CI/CD
Con el contenedor `jenkins` corriendo en `http://localhost:8088` (`admin` / `admin123`), levantar en una terminal PowerShell el agente local de Windows para habilitar la ejecución de los jobs (`harvest-templates`, `run-e2e-tests`, `historical-dashboard`) sobre el `.venv` local y soportar modo `--headed`:
```powershell
.\automation-lab\jenkins\start-local-agent.ps1
```

---

## Flujo de Trabajo 📦

1. Crear rama de funcionalidad (`feature/*` o `fix/*`).
2. Implementar cambios atómicos y ejecutar la suite de pruebas correspondiente.
3. Abrir Pull Request hacia la rama principal.

---

## Wiki 📖

Puedes encontrar más información sobre el proyecto en la [Wiki del repositorio](https://github.com/MatiasBertone21/Trabajo-Final/wiki).

## Autor ✒️

* **Matías Bertone**

## Licencia 📄

Este proyecto se distribuye bajo la licencia **Apache License 2.0** — consulta el archivo [LICENSE](LICENSE) para más detalles.
