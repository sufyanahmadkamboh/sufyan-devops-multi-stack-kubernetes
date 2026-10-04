# Report job: plain JavaScript on Node.js. It runs once and exits (Kubernetes: a Job / CronJob).
FROM node:24.21-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY src ./src

ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION \
    NODE_ENV=production

USER node
CMD ["node", "src/worker.js"]
