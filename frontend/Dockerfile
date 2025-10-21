FROM docker.1ms.run/node:20-alpine
WORKDIR /usr/src/app
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"] 
