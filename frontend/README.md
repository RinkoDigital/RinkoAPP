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

## App nativo (iOS/Android) com Capacitor

`android/` e `ios/` já existem no repo (gerados com `npx cap add`) e são
versionados de propósito — carregam customização nativa de verdade (ver
"Share Sheet" abaixo), não só boilerplate. Depois de mudar o front-end:

```bash
npm run build
npx cap sync
npx cap open ios       # precisa de Xcode (macOS) — não existe neste ambiente
npx cap open android   # precisa de Android Studio / Android SDK — idem
```

A partir daí é build nativo normal, incluindo assinatura e publicação nas
lojas — nada disso foi rodado aqui (sem Xcode/Android SDK no sandbox).

## Share Sheet — receber evidência direto de outros apps

Em vez do motorista reabrir a Rinko e navegar um seletor de arquivo toda
vez, dá pra compartilhar um print (da UniUni, GOFO, da galeria de fotos)
direto pra Rinko pelo Share Sheet do sistema, igual compartilhar pra
WhatsApp. Cai na tela `/share`, que deixa escolher a work session aberta e
o tipo de evidência, e sobe pelo mesmo endpoint de sempre
(`POST /sessions/{id}/evidence`).

- **Android**: pronto — `android/app/src/main/AndroidManifest.xml` já tem
  os `intent-filter` de `ACTION_SEND`, e o plugin nativo
  (`ShareTargetPlugin.java`) já está registrado em `MainActivity.java`.
  Compila direto no Android Studio, sem passo manual.
- **iOS**: o código Swift está pronto
  (`ios/ShareExtension/ShareViewController.swift`,
  `ios/App/App/ShareTargetPlugin.swift`), mas criar a Share Extension e o
  App Group são passos que só existem dentro do Xcode (target novo,
  capability, provisioning — amarrados à sua conta de desenvolvedor Apple).
  Passo a passo em `ios/SHARE_EXTENSION_SETUP.md`.

Isso continua **não sendo** integração com a API da UniUni/GOFO — não
existe parceria pra isso. É só tirar um passo manual de re-upload; a
Rinko continua sendo alimentada pelo que o motorista já tem na tela.

## O que falta pra "pronto"

- Rodar o build nativo de verdade (iOS e Android) numa máquina com
  Xcode/Android Studio — inclui terminar a configuração da Share
  Extension no iOS (`ios/SHARE_EXTENSION_SETUP.md`)
- Ícone/splash screen do app nativo
- Push notifications (se fizer sentido pro produto)
- Testes automatizados de UI (hoje só foi validado manualmente e via
  smoke test com Playwright)
- Deploy do build web em algum lugar público (Vercel, Netlify, etc.) —
  hoje só roda local
