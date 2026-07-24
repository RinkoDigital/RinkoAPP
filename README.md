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
registro validado e o valor devido por motorista.

## Modelo de dados

- **Company**: cliente B2B, autenticado por API key, com uma tarifa padrão
  por pacote (`default_rate_cents`).
- **Driver**: motorista de uma empresa. Usa o sistema gratuitamente para
  acompanhar entregas e ganhos.
- **Delivery**: uma entrega registrada, com status `pending` → `validated`
  ou `rejected`. O valor devido (`amount_due_cents`) só é calculado quando a
  entrega é validada.

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/companies` | admin key | Cria uma empresa e retorna a API key (mostrada uma única vez) |
| POST | `/drivers` | company key | Cadastra um motorista |
| GET | `/drivers` | company key | Lista motoristas |
| POST | `/deliveries` | company key | Registra uma entrega (status `pending`) |
| GET | `/deliveries` | company key | Lista entregas (filtros: `driver_id`, `status`) |
| POST | `/deliveries/{id}/validate` | company key | Valida a entrega e calcula o valor devido |
| POST | `/deliveries/{id}/reject` | company key | Rejeita a entrega com um motivo |
| GET | `/reports/drivers/{driver_id}` | company key | Relatório de ganhos de um motorista |
| GET | `/reports/summary` | company key | Resumo de entregas/valores da empresa |

Autenticação de empresa via header `x-api-key`. Criação de empresa via
header `x-admin-key` (ver `ADMIN_API_KEY` no `.env`).

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
