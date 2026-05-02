# lab-agenda

Micro-API backend em FastAPI organizada com Clean Architecture para evolucao incremental do projeto de agenda.

## Visao Geral

O projeto esta estruturado em camadas para separar responsabilidades de dominio, casos de uso, infraestrutura e apresentacao HTTP.

No estado atual, a aplicacao entrega:

- inicializacao basica do FastAPI
- fluxo assincrono na aplicacao e nos contratos principais
- endpoint de health check em `GET /health`
- CRUD de compromissos em `Appointment`
- agente de decisao com LangGraph para interpretar linguagem natural
- configuracao por variaveis de ambiente com Pydantic Settings
- logging centralizado
- integracao preparada com MongoDB usando Motor
- integracao com Google Calendar usando o cliente oficial da API Google
- repository base generico e repository MongoDB para `Appointment`
- casos de uso assincronos para criar, buscar, listar, atualizar e deletar `Appointment`
- criacao de evento no Google Calendar ao criar compromisso, com persistencia de `event_id`
- testes automatizados com pytest, incluindo testes unitarios e integracao sem banco real

## Requisitos

- Python 3.11 ou superior
- Git

## Estrutura Do Projeto

```text
app/
	agents/
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
- `agents`: grafo LangGraph e estrutura de decisao por linguagem natural
- `tests`: testes automatizados

## Arquitetura

```mermaid
flowchart LR
	Client[Cliente HTTP] --> Routes[Rotas FastAPI]
	User[Usuario em linguagem natural] --> AgentEntry[Entrada do Agente]

	subgraph Presentation[Presentation]
		Routes
		Schemas[Schemas Pydantic]
	end

	subgraph Agents[Agents]
		AgentEntry
		Decision[No de decisao]
		CreateAction[No de acao: criar]
		ListAction[No de acao: listar]
		UpdateAction[No de acao: atualizar]
		DeleteAction[No de acao: deletar]
	end

	subgraph Application[Application]
		CreateUC[CreateAppointmentUseCase]
		CrudUC[Get/List/Update/Delete Use Cases]
	end

	subgraph Domain[Domain]
		Appointment[Appointment]
		RepoPort[AppointmentRepository]
		CalendarPort[CalendarService]
	end

	subgraph Infrastructure[Infrastructure]
		MongoRepo[MongoAppointmentRepository]
		GoogleSvc[GoogleCalendarService]
		Settings[Settings]
		Mongo[(MongoDB)]
	end

	GCal[Google Calendar API]

	Routes --> Schemas
	Routes --> CreateUC
	Routes --> CrudUC
	AgentEntry --> Decision
	Decision --> CreateAction
	Decision --> ListAction
	Decision --> UpdateAction
	Decision --> DeleteAction
	CreateAction --> CreateUC
	ListAction --> CrudUC
	UpdateAction --> CrudUC
	DeleteAction --> CrudUC

	CreateUC --> Appointment
	CrudUC --> Appointment

	CreateUC --> RepoPort
	CrudUC --> RepoPort
	CreateUC --> CalendarPort

	RepoPort -. implementado por .-> MongoRepo
	CalendarPort -. implementado por .-> GoogleSvc

	MongoRepo --> Mongo
	GoogleSvc --> GCal
	Settings --> MongoRepo
	Settings --> GoogleSvc
```

## Modulo Appointment

O dominio `Appointment` foi introduzido com os campos:

- `id`
- `user_id`
- `datetime`
- `status`
- `notes`
- `event_id`

Status suportados:

- `scheduled`
- `confirmed`
- `canceled`

O projeto ja possui:

- interface `AppointmentRepository` na camada de dominio
- interface `CalendarService` na camada de dominio
- `MongoBaseRepository` generico na infraestrutura
- `MongoAppointmentRepository` como implementacao concreta
- `GoogleCalendarService` como adaptador da API externa
- casos de uso de criacao, busca, listagem, atualizacao e delecao na camada de aplicacao
- rotas HTTP com schemas Pydantic para request e response

Endpoints disponiveis para compromissos:

- `POST /appointments`
- `GET /appointments/{id}`
- `GET /appointments`
- `PUT /appointments/{id}`
- `DELETE /appointments/{id}`

## Agente LangGraph

O projeto possui um agente separado do FastAPI para interpretar linguagem natural e decidir a intencao relacionada a compromissos.

Fluxo do agente:

- no de entrada
- no de decisao
- nos de acao para criar, listar, atualizar e deletar

Saida do agente:

- intencao estruturada
- parametros extraidos da mensagem do usuario

O agente foi implementado de forma assincrona com LangGraph para evitar bloqueio do servidor em cenarios concorrentes e pode reutilizar os casos de uso existentes por meio de um executor separado.

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
APP_GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
APP_GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service-account.json
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

Para a integracao com Google Calendar, configure `APP_GOOGLE_CALENDAR_ID` e `APP_GOOGLE_SERVICE_ACCOUNT_FILE` com as credenciais da conta de servico. As credenciais devem ficar fora do codigo-fonte e ser carregadas por variaveis de ambiente.

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

### Appointments

Exemplo de criacao:

```http
POST /appointments
```

```json
{
	"user_id": "user-123",
	"datetime": "2026-05-03T15:30:00Z",
	"status": "scheduled",
	"notes": "consulta inicial"
}
```

Ao criar um compromisso, a aplicacao cria um evento correspondente no Google Calendar e persiste o `event_id` retornado pela API.

O campo `datetime` deve incluir timezone e `status` aceita apenas:

- `scheduled`
- `confirmed`
- `canceled`

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

Teste unitario do agente LangGraph:

```bash
pytest tests/unit/agents
```

Teste de integracao da API de compromissos:

```bash
pytest tests/integration
```

## Dependencias Principais

- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- Motor
- LangGraph
- Pytest

## Principios Adotados

- separacao clara entre regras de negocio e framework
- injecao de dependencia por funcoes de composicao
- contratos e casos de uso orientados a async
- repositories definidos no dominio e implementados na infraestrutura
- rotas sem regra de negocio
- base preparada para extensao sem acoplamento desnecessario
