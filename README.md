# lab-agenda

Micro-API backend em FastAPI organizada com Clean Architecture para evolucao incremental do projeto de agenda.

## Visao Geral

O projeto esta estruturado em camadas para separar responsabilidades de dominio, casos de uso, infraestrutura e apresentacao HTTP.

No estado atual, a aplicacao entrega:

- inicializacao basica do FastAPI
- fluxo assincrono na aplicacao e nos contratos principais
- endpoint de health check em `GET /health`
- configuracao por variaveis de ambiente com Pydantic Settings
- logging centralizado
- integracao preparada com MongoDB usando Motor
- repository base generico e repository MongoDB para `Appointment`
- caso de uso assincrono para criacao de `Appointment`
- testes automatizados com pytest, incluindo testes unitarios com mock de repository

## Requisitos

- Python 3.11 ou superior
- Git

## Estrutura Do Projeto

```text
app/
	domain/
		entities/
		interfaces/
	application/
		use_cases/
	infrastructure/
		config/
		database/
		logging/
		repositories/
		services/
	presentation/
		api/
			routes/
			schemas/
tests/
	unit/
```

## Camadas

- `domain`: entidades e contratos do negocio
- `application`: casos de uso e orquestracao
- `infrastructure`: configuracao, logging, conexao com MongoDB e implementacoes concretas
- `presentation`: rotas e schemas HTTP
- `tests`: testes automatizados

## Modulo Appointment

O dominio `Appointment` foi introduzido com os campos:

- `id`
- `user_id`
- `datetime`
- `status`
- `notes`

Status suportados:

- `scheduled`
- `confirmed`
- `canceled`

O projeto ja possui:

- interface `AppointmentRepository` na camada de dominio
- `MongoBaseRepository` generico na infraestrutura
- `MongoAppointmentRepository` como implementacao concreta
- `CreateAppointmentUseCase` assincrono na camada de aplicacao

No momento, esse modulo esta preparado na arquitetura e coberto por testes unitarios, mas ainda nao esta exposto por rotas HTTP.

## Configuracao De Ambiente

O projeto usa variaveis de ambiente carregadas de `.env`.

Arquivo de exemplo:

```env
APP_NAME=Lab Agenda API
APP_VERSION=0.1.0
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
APP_MONGODB_URI=mongodb://localhost:27017
APP_MONGODB_DB_NAME=lab_agenda
```

Para iniciar a configuracao local:

```bash
cp .env.example .env
```

## Instalacao

1. Crie o ambiente virtual:

```bash
python3 -m venv .venv
```

2. Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

3. Instale as dependencias:

```bash
pip install -r requirements.txt
```

## Execucao

Para subir a API localmente:

```bash
uvicorn app.main:app --reload
```

Para recursos que dependem de persistencia MongoDB, mantenha uma instancia do MongoDB disponivel e configure `APP_MONGODB_URI` e `APP_MONGODB_DB_NAME` no `.env`.

Documentacao automatica:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoint Disponivel

### Health Check

```http
GET /health
```

Resposta esperada:

```json
{
	"status": "ok",
	"service": "Lab Agenda API",
	"version": "0.1.0"
}
```

## Testes

Para executar os testes:

```bash
pytest
```

Testes unitarios do modulo `Appointment`:

```bash
pytest tests/unit/application
```

Esses testes usam mock de repository e nao acessam banco real.

## Dependencias Principais

- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- Motor
- Pytest

## Principios Adotados

- separacao clara entre regras de negocio e framework
- injecao de dependencia por funcoes de composicao
- contratos e casos de uso orientados a async
- repositories definidos no dominio e implementados na infraestrutura
- rotas sem regra de negocio
- base preparada para extensao sem acoplamento desnecessario
