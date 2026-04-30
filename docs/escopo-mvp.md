# Escopo do MVP

## Objetivo

Definir o escopo do produto minimo viavel de uma micro-API para integracao com o Google Calendar, com foco em operacoes basicas de consulta e criacao de compromissos.

O MVP deve disponibilizar uma interface HTTP simples para que um cliente autenticado possa consultar eventos e registrar novos eventos em uma agenda Google previamente autorizada, com baixo acoplamento e facilidade de evolucao.

## Requisitos Funcionais

### RF01 - Verificacao de saude da API

A API deve disponibilizar um endpoint de verificacao de disponibilidade para confirmar que o servico esta ativo e apto a receber requisicoes.

### RF02 - Autenticacao de acesso a API

A API deve exigir autenticacao para acesso aos endpoints de negocio do MVP.

### RF03 - Integracao com Google Calendar

A API deve integrar-se ao Google Calendar por meio da API oficial do Google, utilizando credenciais validas e escopo minimo necessario para leitura e escrita de eventos.

### RF04 - Consulta de eventos

A API deve permitir a consulta de eventos de uma agenda Google configurada.

### RF05 - Filtro por periodo

A consulta de eventos deve aceitar, no minimo, os parametros de data e hora inicial e data e hora final para filtragem por periodo.

### RF06 - Criacao de evento

A API deve permitir a criacao de um novo evento em uma agenda Google configurada.

### RF07 - Dados minimos para criacao

A criacao de evento deve aceitar, no minimo, titulo, data e hora de inicio, data e hora de fim e identificacao da agenda de destino.

### RF08 - Validacao de dados de entrada

A API deve validar obrigatoriedade, formato e consistencia dos dados recebidos antes de acionar a integracao com o Google Calendar.

### RF09 - Retorno padronizado

A API deve retornar respostas em formato JSON, com estrutura padronizada para sucesso e erro.

### RF10 - Tratamento de falhas externas

A API deve tratar erros de autenticacao, autorizacao, indisponibilidade e rejeicao retornados pela API do Google Calendar, repassando mensagens tecnicas controladas ao cliente.

## Requisitos Nao Funcionais

### RNF01 - Arquitetura

O sistema deve ser implementado como micro-API HTTP stateless, sem dependencia de interface grafica propria.

### RNF02 - Simplicidade do MVP

O desenho da solucao deve priorizar baixo nivel de complexidade tecnica, com numero reduzido de endpoints e regras de negocio estritamente necessarias ao caso de uso principal.

### RNF03 - Seguranca

Credenciais, tokens e segredos de integracao nao devem ser armazenados em codigo-fonte nem expostos em logs ou respostas da API.

### RNF04 - Desempenho

Para operacoes sem falha externa, a API deve responder em tempo adequado ao uso interativo, considerando como referencia ate 2 segundos para consultas e criacoes simples, desconsiderando degradacao causada por servicos terceiros.

### RNF05 - Confiabilidade

Falhas de integracao com servicos externos devem ser tratadas de forma controlada, sem derrubar a aplicacao e sem retornar erros genericos sem contexto tecnico minimo.

### RNF06 - Observabilidade minima

O servico deve registrar logs tecnicos suficientes para diagnostico de erro e rastreamento basico de requisicoes, preservando dados sensiveis.

### RNF07 - Padronizacao de interface

Os endpoints devem seguir padrao consistente de nomenclatura, codigos HTTP e formato de resposta.

### RNF08 - Portabilidade de ambiente

O servico deve poder ser executado localmente para desenvolvimento e testes com configuracao baseada em variaveis de ambiente.

### RNF09 - Manutenibilidade

A implementacao deve ser organizada de forma a separar responsabilidades de roteamento, validacao, regras de negocio e acesso a servicos externos.

## Fora de Escopo

### FE01 - Interface web

Nao faz parte do MVP o desenvolvimento de frontend, painel administrativo ou interface grafica para uso final.

### FE02 - Sincronizacao bidirecional completa

Nao faz parte do MVP a sincronizacao continua entre sistemas internos e multiplas agendas com reconciliacao automatica de conflitos.

### FE03 - Edicao e exclusao de eventos

Nao faz parte do MVP a alteracao ou remocao de eventos ja cadastrados.

### FE04 - Suporte multiusuario amplo

Nao faz parte do MVP a gestao completa de contas, perfis, tenants ou multiplos usuarios com isolamento avancado.

### FE05 - Recorrencia avancada

Nao faz parte do MVP o suporte completo a eventos recorrentes, excecoes de recorrencia e regras complexas de repeticao.

### FE06 - Notificacoes

Nao faz parte do MVP o envio de e-mails, alertas, webhooks ou notificacoes push relacionadas aos eventos.

### FE07 - Persistencia propria de agenda

Nao faz parte do MVP a manutencao de banco de dados proprio para espelhamento integral dos eventos do Google Calendar.

### FE08 - Escalabilidade avancada

Nao faz parte do MVP a implementacao de mecanismos avancados de alta disponibilidade, filas, cache distribuido ou balanceamento para alta carga.
