FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE {{PORT}}

ENV NODE_ENV=production
ENV PORT={{PORT}}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:{{PORT}}/health || exit 1

CMD {{START_COMMAND}}
