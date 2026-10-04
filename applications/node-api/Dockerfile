# Node.js users API. No build step: install production dependencies, copy the code, run as a non-root user.
FROM node:24.21-alpine

WORKDIR /app

# dependencies first: this layer is cached until package.json / package-lock.json change
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY src ./src

ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION \
    NODE_ENV=production \
    PORT=3000

USER node
EXPOSE 3000
CMD ["node", "src/server.js"]
