# Laboratorio DevOps com GenAI no GitHub Actions

Este laboratorio reproduz, em uma pasta isolada, o diagnostico assistido por IA descrito no projeto integrador. A API Lab Agenda e seus testes nao sao alterados pelo defeito intencional.

## Fluxo

1. O workflow `DevOps GenAI Lab CI` executa apenas o teste de demonstracao quando um PR altera `devops_lab/`, ou quando iniciado manualmente.
2. O teste falha intencionalmente porque `calculate_shipping` soma um `float` com uma taxa recebida como texto.
3. O log e salvo como artefato temporario, sem credenciais no job de testes.
4. O workflow `DevOps GenAI Lab Failure Analysis` roda depois de uma falha, baixa o artefato, consulta a API Gemini com o log e o diff do PR e publica um diagnostico como comentario. Ele nao modifica codigo nem aplica sugestoes.

O workflow de analise deve estar na branch padrao para usar seu codigo confiavel. Na primeira instalacao, depois de integrar os arquivos a essa branch, abra outro PR de demonstracao ou inicie `DevOps GenAI Lab CI` manualmente para exercitar o fluxo.

## Configuracao no GitHub

1. Em **Settings > Secrets and variables > Actions**, crie o secret `GEMINI_API_KEY` com sua chave do Gemini. O modelo configurado e `gemini-2.5-flash-lite`. Nao adicione a chave a arquivos, prompts, commits ou logs.
2. Em **Settings > Actions > General > Workflow permissions**, habilite a permissao necessaria para que o token do workflow possa comentar em pull requests. Os workflows declaram somente `pull-requests: write` no job de analise.
3. Envie as alteracoes para o GitHub. Abra um PR alterando a pasta `devops_lab/` ou execute manualmente `DevOps GenAI Lab CI` em **Actions**.
4. Confirme a falha esperada no job de teste e, depois, verifique o comentario do diagnostico no PR. Se executado manualmente sem PR associado, o resultado fica no resumo/log do job.

## Limites e seguranca

- O erro e proposital e fica restrito ao teste do laboratorio; nao e uma falha da API real.
- O job que executa os testes nao recebe `OPENAI_API_KEY` nem permissao de escrita.
- A analise envia para a API Gemini o log de teste e somente os trechos do diff em `devops_lab/`, com truncamento e redacao simples de valores que parecam segredos. Nao use dados reais ou confidenciais.
- Logs e diffs sao conteudo nao confiavel. A IA e instruida a nao executar instrucoes contidas neles.
- A resposta e uma sugestao para revisao humana; nenhuma correcao e aplicada automaticamente.
- O workflow de analise depende de artefato, permissao de comentario e secret valido. Falhas nessas dependencias nao significam que o teste tenha passado.

## Execucao local

```bash
python -m pip install pytest==8.3.5
python -m pytest -q devops_lab/tests/test_shipping_service.py
```

O teste deve falhar com `TypeError` devido ao defeito intencional. A correcao sugerida para o exercicio e converter/validar a taxa antes da soma; ela deve ser revisada e aplicada manualmente, seguida de nova execucao do teste.