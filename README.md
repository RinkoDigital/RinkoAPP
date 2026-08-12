# Rinko — Independent Driver Work Record

*Your routes. Your work. Your records.*

Uma ferramenta que cria um registro verificável do trabalho realizado por um
motorista independente — separado do sistema da contratante (UniUni, GOFO,
OnTrac, etc.).

## O problema

Hoje o motorista trabalha dentro do sistema da contratante:

```
contratante → fornece rota → controla os dados → calcula pagamento → paga motorista
```

Se houver divergência — a empresa diz que foram 118 pacotes quando o
motorista acredita ter entregue 137 — a principal fonte de dados costuma
pertencer justamente à empresa que está sendo questionada.

## O que a Rinko é (Fase 1)

Uma segunda camada, independente:

```
CONTRATANTE → Route assigned → DRIVER → RINKO (Independent Record) → DRIVER'S RECORD
```

A Rinko não é uma plataforma de delivery. Não compete com o software da
UniUni, OnTrac etc. — não determina rotas, não despacha, não gerencia
frota. Ela documenta, do lado do motorista, o que foi trabalhado, o que é
devido, e o que já foi recebido — com evidência anexada — pra que o
motorista tenha seu próprio registro contemporâneo, não uma reconstrução
de memória meses depois.

Isso **não transforma automaticamente um relatório em prova conclusiva**
numa disputa legal — autenticidade, contrato, regras probatórias ainda
importam — mas cria documentação muito melhor do que tentar reconstruir
uma rota depois do fato.

## Conta é do motorista, ponto

Não existe camada de empresa/admin. O motorista cria a própria conta
(`POST /auth/signup`) e é dono de todos os dados dela. Um "Carrier"
(UniUni, GOFO, OnTrac...) é só um registro dentro da conta do motorista —
não um tenant que o controla, não um diretório compartilhado. Dois
motoristas cadastrando "UniUni" têm dois registros independentes.

## Modelo de dados

- **Driver**: o motorista, conta raiz. Login por email + senha.
- **Carrier**: a contratante que atribuiu a rota (UniUni, GOFO, OnTrac...),
  registrada pelo próprio motorista, com uma tarifa padrão opcional.
- **WorkSession**: uma rota/turno trabalhado — o registro independente em
  si. `route_id`, data, horário de início/fim, pacotes atribuídos,
  exceções, milhagem, tarifa acordada. Começa `open`; ao ser encerrada
  (`closed`) calcula o valor bruto esperado. Depois disso, o motorista
  registra o que recebeu — que pode ser igual, menor (pagamento parcial)
  ou não registrado ainda — e a diferença é calculada automaticamente.
- **Evidence**: documentos anexados à sessão — print da rota, print da
  rate oferecida, sessão de GPS, registro de conclusão, settlement
  statement. É a evidência de nível de sessão, a camada principal do
  MVP.
- **Package** *(opcional)*: detalhe pacote a pacote — prova de entrega
  (foto, código escaneado, geolocalização) ou devolução (motivo). Fica
  disponível pra quem quiser granularidade além dos totais da sessão; não
  é obrigatório.

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/auth/signup` | público | Motorista cria a própria conta → token (dispara email de verificação) |
| POST | `/auth/login` | público | Login (email + senha) → token |
| POST | `/auth/verify-email` | público | Confirma o email a partir do token enviado no signup |
| POST | `/auth/resend-verification` | público | Reenvia o email de verificação (resposta genérica, não revela se a conta existe) |
| POST | `/auth/request-password-reset` | público | Solicita reset de senha (resposta genérica, não revela se a conta existe) |
| POST | `/auth/reset-password` | público | Confirma o reset com o token recebido e define a nova senha |
| GET | `/account/plan` | driver token | Consulta o plano atual e o que ele libera |
| POST | `/account/plan` | driver token | Troca de plano (`free`/`pro`) — hoje é uma flag manual, sem billing real |
| POST | `/carriers` | driver token | Registra uma contratante (ex.: UniUni) |
| GET | `/carriers` | driver token | Lista as contratantes do motorista |
| POST | `/sessions` | driver token | Inicia uma work session (`open`) |
| GET | `/sessions` | driver token | Lista sessões (filtros: `status`, `carrier_id`, `start_date`, `end_date`) |
| GET | `/sessions/export.csv` | driver token | Exporta todas as sessões em CSV |
| GET | `/sessions/{id}` | driver token | Detalhe de uma sessão |
| POST | `/sessions/{id}/close` | driver token | Encerra a sessão e calcula o valor bruto esperado |
| POST | `/sessions/{id}/record-payment` | driver token | Registra o valor recebido (calcula a diferença) |
| POST | `/sessions/{id}/evidence` | driver token | Anexa um documento (print, GPS, settlement statement...) |
| GET | `/sessions/{id}/evidence` | driver token | Lista os documentos anexados |
| POST | `/sessions/{id}/packages` | driver token | *(opcional)* Registra prova de entrega/devolução por pacote |
| GET | `/sessions/{id}/packages` | driver token | Lista os pacotes da sessão |
| POST | `/sessions/{id}/packages/{package_id}/pod-photo` | driver token | Upload da foto de prova daquele pacote |
| GET | `/sessions/{id}/work-report` | driver token | O Rinko Work Report (JSON) — só após encerrada |
| GET | `/sessions/{id}/work-report.docx` | driver token | O mesmo relatório, como `.docx` |
| GET | `/ledger` | driver token | Payment ledger — quanto está pendente de receber, e onde |

Autenticação via header `Authorization: Bearer <token>`, obtido no
signup/login.

### Verificação de email e reset de senha

O signup já dispara um token de verificação de email; o login **não**
exige o email verificado ainda — isso fica marcado em `Driver.email_verified`
pra o produto decidir depois se quer travar alguma ação nisso, sem
adicionar fricção ao MVP agora.

O reset de senha funciona de ponta a ponta: `POST /auth/request-password-reset`
gera um token de uso único (expira em 30 min) e `POST /auth/reset-password`
troca a senha. Ambos os endpoints de "esqueci minha senha" e "reenviar
verificação" sempre respondem `202`, verificando ou não a conta, pra não
vazar quais emails têm cadastro.

**O que ainda é placeholder:** não existe provedor de email real (SES,
SendGrid...) — `app/services/email.py` só loga a mensagem (`logger.info`),
com o token dentro. Antes de publicar, isso precisa virar um envio de
email de verdade; a lógica de token/expiração/uso único já está pronta e
testada, só falta trocar a "entrega".

### O Rinko Work Report

Ao encerrar uma sessão (`POST /sessions/{id}/close`), o motorista pode
gerar o relatório estruturado — o verdadeiro produto:

```
RINKO — INDEPENDENT WORK RECORD

Driver / Carrier / Service date / Route ID

WORK RECORD
Route started / completed, packages assigned/completed, exceptions, distance

COMPENSATION RECORD
Agreed rate, expected gross, payment due, payment status
(e, quando aplicável, valor recebido e a diferença)

SUPPORTING RECORDS
✓ Route screenshot  ✓ Rate screenshot  ✓ GPS session  ✓ Settlement statement...
```

Disponível como JSON (`/work-report`) ou documento Word (`/work-report.docx`).

### Payment Ledger

`GET /ledger` soma o que está pendente de receber (sessões encerradas com
pagamento parcial ou não registrado) e lista cada uma, pra o motorista
descobrir exatamente quais rotas ainda não foram pagas.

### Exportação — sem lock-in

Desde o dia 1: `GET /sessions/export.csv` exporta todo o histórico de
sessões. Os documentos de evidência (`Evidence.file_url`) continuam
baixáveis diretamente. Se a promessa da Rinko é dar ao motorista
independência sobre o próprio histórico, prender esse histórico dentro de
outro sistema fechado contradiz a proposta.

## Planos: Free vs. Pro (billing desativado por enquanto)

Existe uma estrutura de planos (`Driver.plan`, `FREE`/`PRO`, endpoints
`GET`/`POST /account/plan`) desenhada pra separar o que é sempre grátis
(Work Report em JSON, CSV, Payment Ledger — o registro em si nunca é a
parte paga) do que poderia ser reservado a um plano pago (`.docx`
formatado, evidence acima de um limite por sessão).

**Por decisão de produto, o gating está desligado agora**: não existe
integração de billing real (sem Stripe, sem cobrança), e a prioridade
atual é validar se o Work Report resolve dor suficiente antes de cobrar
por qualquer coisa — então todo mundo tem acesso completo, `.docx` e
evidence ilimitados, independente do valor de `Driver.plan`. Isso está
centralizado em `app/plans.py` (`PLAN_LIMITS`) — free e pro apontam pros
mesmos limites (irrestritos) até essa decisão mudar.

Quando fizer sentido cobrar, é só devolver `PLAN_LIMITS[FREE]` pros
limites reais e plugar um provedor de pagamento em `POST /account/plan`
(hoje é só uma troca manual de flag).

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
docker compose up -d db
alembic upgrade head

uvicorn app.main:app --reload
```

## Front-end

Dois clientes, um backend:

- `frontend/` — web app (React + Vite), deployado via Netlify. Ver
  `frontend/README.md`.
- `mobile/` — app nativo iOS/Android (Expo + React Native + Expo Router),
  buildado na nuvem via EAS Build (sem precisar de Mac/Xcode local). Ver
  `mobile/README.md`.

Os dois consomem a mesma API e replicam as mesmas telas/tema — não
compartilham código de UI entre si (React DOM vs. React Native têm
primitivos diferentes), mas seguem a mesma estrutura.

## Deploy

### Backend

`Dockerfile` na raiz builda a API e roda `alembic upgrade head` antes de
subir o servidor. `render.yaml` é um Blueprint pronto pro
[Render](https://render.com) — sobe o serviço web (a partir do Dockerfile)
e provisiona um Postgres gerenciado, já conectando `DATABASE_URL` entre os
dois. Qualquer host que rode um Dockerfile (Railway, Fly.io, etc.) funciona
do mesmo jeito, só sem o blueprint pronto.

Variáveis de ambiente que precisam existir em produção (ver
`.env.example`): `DATABASE_URL`, `JWT_SECRET` (gere um valor real — o
blueprint do Render já gera um automaticamente).

**Storage e email têm um backend padrão que não serve pra produção de
verdade:**
- `STORAGE_BACKEND=local` (padrão) grava evidence/POD no disco do próprio
  container. Isso funciona pra rodar localmente, mas a maioria dos hosts
  (incluindo o Render sem um Disk pago) tem filesystem efêmero — os
  arquivos somem no próximo deploy ou restart. Antes de usar com dados
  reais, troque pra `STORAGE_BACKEND=s3` e preencha `S3_BUCKET`,
  `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` (e
  `S3_ENDPOINT_URL`/`S3_PUBLIC_BASE_URL` se for Cloudflare R2, Backblaze
  B2, ou qualquer coisa que não seja AWS S3 direto).
- `EMAIL_BACKEND=log` (padrão) não entrega email nenhum — só loga a
  mensagem, então verificação de conta e reset de senha não chegam pra
  ninguém. Troque pra `EMAIL_BACKEND=smtp` e preencha `SMTP_HOST`,
  `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` com as
  credenciais de qualquer provedor (SendGrid, Postmark, SES, Mailgun...) —
  é SMTP puro, sem SDK específico de provedor.

Ambos os backends foram testados (mockados) em `tests/test_storage_backends.py`
e `tests/test_email_backend.py`, e o schema/migrations foram validados
rodando de verdade contra um Postgres real (não só o SQLite dos testes).

### Front-end

`netlify.toml` na raiz já aponta pro subdiretório `frontend/`, builda com
Vite e configura o fallback de SPA pro react-router funcionar em rotas
diretas. No Netlify, é só conectar o repositório — o `netlify.toml` cobre
o resto. Na Vercel funciona igual, mas o "Root Directory" do projeto
precisa ser configurado como `frontend` no dashboard (não tem equivalente
em arquivo). Em qualquer uma das duas, defina `VITE_API_BASE_URL` nas
variáveis de ambiente do projeto, apontando pro backend já deployado.

### App nativo (mobile/)

`eas.json` já tem os perfis de build configurados. Com uma conta Expo
(grátis pra começar): `eas build --platform ios --profile preview` builda
o binário na nuvem deles — não precisa de Mac/Xcode local, ao contrário
do caminho Capacitor que foi abandonado (ver `mobile/README.md` pro porquê).
Não executado aqui — exige a conta Expo, que só você pode criar.

### O que não foi verificado aqui

Não existe Docker daemon neste ambiente (sandbox sem suporte a
containers), então o `Dockerfile` não foi buildado de verdade — só
revisado. O que **foi** verificado: as migrations do Alembic rodam limpo
num Postgres real (não só SQLite), e a API completa (signup, sessão,
evidence, work report em `.docx`, export CSV) funciona ponta a ponta
contra esse Postgres.

## Testes

```bash
pytest
```

Os testes usam SQLite em memória e não dependem do Postgres — exceto a
verificação manual contra Postgres real descrita acima, que não faz parte
da suíte automatizada.

## Evolução do produto (não faz parte do MVP)

```
Fase 1  Driver Work Records        ← isto aqui
Fase 2  Payments + Disputes
Fase 3  Driver Management
Fase 4  Rinko Dispatch
Fase 5  Rinko Routes
Fase 6  Rinko Warehouse
        → Rinko Last-Mile Network
```

As entidades fundamentais (driver, work session, carrier, package,
evidence) são desenhadas pra continuar valendo conforme o produto evolui
— o MVP não é descartado quando o negócio cresce.

## Próximos passos

- Validar com motoristas reais se o Work Report, sozinho, já resolve dor
  suficiente pra pagar por isso, antes de expandir.
- Geração de PDF do Work Report (hoje é `.docx`) — mais universal pra
  anexar numa disputa.
- Confirmar com UniUni/GOFO/OnTrac se algum tipo de integração
  (webhook, API, importação de arquivo) é viável — nada disso existe
  hoje; o motorista registra tudo manualmente ou anexa a evidência que já
  tem.
