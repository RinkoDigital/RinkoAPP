# Rinko Delivery Payment API

API/SaaS B2B para registrar entregas e calcular automaticamente quanto cada
motorista tem a receber.

## Problema

Empresas de last-mile podem levar dias ou semanas entre a entrega e o
pagamento devido a processos de conferência, reconciliação e cálculo.

## Fluxo do MVP

```
Entrega → registro → validação → cálculo por pacote → valor devido → relatório
```

A empresa continua realizando o pagamento pelos meios atuais — não há
Stripe, Wise ou movimentação financeira nesta etapa. A API apenas produz o
registro validado, o valor devido por motorista e o relatório de pagamento.

## Dois níveis de acesso

- **Admin (empresa)** — autenticado por `x-api-key`. Cadastra motoristas e
  clients, registra e valida lotes de entrega, e marca pagamentos.
  Verifica o trabalho e efetua o pagamento pelos meios atuais da empresa.
- **Driver (motorista)** — autenticado por login próprio (email + senha,
  token JWT). Só enxerga os próprios dados: suas entregas, seu relatório de
  pagamento, e pode registrar a prova de entrega/devolução dos próprios
  pacotes. Não consegue validar lotes nem marcar pagamentos — isso é
  exclusivo do admin.

## Modelo de dados

- **Company**: cliente B2B, autenticado por API key, com uma tarifa padrão
  por pacote (`default_rate_cents`).
- **Driver**: motorista de uma empresa. Cadastrado pelo admin; se tiver
  email, recebe um `invite_token` pra criar a própria senha e acessar o
  sistema (`has_account` indica se já ativou a conta). Usa o sistema
  gratuitamente para acompanhar entregas e ganhos.
- **Client**: o parceiro para quem a empresa entrega pacotes (ex.: UniUni,
  GOFO). Pode ter uma tarifa própria (`default_rate_cents`), que sobrepõe a
  tarifa padrão da empresa.
- **Delivery**: um lote diário de entregas de um motorista para um client
  (`assigned_count`, `exceptions_count` → `payable_count` calculado).
  Status `pending` → `validated` ou `rejected`. O valor devido
  (`amount_due_cents`) só é calculado na validação. Depois de validado, o
  lote pode ser marcado como pago (`payment_status`) para fins de
  reconciliação — sem mover dinheiro de fato.
- **Package**: o detalhe individual de um pacote dentro de um lote —
  entregue (com prova de entrega: foto, código de confirmação escaneado,
  geolocalização) ou devolvido (com motivo). Os totais do lote
  (`assigned_count`/`exceptions_count`) continuam sendo a fonte de verdade
  pro cálculo de pagamento; o `Package` é a camada de evidência/detalhe.

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/companies` | admin key | Cria uma empresa e retorna a API key (mostrada uma única vez) |
| POST | `/drivers` | company key | Cadastra um motorista |
| GET | `/drivers` | company key | Lista motoristas |
| POST | `/clients` | company key | Cadastra um client (ex.: UniUni, GOFO), com tarifa própria opcional |
| GET | `/clients` | company key | Lista clients |
| POST | `/deliveries` | company key | Registra um lote diário de entregas (status `pending`) |
| GET | `/deliveries` | company key | Lista lotes (filtros: `driver_id`, `client_id`, `status`, `payment_status`, `start_date`, `end_date`) |
| POST | `/deliveries/{id}/validate` | company key | Valida o lote e calcula o valor devido |
| POST | `/deliveries/{id}/reject` | company key | Rejeita o lote com um motivo |
| POST | `/deliveries/{id}/mark-paid` | company key | Marca um lote validado como pago (reconciliação) |
| POST | `/deliveries/{id}/packages` | company key | Registra um pacote entregue (com prova) ou devolvido (com motivo) |
| GET | `/deliveries/{id}/packages` | company key | Lista os pacotes de um lote |
| POST | `/deliveries/{id}/packages/{package_id}/pod-photo` | company key | Upload da foto de prova de entrega (JPEG/PNG/WebP, multipart) |
| GET | `/reports/drivers/{driver_id}/pay-report` | company key | Relatório de pagamento do motorista (JSON) para um período |
| GET | `/reports/drivers/{driver_id}/pay-report.docx` | company key | O mesmo relatório, como arquivo `.docx` para download |
| POST | `/auth/driver/accept-invite` | público | Motorista define a senha com o `invite_token` recebido e já volta logado |
| POST | `/auth/driver/login` | público | Login do motorista (email + senha) → token JWT |
| GET | `/me` | driver token | Perfil do motorista logado |
| GET | `/me/deliveries` | driver token | Lista só as próprias entregas |
| GET | `/me/deliveries/{id}/packages` | driver token | Lista os pacotes do próprio lote |
| POST | `/me/deliveries/{id}/packages` | driver token | Motorista registra a própria prova de entrega/devolução |
| POST | `/me/deliveries/{id}/packages/{package_id}/pod-photo` | driver token | Upload da própria foto de prova de entrega |
| GET | `/me/pay-report` | driver token | O próprio relatório de pagamento (JSON) |

Autenticação de empresa via header `x-api-key`. Criação de empresa via
header `x-admin-key` (ver `ADMIN_API_KEY` no `.env`). Autenticação de
motorista via header `Authorization: Bearer <token>`, obtido no login.

### Relatório de pagamento do motorista

`GET /reports/drivers/{driver_id}/pay-report?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
retorna, a partir dos lotes validados no período: detalhe diário por
client, resumo por client, resumo geral (completion rate, compensação
total) e reconciliação de pagamento (total ganho, já pago, saldo
pendente). O endpoint `.docx` gera o mesmo relatório como um documento
Word, no layout de relatório semanal de performance e pagamento por
motorista.

### Prova de entrega e devoluções

Cada pacote dentro de um lote pode ser registrado individualmente via
`POST /deliveries/{id}/packages`, com `outcome` `delivered` ou `returned`.
Entregues aceitam código de confirmação escaneado (`pod_scan_code`) e
geolocalização (`pod_latitude`/`pod_longitude`) no próprio registro, e uma
foto via upload separado (`pod-photo`, `multipart/form-data`, até 8MB,
JPEG/PNG/WebP). Devolvidos exigem um `return_reason` (`refused`,
`wrong_address`, `damaged`, `undeliverable`, `other`) e aceitam uma nota
livre. As fotos ficam em `UPLOAD_DIR` (padrão `uploads/`, fora do
controle de versão) e são servidas em `/uploads/{arquivo}` — em produção,
trocar por um bucket S3 por trás da mesma função `save_pod_photo`. Tanto o
admin (`/deliveries/{id}/packages`) quanto o próprio motorista
(`/me/deliveries/{id}/packages`) podem registrar pacotes — o motorista só
no que for de um lote seu.

### Origem do registro (`source`) — ponto de integração futuro

Cada `Package` tem um campo `source`: `manual` (motorista registrou pelo
app da Rinko — o padrão hoje), ou `uniuni`/`gofo`/`other_platform` pra
quando existir integração real com as plataformas parceiras (elas
capturam a prova de entrega nos próprios apps dos motoristas; nesse caso
a Rinko só puxaria o dado, não pediria pro motorista registrar de novo).
Isso ainda **não está integrado** — hoje não há acesso de API da
UniUni/GOFO — mas o campo já existe pra não travar o esquema quando essa
integração vier. Só o admin pode marcar um pacote como vindo de uma
plataforma externa (`POST /deliveries/{id}/packages` com `source` e
`external_reference`); o endpoint do motorista (`/me/...`) sempre força
`source=manual`, mesmo que o payload tente informar outra coisa.

### Onboarding do motorista

1. Admin cadastra o motorista com `POST /drivers` incluindo o `email`.
2. A resposta traz um `invite_token` (a empresa envia esse link/código pro
   motorista pelo canal que preferir — SMS, WhatsApp, email).
3. Motorista chama `POST /auth/driver/accept-invite` com o token e a senha
   escolhida — a conta é ativada e ele já recebe um token de acesso.
4. Depois disso, login normal via `POST /auth/driver/login`.

O token expira em `DRIVER_TOKEN_EXPIRE_MINUTES` (padrão 14 dias); o convite
expira em `DRIVER_INVITE_EXPIRE_MINUTES` (padrão 7 dias) e é de uso único.

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
docker compose up -d db
alembic upgrade head

uvicorn app.main:app --reload
```

## Testes

```bash
pytest
```

Os testes usam SQLite em memória e não dependem do Postgres.

## Próximos passos

- Validar com empresas reais quanto tempo e dinheiro elas gastam hoje na
  reconciliação, antes de expandir o MVP.
- Regras de tarifa mais ricas (por tipo de pacote, por região, etc.), hoje é
  uma tarifa fixa por empresa.
- Exportação de relatórios (CSV/PDF) para uso no processo de pagamento
  existente da empresa.
- Integração real com UniUni/GOFO (API oficial, se disponibilizarem, ou
  importação de arquivo exportado do portal delas) para puxar prova de
  entrega automaticamente em vez do motorista registrar manualmente.
