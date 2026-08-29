# Automation Lab

Laboratorio de QA Automation orientado a prácticas reales de testing sobre una arquitectura moderna con API backend y múltiples frontends.

## Objetivo

Este proyecto no busca construir un producto comercial final. Su propósito es proveer un entorno consistente para practicar:

- Automatización de UI
- Testing visual
- Estrategias self-healing
- Docker
- CI/CD
- Playwright
- Inteligencia artificial aplicada al testing

## Arquitectura

Automation Lab está compuesto por:

- Un backend en FastAPI que expone la API y recursos estáticos.
- Tres implementaciones frontend (React, Angular y Svelte) que consumen la misma API.
- Orquestación completa con Docker Compose para facilitar ejecución y pruebas reproducibles.

## Desafío de Investigación

El flujo de productos incluye una variación intencional en el botón Add to bag para evaluar automatización sin apoyarse en un locator dedicado.

- React utiliza un botón semántico con `onClick`.
- Angular utiliza una implementación distinta con un elemento interactivo no semántico.
- Svelte mantiene el botón semántico con su evento correspondiente.

La funcionalidad es la misma en los tres frontends: al hacer click, se agrega el producto correcto al carrito.

## Stack Tecnológico

- Backend: Python 3.12, FastAPI, Uvicorn
- Frontend React: React 19, Vite, TypeScript
- Frontend Angular: Angular 21, TypeScript
- Frontend Svelte: Svelte 5, Vite
- Infraestructura: Docker, Docker Compose

## Servicios y Puertos

| Servicio | Puerto en host | Descripción |
|---|---:|---|
| backend | 8000 | API principal, health check y assets |
| react | 3000 | Frontend React |
| angular | 4200 | Frontend Angular (Nginx en contenedor) |
| svelte | 5173 | Frontend Svelte |

## Requisitos Previos

- Docker Desktop con Docker Compose v2
- Opcional: Node.js 20 o superior para ejecutar frontends fuera de Docker
- Opcional: Python 3.12 para ejecutar backend fuera de Docker

## Puesta en Marcha

Desde la carpeta `automation-lab`:

1. Levantar todos los servicios:

```bash
docker compose up -d --build
```

2. Verificar estado de contenedores:

```bash
docker compose ps
```

Accesos principales:

- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Frontend React: http://localhost:3000
- Frontend Angular: http://localhost:4200
- Frontend Svelte: http://localhost:5173

## Aislamiento de Carrito Por Frontend

Para evitar que distintos frontends compartan el mismo carrito, la API ahora segmenta el carrito por scope usando el header `X-Cart-Scope`.

- React envía `X-Cart-Scope: react`
- Angular envía `X-Cart-Scope: angular`
- Svelte mantiene carrito local en su store y no usa los endpoints de carrito del backend en el flujo actual

Notas de compatibilidad:

- Si `app/data/cart.json` está en formato legacy (lista única), el backend lo interpreta como scope `default`.
- Los nuevos cambios persisten el carrito en formato por scope (objeto con una lista por entorno).

## Estructura del Proyecto

- `backend`: API FastAPI, lógica de dominio, repositorios JSON y servicios.
- `frontend-react`: implementación UI en React + TypeScript.
- `frontend-angular`: implementación UI en Angular.
- `frontend-svelte`: implementación UI en Svelte.
- `assets`: recursos compartidos usados por backend y frontends.

