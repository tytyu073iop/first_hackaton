# Stage 1: builder
FROM node:20-alpine as builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/vite.config.js ./
COPY frontend/index.html ./
COPY frontend/src ./src

RUN npm run build


# Stage 2: runtime
FROM node:20-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]