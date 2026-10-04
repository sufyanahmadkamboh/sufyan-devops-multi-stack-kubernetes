# syntax=docker/dockerfile:1
# Stage 1: build. Node.js and all build tools exist only here; the result is a folder of static files (dist/).
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
ARG APP_VERSION=1.0.0
# the URL path the app is served under; "/" unless it runs behind a path prefix such as /shop/
ARG BASE_PATH=/
ENV APP_VERSION=${APP_VERSION}
RUN npm run build -- --base=${BASE_PATH}

# Stage 2: serve. Only nginx and the built files: no Node.js, no node_modules, no source code.
FROM nginxinc/nginx-unprivileged:1.30.5-alpine
ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION} \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1 \
    APP_ENV=production \
    ADMIN_URL="" \
    NODE_API_URL=http://node-api:3000 \
    JAVA_API_URL=http://java-api:8080 \
    PYTHON_API_URL=http://python-api:8000 \
    GO_STATUS_URL=http://go-status:8080
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chmod=755 nginx/40-config-js.sh /docker-entrypoint.d/
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
# the base image already runs as the unprivileged user "nginx" (uid 101)
