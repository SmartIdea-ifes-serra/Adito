# Dicionário de Dados do Modelo Conceitual SigPesq

**Arquivo de Referência:** `ModeloSigpesqCopia.asta` (Diagrama de Classes UML `ModeloCompleto`)  
**Bases de Origem:** Planilhas Oficiais SigPesq exportadas via `agent_sigpesq`:
* `data/raw/sigpesq/research_group/Relatorio_16_10_2026.xlsx`
* `data/raw/sigpesq/research_projects/Relatorio_16_10_2026.xlsx`
* `data/raw/sigpesq/advisorships/*/Relatorio_16_10_2026.xlsx` (2015 a 2026)

---

## Sumário das Classes e Enums do Modelo

1. **Pessoas e Atores:** [`Pessoa`](#1-classe-pessoa), [`Pesquisador`](#2-classe-pesquisador), [`Estudante`](#3-classe-estudante)
2. **Atividades de Pesquisa:** [`ProjetoPesquisa`](#4-classe-projetopesquisa), [`GrupoPesquisa`](#5-classe-grupopesquisa), [`Orientacao`](#6-classe-orientacao), [`PlanoTrabalho`](#7-classe-planotrabalho)
3. **Organização Institucional e Acadêmica:** [`Campus`](#8-classe-campus), [`Curso`](#9-classe-curso), [`AreaConhecimento`](#10-classe-areaconhecimento), [`GrandeArea`](#11-classe-grandearea)
4. **Agentes Externos e Fomento:** [`ParceiroDemandante`](#12-classe-parceirodemandante), [`GrupoPesquisaExterno`](#13-classe-grupopesquisaexterno), [`AgenciaFinanciamento`](#14-classe-agenciafinanciamento), [`Edital`](#15-classe-edital)
5. **Tipos Enumerados (Enums):** [`SituacaoGrupo`](#16-enum-situacaogrupo), [`NaturezaProjeto`](#17-enum-naturezaprojeto), [`ParecerDiretoria`](#18-enum-parecerdiretoria), [`Modalidade`](#19-enum-modalidade), [`Gerenciamento`](#20-enum-gerenciamento), [`Programa`](#21-enum-programa)

---

## 1. Núcleo de Pessoas e Atores

### 1. Classe: `Pessoa`
Superclasse conceitual generalizada que representa qualquer indivíduo físico registrado no ecossistema de pesquisa do Ifes.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `research_group` (`Lideres`)<br>• `research_projects` (`Coordenador`, `Pesquisadores`, `Estudantes`)<br>• `advisorships` (`Orientador`, `Orientado`) | Nome civil completo da pessoa física. Chave fundamental para resolução de entidades e cruzamento com bases externas (Lattes/CNPq). | `"Marco Antonio De Souza Leite Cuadros"`, `"Felipe Da Silva Paiva"` |
| **`email`** | `String` | `0..*` | • `research_group` (`Lideres` - entre parênteses)<br>• `research_projects` (`EmailCoordenador`)<br>• `advisorships` (`OrientadorEmail`, `OrientadoEmail`) | Endereço de correio eletrônico de contato (pessoal ou institucional `@ifes.edu.br`). Uma pessoa pode ter múltiplos e-mails cadastrados. Na planilha de Projetos de Pesquisa, o e-mail só é informado para o Coordenador; para os demais pesquisadores e estudantes participantes, a planilha traz apenas seus nomes. | `"cuadros@ifes.edu.br"`, `"aluno@gmail.com"` |
| **`cpf`** | `String` | `0..1` | • `advisorships` (`OrientadoCpf`) | Cadastro de Pessoa Física (CPF) da Receita Federal. Na planilha de Orientações, o CPF do estudante orientado vem registrado na coluna `OrientadoCpf`. Já na planilha de Projetos de Pesquisa, não há coluna de CPF para nenhum participante. | `"14455054790"`, `"076693724"` |
| **`celular`** | `String` | `0..1` | • `advisorships` (`CelularOrientador`, `CelularOrientado`) | Número de telefone celular com DDD para contato. Vem preenchido na planilha de Orientações para o orientador e para o estudante. Na planilha de Projetos de Pesquisa, não há coluna de telefone. | `"27999881122"`, `"27981334455"` |

---

### 2. Classe: `Pesquisador`
Especialização de `Pessoa`. Representa o servidor docente, técnico-administrativo ou pesquisador externo com titulação acadêmica que atua na formulação, liderança e condução de pesquisas.

* **Herança:** Herda todos os atributos de `Pessoa` (`nome`, `email`, `cpf`, `celular`).
* **Papéis Desempenhados no Modelo:**
  * **Líder de Grupo de Pesquisa:** Conduz o grupo certificado no CNPq (`lidera` `GrupoPesquisa`).
  * **Coordenador de Projeto:** Responsável técnico-científico do projeto (`coordena` `ProjetoPesquisa`).
  * **Pesquisador de Equipe:** Membro colaborador da equipe (`participa` de `ProjetoPesquisa`).
  * **Orientador:** Tutor acadêmico de alunos em planos de IC/Pós (`orienta` `Orientacao`).
* **Relação com Campus:**
  * `pertence a` $\rightarrow$ `Campus [0..1]`: Reflete a lotação funcional do servidor (extraído da coluna `CampusOrientador` em `advisorships`).

---

### 3. Classe: `Estudante`
Especialização de `Pessoa`. Representa o discente em processo de formação acadêmica (ensino técnico, graduação ou pós-graduação).

* **Herança:** Herda todos os atributos de `Pessoa` (`nome`, `email`, `cpf`, `celular`).
* **Papéis Desempenhados no Modelo:**
  * **Membro Discente de Projeto:** Participa da equipe de um projeto (`participa` de `ProjetoPesquisa`).
  * **Orientado:** Executa o plano de trabalho tutelado por um orientador (`participa` como `orientado` em `Orientacao`).
* **Relação com Curso e Campus:**
  * `cursa` $\rightarrow$ `Curso [0..1]`: O curso em que o aluno está regularmente matriculado no Ifes.
  * `pertence a` $\rightarrow$ `Campus [0..1]`: O campus de oferta do curso onde o discente estuda.

---

## 2. Atividades e Estruturas de Pesquisa

### 4. Classe: `ProjetoPesquisa`
Entidade central que representa um Projeto de Pesquisa Institucional formalmente cadastrado, submetido e homologado no Ifes.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`id`** | `int` | `1` | • `research_projects` (`Id`)<br>• `advisorships` (`CodPJ`) | Número inteiro identificador único do projeto gerado pelo banco de dados do SIGPESq. Serve como chave primária de integração entre projetos e orientações. | `7140`, `7219`, `8448` |
| **`nome`** | `String` | `1` | • `research_projects` (`Titulo`)<br>• `advisorships` (`TituloPJ`) | Título completo e oficial da proposta de pesquisa aprovada. | `"Mina Digital de Rochas Ornamentais"`, `"Sistema de Aquisição de Dados"` |
| **`data_inicio`** | `Date` | `1` | • `research_projects` (`Inicio`) | Data formal de início da vigência do projeto aprovado. Formato de apresentação `dd-mm-yy` normalizado para ISO (`YYYY-MM-DD`). | `2022-08-01` (`01-08-22`) |
| **`data_fim`** | `Date` | `1` | • `research_projects` (`Fim`) | Data oficial prevista ou estendida para encerramento das atividades do projeto. Utilizada para determinar se o projeto está em andamento ou concluído. | `2026-12-31` (`31-12-26`) |
| **`linha_pesquisa`** | `String` | `0..1` | • `research_projects` (`LinhaPesquisa`) | Linha temática de investigação científica na qual o projeto se insere dentro do seu grupo de pesquisa. Pode ser nula quando o projeto não formaliza a linha no cadastro. | `"Engenharia de Software e Ciência de Dados"`, `"Energias Renováveis"` |
| **`palavras_chave`** | `String` | `0..1` | • `research_projects` (`PalavraChave`) | Termos descritores dos conceitos e tecnologias centrais investigados, separados por ponto e vírgula ou nova linha. | `"Inteligência Artificial; Visão Computacional; Indústria 4.0"` |
| **`natureza`** | `NaturezaProjeto` | `1` | • `research_projects` (`Natureza`) | Classificação quanto ao direcionamento prático da pesquisa: aplicada (voltada à solução prática de problemas industriais/sociais) ou básica (voltada ao avanço do conhecimento teórico). | `pesquisa_aplicada`, `pesquisa_basica` |
| **`sigilo`** | `boolean` | `1` | • `research_projects` (`Sigilo`) | Flag booleano que indica se o projeto envolve alguma confidencialidade | `false`, `true` |
| **`parecer_diretoria`** | `ParecerDiretoria` | `1` | • `research_projects` (`ParecerDiretoria`) | Estado conclusivo do trâmite administrativo do projeto perante a PRPPG/Diretoria de Pesquisa do Campus. | `aprovado`, `recusado`, `aprovacao_solicitada`, `salvo` |

---

### 5. Classe: `GrupoPesquisa`
Representa um Grupo de Pesquisa formalmente instituído, liderado por servidores do Ifes e certificado pela instituição junto ao Diretório dos Grupos de Pesquisa do CNPq (DGP).

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `research_group` (`Nome`)<br>• `research_projects` (`GrupoPesquisa`) | Nome por extenso oficial do grupo registrado e certificado no CNPq. Utilizado como chave nominal de relacionamento com os projetos. | `"Grupo de Automação Industrial - GAIn"`, `"Agro Data Science e Tecnologias"` |
| **`sigla`** | `String` | `0..1` | • `research_group` (`Sigla`) | Sigla ou acrônimo de identificação e divulgação acadêmica do grupo. Pode ser nula se o grupo não instituiu sigla. | `"GAIn"`, `"TCA"`, `"LEDS"` |
| **`situacao_grupo`** | `SituacaoGrupo` | `1` | • `research_group` (`ParecerDiretoria`) | Status da certificação institucional do grupo perante a pró-reitoria (PRPPG) e o espelho no CNPq. | `certificado`, `salvo`, `recusado`, `excluidoCNPQ` |
| **`url_cnpq`** | `String` | `1` | • `research_group` (`Column1`) | Endereço URL público permanente do espelho oficial do grupo no portal DGP/CNPq (`http://dgp.cnpq.br/dgp/espelhogrupo/<id_cnpq>`). | `"http://dgp.cnpq.br/dgp/espelhogrupo/4439471564090237"` |

---

### 6. Classe: `Orientacao`
Representa a concessão individual de bolsa ou a execução de voluntariado de pesquisa ligando formalmente um orientador a um estudante em um determinado ciclo anual.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`id`** | `int` | `1` | • `advisorships` (`Id`) | Identificador numérico exclusivo do registro de orientação no SIGPESq. | `5439`, `6254`, `7715`, `9442` |
| **`ano`** | `int` | `1` | • `advisorships` (`Ano`) | Ano do exercício de fomento ou do edital anual de referência da pesquisa. | `2016`, `2022`, `2024`, `2026` |
| **`gerenciamento`** | `Gerenciamento` | `1` | • `advisorships` (`Gerenciamento`) | Tipo de gestão administrativa: `reitoria` (editais centralizados da PRPPG) ou `independente` (fluxo contínuo descentralizado de campus). | `reitoria`, `independente` |
| **`modalidade`** | `Modalidade` | `1` | • `advisorships` (`Modalidade`) | Indica se o estudante recebe remuneração financeira (`bolsista`) ou se atua sem contraprestação pecuniária (`voluntario`). | `bolsista`, `voluntario` |
| **`programa`** | `Programa` | `0..1` | • `advisorships` (`Programa`) | Política de Iniciação Científica/Tecnológica ou Pós-Graduação que regulamenta a orientação. Pode ser nulo em projetos voluntários de fluxo contínuo. | `pibic`, `pibiti`, `pivic`, `pibic_jr`, `propos` |
| **`valor_bolsa`** | `float` | `0..1` | • `advisorships` (`Valor`) | Quantia monetária mensal (em BRL) repassada ao aluno bolsista. Para voluntários é nulo ou `0.0`. | `700.00`, `300.00`, `0.00` |
| **`data_inicio`** | `Date` | `1` | • `advisorships` (`Inicio`) | Data inicial de vigência da participação do discente no plano de trabalho. | `2022-09-01` (`01-09-22`) |
| **`data_fim`** | `Date` | `1` | • `advisorships` (`Fim`) | Data final da vigência do plano de trabalho ou da bolsa. | `2023-08-31` (`31-08-23`) |
| **`cancelado`** | `boolean` | `1` | • `advisorships` (`Cancelado`) | Flag que informa se a orientação foi interrompida antes da data final de vigência (por desistência, formatura ou desligamento). | `false`, `true` |
| **`nome_cancelador`** | `String` | `0..1` | • `advisorships` (`CanceladoPor` - extraído) | Nome da autoridade ou gestor que homologou o cancelamento precoce da bolsa/orientação no sistema. | `"Moisés Savedra Omena"`, `"Dirceu Soares Júnior"` |
| **`data_cancelado`** | `Date` | `0..1` | • `advisorships` (`CanceladoPor` - extraído) | Carimbo de data e hora em que a operação de cancelamento foi consumada no portal. | `2024-06-20 07:58:00` |
| **`relatorio_enviado`**| `boolean` | `1` | • `advisorships` (`AvaliacaoRelatorio`) | Indica se o estudante e orientador cumpriram o dever acadêmico de submeter o relatório técnico final de atividades no SIGPESq. | `true` (`"Enviado"`), `false` (`"Não Enviado"`) |

---

### 7. Classe: `PlanoTrabalho`
Representa a proposta metodológica específica de um estudante, subordinada ao projeto-mãe, detalhando as atividades que serão executadas pelo discente.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`codigo`** | `String` | `1` | • `advisorships` (`CodPT`) | Identificador único alfanumérico do Plano de Trabalho no sistema SIGPESq. Um plano pode ser continuado por outro aluno caso haja substituição. | `"PT2022-0012"`, `"8448-1"` |
| **`titulo`** | `String` | `1` | • `advisorships` (`TituloPT`) | Título descritivo específico da pesquisa individual do estudante. | `"Desenvolvimento de módulo IoT para sensoriamento"`, `"Análise computacional de imagens OCT"` |

---

## 3. Organização Institucional e Acadêmica

### 8. Classe: `Campus`
Representa uma unidade operacional/geográfica do Instituto Federal do Espírito Santo (Ifes).

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`name`** | `String` | `1` | • `research_group` (`Unidade`)<br>• `research_projects` (`CampusExecucao`)<br>• `advisorships` (`CampusExecucao`, `CampusOrientador`, `Campus`) | Nome oficial do Campus do Ifes. Pode atuar como sede de grupo, local físico de execução de projeto/orientação ou local de estudo do aluno. | `"Serra"`, `"Vitória"`, `"Vila Velha"`, `"Montanha"`, `"Colatina"` |

---

### 9. Classe: `Curso`
Representa um curso técnico, de graduação ou pós-graduação ofertado pelo Ifes no qual o estudante de Iniciação Científica está matriculado.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `advisorships` (`Curso`) | Denominação oficial da formação acadêmica do estudante. Pode vir ausente em alunos de escolas públicas externas atendidos pelo PIBIC-Jr. | `"Engenharia de Controle e Automação"`, `"Sistemas de Informação"`, `"Técnico em Informática"` |

---

### 10. Classe: `AreaConhecimento`
Classificação temática segundo a Árvore do Conhecimento oficial do CNPq (nível 2), organizando as competências de grupos, projetos e orientações.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `research_group` (`AreaConhecimento`)<br>• `research_projects` (`AreaConhecimento`)<br>• `advisorships` (`AreaConhecimento`) | Nome da área do conhecimento regulamentada pelo CNPq. | `"Ciência da Computação"`, `"Engenharia Elétrica"`, `"Engenharia Biomédica"`, `"Educação"` |

---

### 11. Classe: `GrandeArea`
Nível mais amplo e generalista da Árvore do Conhecimento do CNPq (nível 1), agrupando diversas áreas correlatas.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `advisorships` (`GradeArea` - *sic*) | Denominação da grande área no CNPq que engloba as subáreas de pesquisa. | `"Ciências Exatas e da Terra"`, `"Engenharias"`, `"Ciências Humanas"`, `"Multidisciplinar"` |

---

## 4. Agentes Externos, Parcerias e Fomento

### 12. Classe: `ParceiroDemandante`
Representa a pessoa jurídica externa (empresa privada, órgão público governamental ou fundação) que trouxe o desafio tecnológico/social ou que é a principal beneficiária da pesquisa.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `research_projects` (`ParceiroDemandante`) | Razão social ou nome institucional da entidade parceira que demandou o projeto. Presente em cerca de 37% dos projetos. | `"Vale S.A."`, `"ArcelorMittal"`, `"Coordenadoria Estadual de Proteção e Defesa Civil"`, `"CuboLife"` |

---

### 13. Classe: `GrupoPesquisaExterno`
Representa um laboratório, núcleo de inovação ou grupo de pesquisa vinculado a outra instituição de ensino/pesquisa nacional ou estrangeira que atua em regime de cooperação com o Ifes.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `research_projects` (`GrupoPesquisaExterno`) | Nome ou sigla do grupo/laboratório externo conveniado. Presente apenas quando o projeto é interinstitucional. | `"LABCISNE"`, `"LCAD"`, `"NEES – Núcleo de Excelência em Tecnologias Sociais (UFAL)"` |

---

### 14. Classe: `AgenciaFinanciamento`
Órgão governamental, fundação de amparo ou programa orçamentário responsável pelo aporte dos recursos financeiros destinados ao custeio de bolsas discentes.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`nome`** | `String` | `1` | • `advisorships` (`AgFinanciadora`) | Nome da agência pagadora da cota de bolsa. No caso de não-bolsistas, o SIGPESq registra o termo `"Voluntário"` ou deixa o campo nulo. | `"CNPq"`, `"Fapes"`, `"Ifes"`, `"Finep"`, `"Voluntário"` |

---

### 15. Classe: `Edital`
Instrumento convocatório público institucional sob o qual as propostas de planos de trabalho e pedidos de bolsa foram julgados, aprovados e selecionados.

| Atributo | Tipo UML | Multiplicidade | Planilha Fonte / Coluna Original | Significado Semântico e Regra de Negócio | Exemplos Reais |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **`titulo`** | `String` | `1` | • `advisorships` (`Edital`) | Identificação formal do número e ano do edital, frequentemente associado ao programa institucional correspondente. | `"05/2016 - Pibic"`, `"04/2022 - Pibic-Jr"`, `"03/2026 - Picti"`, `"10/2015 - Pibic-EM"` |

---

## 5. Tipos Enumerados (Domínios de Valores dos Enums)

### 16. Enum: `SituacaoGrupo`
Define o status formal do Grupo de Pesquisa junto à PRPPG e ao CNPq.
* **`salvo`:** Grupo em fase de elaboração ou rascunho no sistema interno.
* **`recusado`:** Proposta de criação do grupo rejeitada pela comissão/diretoria de pesquisa.
* **`certificado`:** Grupo aprovado pelo Ifes e homologado como ativo no Diretório do CNPq.
* **`excluidoCNPQ`:** Grupo desativado ou descredenciado da base nacional do CNPq por inatividade.

---

### 17. Enum: `NaturezaProjeto`
Classificação metodológica quanto à aplicabilidade dos resultados do projeto.
* **`pesquisa_aplicada`:** Objetiva gerar conhecimentos e protótipos para aplicação prática imediata em produtos, processos ou demandas da sociedade e da indústria.
* **`pesquisa_basica`:** Objetiva a geração de novos conhecimentos e teorias sem aplicação prática imediata predeterminada.

---

### 18. Enum: `ParecerDiretoria`
Situação do ciclo de avaliação institucional do Projeto de Pesquisa.
* **`aprovado`:** Projeto avaliado no mérito e autorizado para execução no campus.
* **`recusado`:** Proposta que não atendeu aos critérios dos editais ou diretrizes de pesquisa.
* **`aprovacao_solicitada`:** Projeto submetido pelo coordenador que aguarda deliberação da comissão.
* **`salvo`:** Proposta em preenchimento pelo proponente, não submetida à avaliação final.

---

### 19. Enum: `Modalidade`
Tipo de vínculo financeiro do discente na orientação.
* **`bolsista`:** O aluno recebe estipêndio financeiro mensal.
* **`voluntario`:** O aluno atua no projeto cumprindo as mesmas exigências acadêmicas, sem remuneração.

---

### 20. Enum: `Gerenciamento`
Instância de governança e controle do fluxo da orientação.
* **`reitoria`:** Orientações oriundas de editais institucionais geridos de forma unificada pela PRPPG.
* **`independente`:** Orientações cadastradas em fluxo contínuo ou descentralizado no campus, sem edital da reitoria.

---

### 21. Enum: `Programa`
Linha institucional de Iniciação Científica, Tecnológica ou Formação Acadêmica.
* **`pibic`:** Programa Institucional de Bolsas de Iniciação Científica (graduação).
* **`pibiti`:** Programa Institucional de Iniciação em Desenvolvimento Tecnológico e Inovação (graduação tecnológica/patentes).
* **`pivic`:** Programa Institucional de Voluntariado em Iniciação Científica (graduação voluntária).
* **`piviti`:** Programa Institucional de Voluntariado em Desenvolvimento Tecnológico e Inovação.
* **`pibic_jr`:** Programa de Iniciação Científica Júnior para o Ensino Médio/Técnico.
* **`pibic_af`:** Iniciação Científica com reserva de vagas para Ações Afirmativas.
* **`pibic_em`:** Iniciação Científica voltada a escolas parceiras do Ensino Médio.
* **`finep`:** Pesquisas custeadas por chamadas de desenvolvimento da FINEP.
* **`propos`:** Programa de apoio e formação voltado à Pós-Graduação (mestrado/doutorado).
* **`jtc`:** Programa Jovens Talentos para a Ciência.

