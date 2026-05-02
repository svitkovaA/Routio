FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_BASE_URL=/routio
ENV VITE_BASE_URL=/routio
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html/routio
COPY nginx.conf /etc/nginx/conf.d/default.conf
