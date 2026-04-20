# Frontend Dockerfile — multi-stage build keeps final image ~25 MB.

# Stage 1: build the React app
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci                      # clean install from lock file (faster, reproducible)
COPY . .
# VITE_API_BASE_URL must be passed as a build arg to point to the backend
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build               # outputs static files to /app/dist

# Stage 2: serve with Nginx (no Node runtime in production image)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
