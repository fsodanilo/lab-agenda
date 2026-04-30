# Backlog do MVP

## Release 1 - Core

- [ ] RF-01 - Disponibilizar endpoint de saude da API
  - Criterios de aceite:
  - Existe endpoint HTTP de verificacao de saude.
  - O endpoint responde com status `200` quando a API estiver operacional.
  - A resposta retorna payload JSON simples indicando disponibilidade do servico.

- [ ] RF-02 - Proteger endpoints de negocio com autenticacao
  - Criterios de aceite:
  - Endpoints de consulta e criacao de eventos exigem credencial de acesso.
  - Requisicoes sem credencial valida retornam `401` ou `403`.
  - O endpoint de saude permanece acessivel sem autenticacao.

- [ ] RT-01 - Configurar base da micro-API e variaveis de ambiente
  - Criterios de aceite:
  - O projeto inicia localmente por comando documentado.
  - Credenciais e configuracoes sensiveis sao lidas por variaveis de ambiente.
  - Nenhum segredo fica fixo no codigo-fonte versionado.

- [ ] RF-03 - Integrar a API ao Google Calendar
  - Criterios de aceite:
  - A API autentica com a API oficial do Google Calendar.
  - A integracao utiliza permissao minima para leitura e escrita de eventos.
  - Falha de autenticacao externa gera resposta controlada pela API.

- [ ] RF-04 - Consultar eventos por periodo
  - Criterios de aceite:
  - Existe endpoint para listar eventos de uma agenda configurada.
  - A consulta aceita data e hora inicial e final como filtro.
  - A resposta retorna lista JSON com os eventos encontrados no periodo informado.

- [ ] RF-05 - Criar evento na agenda Google
  - Criterios de aceite:
  - Existe endpoint para criar evento em agenda configurada.
  - O endpoint aceita, no minimo, titulo, data/hora de inicio, data/hora de fim e identificacao da agenda.
  - Em caso de sucesso, a API retorna status de criacao e os dados essenciais do evento criado.

## Release 2 - Qualidade

- [ ] RF-06 - Validar dados obrigatorios e consistencia de entrada
  - Criterios de aceite:
  - Campos obrigatorios ausentes retornam erro `400`.
  - Datas e horas em formato invalido retornam erro `400`.
  - Eventos com inicio posterior ao fim sao rejeitados com mensagem objetiva.

- [ ] RF-07 - Padronizar respostas de sucesso e erro
  - Criterios de aceite:
  - Todos os endpoints retornam JSON.
  - Respostas de erro seguem estrutura consistente entre os endpoints.
  - Codigos HTTP estao coerentes com o resultado de cada operacao.

- [ ] RF-08 - Tratar falhas de integracao com o Google Calendar
  - Criterios de aceite:
  - Erros de autenticacao, autorizacao e indisponibilidade externa sao tratados sem derrubar a API.
  - A resposta de erro nao expone tokens, segredos ou stack trace.
  - O cliente recebe mensagem tecnica controlada e codigo HTTP coerente.

- [ ] RT-02 - Implementar logs tecnicos minimos
  - Criterios de aceite:
  - A API registra inicio e resultado das requisicoes principais.
  - Erros de integracao externa sao registrados para diagnostico.
  - Logs nao armazenam credenciais, tokens ou dados sensiveis indevidos.

- [ ] RT-03 - Criar testes automatizados do fluxo principal
  - Criterios de aceite:
  - Existem testes automatizados para endpoint de saude.
  - Existem testes automatizados para consulta de eventos.
  - Existem testes automatizados para criacao de eventos e validacoes basicas.

- [ ] RT-04 - Documentar execucao local e configuracao
  - Criterios de aceite:
  - A documentacao descreve pre-requisitos do projeto.
  - A documentacao descreve variaveis de ambiente necessarias.
  - A documentacao descreve como executar a API e como rodar os testes.

## Release 3 - Entrega Final

- [ ] RT-05 - Preparar pacote final de entrega
  - Criterios de aceite:
  - O repositorio contem estrutura final organizada para avaliacao.
  - O projeto pode ser executado a partir das instrucoes documentadas sem ajustes manuais fora do previsto.
  - Arquivos temporarios, segredos e artefatos locais nao fazem parte da entrega.

- [ ] RT-06 - Publicar documentacao final da API
  - Criterios de aceite:
  - A documentacao lista endpoints, metodos, autenticacao, parametros e exemplos de resposta.
  - A documentacao diferencia claramente consulta de eventos e criacao de eventos.
  - A documentacao esta consistente com o comportamento implementado.

- [ ] RT-07 - Executar validacao final do MVP
  - Criterios de aceite:
  - O fluxo de consultar eventos funciona em ambiente de entrega.
  - O fluxo de criar evento funciona em ambiente de entrega.
  - Os testes definidos para o MVP executam sem falha no estado final da release.

- [ ] RT-08 - Consolidar checklist de entrega
  - Criterios de aceite:
  - Existe checklist final de validacao tecnica e funcional.
  - O checklist confirma configuracao, execucao, testes e documentacao.
  - O checklist pode ser reutilizado para apresentacao ou avaliacao final.
