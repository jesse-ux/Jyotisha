FROM node:22-alpine

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/next.config.ts frontend/postcss.config.mjs frontend/tsconfig.json ./

ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
COPY SKILL.md /app/SKILL.md
COPY assets /app/assets
COPY references /app/references
COPY scripts /app/scripts
COPY skills /app/skills

RUN npm run build && npm prune --omit=dev

ENV NODE_ENV=production
CMD ["sh", "-c", "exec npm start -- --hostname 0.0.0.0 --port \"${PORT:-3000}\""]
