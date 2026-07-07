# Automation Lab

Monorepo de laboratorio para investigación de herramientas de automatización y testing.

## Tecnologías Elegidas
- **Backend:** Python 3.12, FastAPI, Uvicorn
- **Frontend React:** React 18, Vite, TypeScript
- **Frontend Angular:** Angular 17/18, TypeScript
- **Frontend Vue:** Vue 3, Vite, TypeScript
- **Infraestructura:** Docker & Docker Compose

## Estructura del Proyecto
El proyecto está dividido en microservicios gestionados a través de Docker Compose:
- `/backend` (Puerto 8000)
- `/frontend-react` (Puerto 3000)
- `/frontend-angular` (Puerto 4200)
- `/frontend-vue` (Puerto 5173)

## Cómo ejecutar todo el entorno
Para levantar todos los servicios al mismo tiempo, ejecuta en la raíz del proyecto:
```bash
docker compose up --build