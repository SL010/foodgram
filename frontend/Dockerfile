# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
# RUN npm install react@16.14.0 react-dom@16.14.0
RUN npm install --legacy-peer-deps
# RUN npm install --force
COPY . ./
RUN npm run build
CMD cp -r build result_build
