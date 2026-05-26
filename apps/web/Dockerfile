FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json /app/
COPY apps/web/package.json /app/apps/web/package.json
COPY packages/contracts/package.json /app/packages/contracts/package.json
COPY packages/contracts/src /app/packages/contracts/src
COPY apps/web /app/apps/web

RUN npm ci
RUN npm run build --workspace apps/web

EXPOSE 3000
CMD ["npm", "run", "start", "--workspace", "apps/web"]
