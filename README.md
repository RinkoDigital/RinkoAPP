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

## Modelo de dados

- **Company**: cliente B2B, autenticado por API key, com uma tarifa padrão
  por pacote (`default_rate_cents`).
- **Driver**: motorista de uma empresa. Usa o sistema gratuitamente para
  acompanhar entregas e ganhos.
- **Client**: o parceiro para quem a empresa entrega pacotes (ex.: UniUni,
  GOFO). Pode ter uma tarifa própria (`default_rate_cents`), que sobrepõe a
  tarifa padrão da empresa.
- **Delivery**: um lote diário de entregas de um motorista para um client
  (`assigned_count`, `exceptions_count` → `payable_count` calculado).
  Status `pending` → `validated` ou `rejected`. O valor devido
  (`amount_due_cents`) só é calculado na validação. Depois de validado, o
  lote pode ser marcado como pago (`payment_status`) para fins de
  reconciliação — sem mover dinheiro de fato.

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
| GET | `/reports/drivers/{driver_id}/pay-report` | company key | Relatório de pagamento do motorista (JSON) para um período |
| GET | `/reports/drivers/{driver_id}/pay-report.docx` | company key | O mesmo relatório, como arquivo `.docx` para download |

Autenticação de empresa via header `x-api-key`. Criação de empresa via
header `x-admin-key` (ver `ADMIN_API_KEY` no `.env`).

### Relatório de pagamento do motorista

`GET /reports/drivers/{driver_id}/pay-report?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
retorna, a partir dos lotes validados no período: detalhe diário por
client, resumo por client, resumo geral (completion rate, compensação
total) e reconciliação de pagamento (total ganho, já pago, saldo
pendente). O endpoint `.docx` gera o mesmo relatório como um documento
Word, no layout de relatório semanal de performance e pagamento por
motorista.

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
