# ShiftProof — Frontend

React + Vite + TypeScript web app that talks to the ShiftProof API. This is
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

## Login com Google

A tela de auth (`src/pages/Auth.tsx`) renderiza o botão oficial do Google
(`src/api/googleAuth.ts`, via Google Identity Services) quando
`VITE_GOOGLE_CLIENT_ID` está definido no ambiente — mesmo client "Web
application" usado pelo `EXPO_PUBLIC_GOOGLE_CLIENT_ID` do app mobile (ver
README da raiz pra como configurar). Sem essa variável, o botão some e só
sobra o login por email/senha. O credential (JWT) que o Google devolve vai
direto pro `POST /auth/oauth/google` do backend, que verifica a assinatura
— o front-end nunca guarda nem inspeciona esse token.

Apple **não** tem botão aqui — "Sign in with Apple" na web exige um Services
ID configurado com domínio verificado (diferente do fluxo nativo do app
mobile, que só usa a capability do Apple Developer). Fora de escopo por
enquanto.

Não deu pra testar o clique de ponta a ponta neste ambiente de
desenvolvimento — o sandbox não tem rota de rede pro
`accounts.google.com/gsi/client` a partir do navegador, então o script
nunca carrega e o botão simplesmente não aparece (sem erro, sem crash — é
esperado; numa máquina/deploy normal com internet de verdade ele carrega).

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
