# Front de Vue servido con Nginx. Nginx también reenvía /api al back, en el mismo dominio.
#   podman build -t reto1-front front/
#   podman run -e BACK_URL=http://back:8000 -p 8080:80 reto1-front

FROM docker.io/library/node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
# true solo para una demo sin back; en staging y producción va en false.
ARG VITE_API_MOCK=false
ENV VITE_API_MOCK=$VITE_API_MOCK
RUN npm run build

FROM docker.io/library/nginx:1.28-alpine
# La imagen de Nginx sustituye ${BACK_URL} al iniciar el contenedor.
ENV BACK_URL=http://back:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
