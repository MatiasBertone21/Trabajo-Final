### Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# build production artifact
RUN npx ng build --configuration production

### Production stage served by nginx
FROM nginx:alpine
# Copy built files directly into nginx html root.
# Angular CLI outputs to dist/frontend-angular/browser for this project.
COPY --from=builder /app/dist/frontend-angular/browser/. /usr/share/nginx/html/

# Copy custom nginx config to enable SPA fallback (rewrite unknown routes to index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]