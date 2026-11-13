# Demonstração do Adito com dados fictícios

Todos os registros são sintéticos. Informe na resposta que os números pertencem
à demonstração. Campus e áreas situam o cenário de teste. Os pesquisadores,
iniciativas, grupos, produções e seus indicadores foram inventados.

## Iniciativas

Cada linha de demo_fato_iniciativa representa uma iniciativa. A coluna tipo
separa Pesquisa e Extensão. Para perguntas sobre projetos de pesquisa, filtre
tipo = 'Pesquisa'. Para ações e atividades de extensão, filtre tipo = 'Extensão'.
O ano é o ano de início da iniciativa. Status pode ser Concluído, Em andamento
ou Planejado. Considere Em andamento como projeto ativo.

Orçamento é o valor previsto em reais, sem indicar execução financeira.
Carga horária é medida em horas por iniciativa. Participantes e certificados
representam participações por ação de extensão, podendo contar uma pessoa em
mais de uma ação. Some essas medidas somente para Extensão.
Certificados registra participações certificadas em ações concluídas.

## Produção e pesquisadores

Cada linha de demo_fato_producao representa uma produção, identificada por
producao_id e atribuída a um único pesquisador responsável na demonstração.
Os tipos são Artigo, Trabalho em evento, Livro, Capítulo e Patente.
O ano da produção coincide com o ano da iniciativa associada nesta amostra.

Use demo_dim_pesquisador para contar pesquisadores por titulação, consultar
orientacoes_concluidas e orientacoes_em_andamento e filtrar
bolsa_produtividade = 'Sim'. As orientações são totais por pesquisador,
sem desagregação temporal.

## Grupos e junções

Use demo_dim_grupo para situação Certificado, ano_formacao, linhas_pesquisa e
membros_ativos. Linhas de pesquisa e membros ativos são quantidades por grupo.
Os pesquisadores e coordenadores possuem nomes fictícios numerados.

As views de fatos já incluem os nomes das dimensões. Para junções adicionais,
use area_id, campus_id, pesquisador_id, coordenador_id, grupo_id, iniciativa_id
e ano conforme as colunas disponíveis. Evite multiplicar linhas ao juntar
diretamente os dois fatos. Para combinar medidas, agregue cada fato antes.
