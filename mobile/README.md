# Rinko — Mobile (Expo / React Native)

The native app: same backend, same screens as `frontend/` (the web app),
rebuilt with Expo + React Native + Expo Router instead of Vite + Capacitor.
Chosen over Capacitor specifically because [EAS Build](https://docs.expo.dev/build/introduction/)
compiles the iOS binary in Expo's cloud — no Mac/Xcode required locally,
which the Capacitor path couldn't avoid.

## Rodando localmente

```bash
npm install
npm run web     # navegador, via react-native-web
npm run ios     # precisa de simulador iOS (macOS) ou Expo Go num device
npm run android # precisa de emulador Android ou Expo Go num device
```

Aponta pra API local por padrão (`http://localhost:8000`). Pra apontar pra
outro lugar, defina `EXPO_PUBLIC_API_BASE_URL` no ambiente antes de rodar.

**Nota sobre este sandbox especificamente**: `api.expo.dev` está bloqueado
pelo proxy de rede daqui, então `expo start` precisa da flag `--offline`
pra não travar tentando validar telemetria/manifesto:

```bash
EXPO_OFFLINE=1 npx expo start --web
```

Isso não deve ser necessário na sua máquina/CI normal, só neste ambiente
de desenvolvimento restrito.

## Estrutura

- `app/` — rotas via [Expo Router](https://docs.expo.dev/router/introduction/)
  (baseado em arquivos, como o Next.js): `auth.tsx`, `(tabs)/` (Home,
  Ledger, Account), `sessions/new.tsx`, `sessions/[sessionId]/index.tsx`
  (fechar sessão + evidence), `sessions/[sessionId]/report.tsx` (Work
  Report)
- `src/api/` — mesmo cliente HTTP/tipos do `frontend/`, adaptado pra
  `AsyncStorage` em vez de `localStorage`
- `src/auth/` — contexto de autenticação (mesma lógica, storage assíncrono)
- `src/components/ui.tsx` — kit de componentes (Card, Button, Field,
  Screen...) — RN não tem classes CSS globais, então isso substitui o
  `theme.css` do app web
- `src/theme.ts` — os mesmos tokens de cor do tema Rinko Digital, como
  objeto JS (RN não lê CSS custom properties)

## O que foi testado aqui

- `npx tsc --noEmit` limpo
- `expo start --web` rodando de verdade contra o backend real: cadastro,
  login, criar carrier, iniciar/encerrar work session, ver Work Report com
  números calculados — tudo verificado com Playwright, sem erros de
  console
- **Não testado**: build nativo de verdade (iOS/Android). Esse ambiente
  não tem simulador nem dispositivo, e `api.expo.dev` (usado pelo EAS)
  está bloqueado pela política de rede daqui — só dá pra validar via
  `--web`, que usa react-native-web e não passa pelo runtime nativo real.

## Share Sheet (evidence direto de outros apps)

**Ainda não implementado neste app** (o app web/Capacitor em `frontend/`
tem essa feature — ver `frontend/ios/SHARE_EXTENSION_SETUP.md` e o plugin
Android lá). Pro Expo, o caminho seria uma lib de share-intent (ex.:
`expo-share-intent`) — isso exige um dev client customizado (não funciona
no Expo Go puro) e não foi validado aqui por falta de acesso a
simulador/EAS. Fica como próximo passo.

## Build nativo (EAS)

`eas.json` já está configurado com os perfis `development`/`preview`/`production`.
Pra buildar de verdade, você precisa de uma conta Expo (grátis pra
começar):

```bash
npm install -g eas-cli
eas login
eas build --platform ios --profile preview      # builda na nuvem, sem precisar de Mac
eas build --platform android --profile preview
```

Nada disso foi executado aqui — exige sua conta Expo, que eu não tenho
como criar por você (mesma situação do Stripe/Render/S3 já discutida).

## Deploy

Este app não tem deploy web próprio — `frontend/` (Vite) continua sendo o
app web deployado (Netlify). O Expo aqui é especificamente pra gerar os
binários iOS/Android via EAS.
