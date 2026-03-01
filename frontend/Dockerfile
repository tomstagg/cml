FROM node:20-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json ./
RUN npm install --frozen-lockfile 2>/dev/null || npm install

FROM base AS runner
COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 3000
ENV NODE_ENV=development
CMD ["npm", "run", "dev"]
