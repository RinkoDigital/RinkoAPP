# Rinko — Frontend

React + Vite + TypeScript web app that talks to the Rinko API. This is
the **web app only** — deployed via `netlify.toml` at the repo root. The
native iOS/Android app lives separately in `../mobile/` (Expo/React
Native), not here — see that project's README for why.

## Rodando localmente

```bash
npm install
cp .env.example .env   # aponte VITE_API_BASE_URL pro backend (padrão: localhost:8000)
npm run dev
```

Precisa da API rodando (`uvicorn app.main:app --reload` na raiz do
repo) — o front-end não guarda nenhum dado sozinho, tudo vem da API.

## Estrutura

- `src/api/` — cliente HTTP (`client.ts`), tipos espelhando os schemas
  do backend (`types.ts`), formatação de dinheiro/data (`format.ts`)
- `src/auth/` — contexto de autenticação (token + driver, persistidos em
  `localStorage`)
- `src/pages/` — uma tela por rota: Auth, Home, Start Session, Session
  Detail (encerrar + evidence + pagamento), Work Report, Ledger, Account
- `src/styles/theme.css` — os tokens de cor/tipografia do tema Rinko
  Digital (mesmo guia usado nos mockups)

## Build

```bash
npm run build
```

## Deploy

Ver `netlify.toml` na raiz do repo e a seção "Deploy" do README principal.

## O que falta pra "pronto"

- Testes automatizados de UI (hoje só foi validado manualmente e via
  smoke test com Playwright)
- Deploy de verdade em produção (Netlify) — hoje só roda local
