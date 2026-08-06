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
| POST | `/auth/signup` | público | Motorista cria a própria conta → token |
| POST | `/auth/login` | público | Login (email + senha) → token |
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

## Planos: Free vs. Pro

Todo `Driver` nasce no plano `free` (`Driver.plan`). O que fica de fora do
plano pago é deliberadamente pequeno, porque o registro em si — o que
prova o trabalho — não pode ser a parte paga:

**Sempre grátis, em qualquer plano:**
- O Work Report em JSON (`GET /sessions/{id}/work-report`)
- A exportação em CSV (`GET /sessions/export.csv`)
- O Payment Ledger (`GET /ledger`)
- Registro ilimitado de sessions, carriers e packages

**Reservado ao plano `pro`:**
- Exportação do Work Report formatado em `.docx`
  (`GET /sessions/{id}/work-report.docx` → `402 Payment Required` no free)
- Evidence acima de 3 arquivos por sessão (`POST /sessions/{id}/evidence`
  → `402 Payment Required` a partir do 4º no free; ilimitado no pro)

A política de gating fica centralizada em `app/plans.py`
(`can_export_docx`, `evidence_limit`). `POST /account/plan` hoje é uma
troca manual de flag — **não existe integração de billing real ainda**
(sem Stripe, sem cobrança recorrente); é o mesmo tipo de placeholder que o
MVP já usa para "pagamento recebido" em geral. Ligar isso a um provedor de
pagamento de verdade é um dos itens antes de qualquer lançamento público.

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
