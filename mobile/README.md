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
  números calculados, registro/remoção de push token (via web, onde vira
  no-op), upload de evidence com carimbo de GPS (localização mockada via
  Playwright) — tudo verificado com Playwright, sem erros de console
- **Não testado**: build nativo de verdade (iOS/Android). Esse ambiente
  não tem simulador nem dispositivo, e `api.expo.dev` (usado pelo EAS)
  está bloqueado pela política de rede daqui — só dá pra validar via
  `--web`, que usa react-native-web e não passa pelo runtime nativo real.

## Notificações push

`src/native/pushNotifications.ts` pede permissão, pega o Expo push token
do device e registra em `POST /account/push-token` assim que o motorista
loga (chamado em `app/(tabs)/_layout.tsx`); no logout, `unregisterPushToken()`
remove o token (`DELETE /account/push-token`), pra um device deslogado
parar de receber lembretes daquele motorista.

O que dispara os lembretes é um job no backend (`app/jobs/send_reminders.py`,
ver README da raiz) — este app só cuida de registrar/desregistrar o token
e receber a notificação quando ela chega.

**Sem token de verdade neste ambiente**: `getExpoPushTokenAsync` exige um
`projectId` de um projeto EAS real (só existe depois de `eas init` numa
conta Expo). Sem isso, `registerForPushNotificationsAsync()` retorna
`null` e loga um aviso — não crasha, só não registra nada. Testado até
esse ponto (o app roda normal, sem token); a entrega de notificação de
verdade num device físico não foi validada aqui.

## GPS na evidência

Ao escolher uma foto pra evidence (`pickImage` em
`app/sessions/[sessionId]/index.tsx`), o app pede a localização
(`src/native/locationStamp.ts`, via `expo-location`), converte as
coordenadas num endereço com o geocoder nativo do sistema
(`Location.reverseGeocodeAsync` — sem chave, cai de volta pras
coordenadas cruas se falhar) e carimba o endereço + data/hora no canto
inferior direito da imagem antes de subir — React Native não tem
`<canvas>`, então isso é feito renderizando a foto + o texto fora da
tela (`src/components/LocationStamper.tsx`) e capturando com
`react-native-view-shot`. Os dados também vão como campos separados
(`latitude`/`longitude`/`address`/`captured_at`), não só cravados na
imagem.

Testado via `expo start --web` com geolocalização mockada pelo Playwright
— confirmei que a imagem final baixada da API tem o carimbo certo. No
web, `captureRef` devolve uma data URI em vez de um arquivo (limitação só
do preview em navegador); o upload trata os dois casos.

## Share Sheet (evidence direto de outros apps)

**Ainda não implementado neste app.** O caminho seria uma lib de
share-intent (ex.: `expo-share-intent`) — isso exige um dev client
customizado (não funciona no Expo Go puro) e não foi validado aqui por
falta de acesso a simulador/EAS. Fica como próximo passo.

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
