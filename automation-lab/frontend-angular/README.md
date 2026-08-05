# FrontendAngular


Run the Angular frontend with Docker (recommended)

This project now builds a production artifact and serves it via `nginx` inside the container.

From the repo root (`automation-lab`) you can bring up the backend and all frontends with Docker Compose:

```bash
docker compose up --build -d
```

If you only want the Angular frontend and the backend:

```bash
docker compose up --build -d backend angular
```

Notes:
- The Angular container now serves the static app via `nginx` on container port `80`, mapped to host port `4200` by default.
- The container reads the API base URL from the runtime environment variable `VITE_API_BASE_URL` and writes it to a small `env-config.js` file at container startup. The app reads `window.__API_BASE__` at runtime.
- Default value inside the compose file is `http://backend:8000` so the Angular UI talks to the backend service on the Docker network.

If you prefer to run a development build with live reload, use the old workflow locally:

```bash
cd frontend-angular
npm install
npm start
```



## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
