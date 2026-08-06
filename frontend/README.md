# Rinko — Frontend

React + Vite + TypeScript app that talks to the Rinko API. It's the same
app in two shapes: a responsive web app today, and — via
[Capacitor](https://capacitorjs.com/) — an installable iOS/Android app
once you build it on a machine with Xcode/Android Studio (this
environment has neither, so native builds weren't produced here).

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

## Build web

```bash
npm run build
```

## Virando app nativo (iOS/Android) com Capacitor

O projeto já tem o Capacitor instalado e configurado
(`capacitor.config.ts`, `appId: com.rinkodigital.app`). Falta rodar,
numa máquina com as ferramentas nativas instaladas:

```bash
npm run build
npx cap add ios       # precisa de Xcode (macOS)
npx cap add android    # precisa de Android Studio / Android SDK
npx cap sync
npx cap open ios       # ou: npx cap open android
```

A partir daí é build nativo normal (Xcode/Android Studio), incluindo
assinatura e publicação nas lojas — nada disso está automatizado aqui.

## O que falta pra "pronto"

- Ícone/splash screen do app nativo
- Push notifications (se fizer sentido pro produto)
- Testes automatizados de UI (hoje só foi validado manualmente e via
  smoke test com Playwright)
- Deploy do build web em algum lugar público (Vercel, Netlify, etc.) —
  hoje só roda local
