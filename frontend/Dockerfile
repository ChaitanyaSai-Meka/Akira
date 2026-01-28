FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_BACKEND_URL
ARG VITE_BACKEND_PORT
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_BACKEND_PORT=$VITE_BACKEND_PORT

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
