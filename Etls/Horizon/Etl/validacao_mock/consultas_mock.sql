-- Resumo dos dados falsos carregados (usado por: make mock-resumo).
-- Também serve de exemplo de consultas para rodar dentro do make mock-psql.
\pset pager off
\pset null '(vazio)'

\echo
\echo '== Linhas por tabela =='
SELECT 'pessoas' AS tabela, count(*) AS linhas FROM pessoas
UNION ALL SELECT 'emails_pessoa', count(*) FROM emails_pessoa
UNION ALL SELECT 'perfis_lattes', count(*) FROM perfis_lattes
UNION ALL SELECT 'organizacoes', count(*) FROM organizacoes
UNION ALL SELECT 'equipes (grupos)', count(*) FROM equipes
UNION ALL SELECT 'membros_equipe', count(*) FROM membros_equipe
UNION ALL SELECT 'iniciativas', count(*) FROM iniciativas
UNION ALL SELECT 'participantes_iniciativa', count(*) FROM participantes_iniciativa
UNION ALL SELECT 'bolsas', count(*) FROM bolsas
UNION ALL SELECT 'bolsas_participante', count(*) FROM bolsas_participante
UNION ALL SELECT 'producoes', count(*) FROM producoes
UNION ALL SELECT 'formacoes_academicas', count(*) FROM formacoes_academicas
UNION ALL SELECT 'vinculos', count(*) FROM vinculos;

\echo '== Iniciativas por tipo e situação =='
SELECT t.nome AS tipo, i.situacao, count(*) AS qtd
FROM iniciativas i JOIN tipos_iniciativa t ON t.id = i.tipo_iniciativa_id
GROUP BY 1, 2 ORDER BY 1, 2;

\echo '== 10 projetos do SigPesq com coordenador e grupo =='
SELECT left(i.nome, 60) AS projeto, i.situacao, i.data_inicio, i.data_fim,
       p.nome AS coordenador, left(e.nome, 45) AS grupo
FROM iniciativas i
JOIN tipos_iniciativa t ON t.id = i.tipo_iniciativa_id AND t.nome = 'projeto_pesquisa'
LEFT JOIN participantes_iniciativa pi ON pi.iniciativa_id = i.id
     AND pi.papel_id = (SELECT id FROM papeis WHERE nome = 'coordenador' AND escopo = 'participacao')
LEFT JOIN pessoas p ON p.id = pi.pessoa_id
LEFT JOIN equipes_iniciativa ei ON ei.iniciativa_id = i.id
LEFT JOIN equipes e ON e.id = ei.equipe_id
ORDER BY i.id LIMIT 10;

\echo '== Bolsas (C3: Petrobras Mock e Vale Mock deveriam ser 1200,00 e 750,00) =='
SELECT b.nome AS programa, o.nome AS financiador, b.valor,
       (SELECT count(*) FROM bolsas_participante bp WHERE bp.bolsa_id = b.id) AS bolsistas
FROM bolsas b JOIN organizacoes o ON o.id = b.financiador_id ORDER BY 1, 2;

\echo '== C1: pessoas gravadas sem nome (deveria ser vazio) =='
SELECT p.id, (SELECT count(*) FROM participantes_iniciativa x WHERE x.pessoa_id = p.id) AS participacoes,
       (SELECT count(*) FROM membros_equipe m WHERE m.pessoa_id = p.id) AS grupos
FROM pessoas p WHERE trim(p.nome) = '';

\echo '== C2: projeto com parecer "Não aprovado" que entrou mesmo assim =='
SELECT id, left(nome, 70) AS nome, situacao FROM iniciativas
WHERE descricao LIKE 'Resumo fictício (parecer ''Não aprovado''%';

\echo '== C4: formação em que o coorientador virou orientador =='
SELECT d.nome AS dono, f.curso, f.titulo_tese, o.nome AS pessoa, ofo.papel
FROM orientadores_formacao ofo
JOIN formacoes_academicas f ON f.id = ofo.formacao_id
JOIN pessoas d ON d.id = f.pessoa_id
JOIN pessoas o ON o.id = ofo.pessoa_id
WHERE f.titulo_tese = 'Avaliação formativa';
