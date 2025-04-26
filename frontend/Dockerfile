FROM node:20-alpine AS build
WORKDIR /src
COPY frontend ./
RUN if [ -f package.json ]; then npm ci && npm run build; fi

FROM nginx:alpine
COPY --from=build /src/dist /usr/share/nginx/html
