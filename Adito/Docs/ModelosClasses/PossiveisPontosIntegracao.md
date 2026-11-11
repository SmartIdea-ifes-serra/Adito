# Proposta de ligações entre as fontes

**SigPesq · Lattes · CNPq DGP · SRC**: o que une as quatro bases e por onde o ETL pode cruzá-las.

Classes e atributos citados conforme os modelos Astah: SigPesq `ModeloSigpesqCopia` · Lattes `lattes_v3` · CNPq `cnpq_dgp_v3` · SRC `ModeloClassesSRC1`.

## Mapa das ligações

**Roteiro:**

| # | Ligação | Cruza por | Resultado |
|:-:|---|---|---|
| ① | SigPesq ↔ CNPq | `GrupoPesquisa.url_cnpq` = `GRUPO_PESQUISA.link_espelho_dgp` | **331 de 347** grupos, chave exata |
| ② | 4 fontes → Pessoa | `PESSOA.id_lattes` → `cpf` → `email` → `nome` + contexto | **65 de 71** coordenadores do SRC achados na pesquisa |
| ③ | SigPesq ↔ Lattes | `PlanoTrabalho.titulo` + `orientador` ↔ `ORIENTACAO.titulo` + dono do CV | **30%** dos planos; orientador igual em 98% |
| ④ | SRC ↔ Lattes | `Acao.titulo` ↔ `PROJETO.nome` | só **10%** das ações: ligar, não fundir |
| ⑤ | SigPesq ↔ SRC | `Orientado.cpf` e `Pessoa.email` ↔ `Pessoa.cpf` e `Pessoa.email` (hash) | chave forte, depende da credencial do SRC |

## Classes que unem as bases

| Classe | SigPesq | Lattes | CNPq | SRC | Junta por | |
|---|---|---|---|---|---|:-:|
| Grupo de pesquisa | `GrupoPesquisa` | ➖ | `GRUPO_PESQUISA` | ➖ | URL do espelho | 🟢 |
| Organização | `Campus`<br>`organização`<br>`AgenciaFinanciamento`<br>`ParceiroDemandante` | `INSTITUICAO_FINANCIADORA`<br>`ATUACAO_PROFISSIONAL` | `INSTITUICAO_PARCEIRA`<br>`GRUPO_PESQUISA.unidade_campus` | `Campus`<br>`Fomento` | tabela de campi (IFES → campus) | 🟢 |
| Área do conhecimento | `GrandeArea`<br>`AreaConhecimento` | `AREA_ATUACAO`<br>`GrandeAreaCNPq` | `GrandeAreaCNPq`<br>`GRUPO_PESQUISA.area_predominante` | ⚠️ `AreaTematicaPrincipal` | tabela de áreas do CNPq | 🟢 |
| Pessoa | `Pessoa`<br>`Pesquisador`<br>`Estudante`<br>`Orientado` | `PESSOA` | `PESSOA` | `Pessoa` | CPF/e-mail em hash ou nome | 🟡 |
| Orientação | `Orientacao`<br>`PlanoTrabalho` | `ORIENTACAO` | ➖ | ➖ | título + orientador | 🟡 |
| Participação com papel | associações `coordena`, `participa`, `orienta`, `lidera` | `MEMBRO_PROJETO` | `MEMBRO_GRUPO` | `MembroEquipeExecucao`<br>`RegistroParticipante` | pessoa já casada | 🟡 |
| Vínculo institucional | herança `Pesquisador` × `Estudante` | `ATUACAO_PROFISSIONAL.vinculo` | `MEMBRO_GRUPO.papel` | `Vinculo` | reforça o casamento de pessoas | 🟡 |
| Fomento | `AgenciaFinanciamento`<br>`Bolsa`<br>`Programa` | `INSTITUICAO_FINANCIADORA`<br>`FOMENTO_PROJETO` | ➖ | `Fomento` | de/para órgão × programa | 🟡 |
| Iniciativa | `ProjetoPesquisa` | `PROJETO` | ➖ | `Acao` | título + coordenador | 🔴 |
| Linha de pesquisa | `ProjetoPesquisa.linha_pesquisa` | `LINHA_PESQUISA` | `LINHA_PESQUISA` | ➖ | texto | 🔴 |
| Curso | `Curso` | `ORIENTACAO.curso`<br>`FORMACAO_ACADEMICA.curso` | ➖ | ➖ | texto | 🔴 |

`Classe` = classe no modelo da fonte · `Classe.atributo` = atributo dessa classe · ➖ não tem · ⚠️ só a área temática; a grande área está no portal, mas falta no modelo · 🟢 funde com segurança · 🟡 funde com regra · 🔴 só liga ou enriquece
