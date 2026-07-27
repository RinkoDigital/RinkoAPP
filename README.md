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
| GET | `/deliveries/{id}/proof` | company key | Prova de entrega do lote (JSON) — disponível assim que validado, com ou sem pagamento |
| GET | `/deliveries/{id}/proof.docx` | company key | A mesma prova, como arquivo `.docx` |
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
| GET | `/me/deliveries/{id}/proof` | driver token | Prova de entrega de um lote próprio (JSON) |
| GET | `/me/deliveries/{id}/proof.docx` | driver token | A mesma prova, como `.docx` |
| POST | `/companies/me/rotate-webhook-secret` | company key | Gera um novo segredo de webhook, invalidando o anterior |
| POST | `/webhooks/{company_id}/{platform}` | webhook secret | Recebe eventos de entrega de uma plataforma parceira (UniUni/GOFO) — especulativo, ver seção abaixo |

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

### Prova de entrega do lote (independente de pagamento)

Diferente do relatório do período (que soma vários lotes) e do
pagamento em si, essa prova existe assim que o lote é **validado** —
`POST /deliveries/{id}/validate` — e não depende de já ter sido pago.
Serve dois propósitos diferentes: provar pra **plataforma parceira**
(UniUni/GOFO) que a entrega aconteceu, mesmo antes do motorista
receber; e, quando já pago, também funcionar como comprovante desse
pagamento. Reúne numa única página: valor calculado, quando foi
validado, status do pagamento (`pending` ou `paid` — com valor e data
quando aplicável), e um resumo da prova de entrega registrada (quantos
pacotes foram logados, quantos têm foto, quantos têm código de
confirmação escaneado). Tem número de referência próprio
(`PRF-XXXXXXXX`). Disponível pro admin (`/deliveries/{id}/proof`) e pro
próprio motorista (`/me/deliveries/{id}/proof`), sempre em JSON ou
`.docx`.

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

### Webhook de entrada (UniUni/GOFO)

`POST /webhooks/{company_id}/{platform}` — `platform` é `uniuni`, `gofo`
ou `other`. Autenticado por um segredo compartilhado no header
`x-webhook-secret` (não é o `x-api-key` da empresa — é um segredo
separado, gerado junto com a empresa e rotacionável via
`POST /companies/me/rotate-webhook-secret`).

Esse endpoint ainda é **especulativo**: não existe integração real com
UniUni/GOFO hoje, então o formato do payload abaixo é o que a Rinko
define pra si mesma, não o que essas plataformas realmente enviam. Serve
pra já ter a peça pronta quando (se) alguma delas topar apontar um
webhook pra cá — nesse caso, provavelmente vai precisar de uma camada de
tradução na frente pra converter o payload real delas pro formato daqui.

```json
{
  "driver_external_id": "uniuni-driver-42",
  "client_name": "UniUni",
  "batch_date": "2026-07-06",
  "tracking_code": "UNI-PKG-1",
  "outcome": "delivered",
  "pod_photo_url": "https://.../pod/abc123.jpg",
  "pod_scan_code": "SCAN-9001",
  "external_reference": "uniuni-event-abc123"
}
```

`driver_external_id` precisa bater com o `external_id` cadastrado no
`Driver` (é assim que o evento é associado a um motorista específico), e
`client_name` precisa bater com um `Client` já cadastrado na empresa. O
lote (`Delivery`) do dia é criado automaticamente na primeira mensagem e
os totais (`assigned_count`/`exceptions_count`) crescem a cada evento —
por isso o webhook só aceita eventos enquanto o lote está `pending`; uma
vez validado ou rejeitado pelo admin, novos eventos pro mesmo dia
retornam erro. Eventos repetidos (mesmo `tracking_code`) são ignorados
de forma idempotente, sem duplicar nem dar erro — importante porque
sistemas de webhook costumam reenviar em caso de timeout.

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
- Confirmar com UniUni/GOFO se elas conseguem apontar um webhook pra Rinko
  (o receptor já existe) ou se o caminho real vai ser API oficial delas
  ou importação de arquivo — o payload atual do webhook é uma hipótese
  nossa, não o formato real delas.
