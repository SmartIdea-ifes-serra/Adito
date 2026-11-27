<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./Adito/app/frontend-vue/public/brand/adito-dark.png">
    <img src="./Adito/app/frontend-vue/public/brand/adito-light.png" alt="Logo oficial do Adito" width="100">
  </picture>
  <h3>Adito</h3>
  <p><strong>Assistente de pesquisa e extensão do IFES</strong></p>
  <p>Dados acadêmicos em um só lugar. Respostas em linguagem natural.</p>
  <p>
    <a href="https://github.com/SmartIdea-ifes-serra/Adito/releases/latest"><img alt="Baixar Adito" src="https://img.shields.io/badge/Baixar_Adito-246B45?style=for-the-badge&amp;logo=github&amp;logoColor=white"></a>
  </p>
</div>

---

### Sobre o Adito

> **Adito** — do grego *ádyton*, o recinto interno onde o oráculo falava.

O Adito é um aplicativo desktop com inteligência artificial que reúne informações de pesquisa e extensão do **IFES Campus Serra**. Seu objetivo é tornar os dados acadêmicos mais acessíveis, permitindo que qualquer pessoa com acesso à base institucional consulte informações sem precisar conhecer SQL ou navegar por diferentes sistemas.

<table>
  <tr>
    <td width="33%" align="center"><strong>01 · Consulte</strong><br><sub>Faça perguntas em português.</sub></td>
    <td width="33%" align="center"><strong>02 · Visualize</strong><br><sub>Explore respostas, tabelas e gráficos.</sub></td>
    <td width="33%" align="center"><strong>03 · Organize</strong><br><sub>Reúna resultados no seu painel.</sub></td>
  </tr>
</table>

### Funcionalidades

<table>
  <tr>
    <td width="50%" valign="top">
      <strong>Chat com IA</strong><br><br>
      Faça perguntas em linguagem natural e receba respostas baseadas nos dados acadêmicos, com tabelas e gráficos quando apropriado.
    </td>
    <td width="50%" valign="top">
      <strong>Meu painel</strong> · Personalizado<br><br>
      Salve resultados do chat, como gráficos, tabelas e indicadores, e organize ou redimensione os cartões conforme suas necessidades.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <strong>Histórico de conversas</strong><br><br>
      Retome consultas anteriores e acompanhe suas análises a partir das conversas armazenadas localmente.
    </td>
    <td valign="top">
      <strong>Dashboard geral</strong> · Indicadores acadêmicos<br><br>
      Visualize um panorama da pesquisa com gráficos e indicadores predefinidos, como número de projetos, orientadores e investimento estimado. O painel está implementado no código, mas não aparece no menu lateral da versão atual.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <strong>Exploração de dados</strong><br><br>
      Consulte informações acadêmicas e explore os resultados disponíveis por meio de tabelas e filtros.
    </td>
    <td valign="top">
      <strong>Atualizações</strong><br><br>
      Receba avisos sobre novas versões do aplicativo e da base acadêmica, sem precisar acompanhar as releases manualmente.
    </td>
  </tr>
</table>


### Download e instalação

**[Acessar a versão mais recente do Adito](https://github.com/SmartIdea-ifes-serra/Adito/releases/latest)**

Na página da release, localize a seção **Assets** e baixe o arquivo correspondente ao seu sistema operacional.

| Sistema operacional | Arquivo | Instalação |
| :--- | :--- | :--- |
| Windows (64 bits) | `*-setup.exe` | Instalador recomendado para uso pessoal. |
| Windows (64 bits) | `*.msi` | Instalador alternativo. |
| Linux (64 bits) | `*.AppImage` | Executável que não exige instalação convencional. |
| Debian / Ubuntu (64 bits) | `*.deb` | Pacote para instalação no sistema. |

Não é necessário instalar Python, Node.js ou Rust para utilizar o aplicativo distribuído nas releases. Os arquivos `.sig`, `latest.json` e os pacotes **Source code** não são instaladores.

#### Windows

1. Baixe o arquivo `*-setup.exe`.
2. Abra o instalador e siga as instruções exibidas.
3. Ao finalizar, abra o Adito pelo menu Iniciar.

#### Linux

**AppImage:** baixe o arquivo `.AppImage`, abra suas propriedades, permita a execução como programa e execute-o.

**DEB:** em distribuições compatíveis, como Ubuntu e Debian, abra o arquivo `.deb` com o instalador de pacotes do sistema. Também é possível instalá-lo pelo terminal, por exemplo (ajuste a versão para o nome do arquivo baixado):

```bash
sudo apt install ./Adito_0.1.1_amd64.deb
```

> Atualmente, os instaladores publicados são destinados a Windows e Linux de 64 bits. Não há instalador oficial para macOS na release disponível.

#### Primeiro acesso

1. Abra o Adito e informe a **chave institucional dos dados** fornecida pela equipe responsável. Selecione **Baixar os dados** e aguarde a conclusão.
2. Para utilizar o chat, abra **Configurações** e configure o provedor de IA disponível na sua versão.
3. Acesse o chat ou explore os dados disponíveis no aplicativo.

> [!IMPORTANT]
> A chave institucional da base de dados e a chave de API da IA são diferentes. O instalador é público, mas a base acadêmica é distribuída separadamente e protegida por criptografia. Solicite a chave dos dados à equipe responsável por um canal autorizado.

#### Atualizações

O aplicativo verifica novas versões do programa e da base de dados. Quando houver uma atualização disponível, um aviso será exibido na barra lateral. Na versão `v0.1.1`, usuários dos pacotes `.deb` e `.msi` devem atualizar o aplicativo manualmente pela página de releases.

### Fontes de dados

Os dados vêm dos pipelines, painéis e agentes do [**ifesserra-lab**](https://github.com/ifesserra-lab).

[**Site → ifesserra-lab.github.io**](https://ifesserra-lab.github.io/) &nbsp;·&nbsp; [**Painel de Extensão →**](https://ifesserra-lab.github.io/src/) &nbsp;·&nbsp; [**Pesquisa STEM →**](https://ifesserra-lab.github.io/pesquisa-stem.html)

#### Fontes originais dos dados

O Adito integra informações de quatro fontes acadêmicas por meio de um processo de extração, transformação e carga de dados (ETL).

| Fonte | Informações disponíveis na base |
| :--- | :--- |
| [SRC — Consulta de ações de extensão](https://src.ifes.edu.br/src/public/consulta-acao.xhtml) | Ações de extensão, atividades e registros de participação. |
| [SigPesq](https://sigpesq.ifes.edu.br/) | Projetos de pesquisa, grupos, orientações e registros relacionados a bolsas. |
| [Plataforma Lattes](https://lattes.cnpq.br/) | Informações acadêmicas selecionadas e produção científica. |
| [CNPq — Diretório dos Grupos de Pesquisa (DGP)](https://lattes.cnpq.br/web/dgp) | Grupos de pesquisa, membros e vínculos registrados. |

O ETL também realiza cruzamentos entre as fontes para relacionar registros acadêmicos e apoiar análises integradas. As consultas analíticas utilizam seis visões de dados no SQLite, dedicadas a ações e participações em extensão, projetos de pesquisa, orientações e bolsas, produção científica e grupos de pesquisa.

### Tecnologias utilizadas

<p align="center">
  <a href="https://vuejs.org/"><img alt="Vue.js" src="https://img.shields.io/badge/Vue.js-35495E?style=flat-square&amp;logo=vuedotjs&amp;logoColor=4FC08D"></a>
  <a href="https://www.typescriptlang.org/"><img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&amp;logo=typescript&amp;logoColor=white"></a>
  <a href="https://tauri.app/"><img alt="Tauri" src="https://img.shields.io/badge/Tauri-24C8DB?style=flat-square&amp;logo=tauri&amp;logoColor=black"></a>
  <a href="https://www.rust-lang.org/"><img alt="Rust" src="https://img.shields.io/badge/Rust-333333?style=flat-square&amp;logo=rust&amp;logoColor=white"></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white"></a>
  <a href="https://www.sqlite.org/"><img alt="SQLite" src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&amp;logo=sqlite&amp;logoColor=white"></a>
</p>

| Camada | Tecnologias |
| :--- | :--- |
| Interface | [Vue 3](https://vuejs.org/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vite.dev/) e [Tailwind CSS](https://tailwindcss.com/) |
| Aplicação desktop | [Tauri](https://tauri.app/) e [Rust](https://www.rust-lang.org/) |
| Núcleo de IA | [Python](https://www.python.org/) e [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) |
| Dados e ETL | [Python](https://www.python.org/) e [SQLite](https://www.sqlite.org/) |
| Testes | [Pytest](https://docs.pytest.org/), [unittest](https://docs.python.org/3/library/unittest.html), [Vitest](https://vitest.dev/) e [Playwright](https://playwright.dev/) |
| Distribuição e automação | [PyInstaller](https://pyinstaller.org/), [Make](https://www.gnu.org/software/make/) e [GitHub Actions](https://docs.github.com/actions) |

### Arquitetura

O Adito integra as fontes acadêmicas em uma base SQLite e utiliza um núcleo Python para interpretar as consultas e apresentar os resultados na interface desktop.

```text
Usuário
   ↕
Interface Vue / TypeScript
   ↕
Tauri / Rust
   ↕  STDIO
Núcleo Python / LangGraph
   ├──→ dados.db (somente leitura)
   ├──↔ app.db (dados da aplicação)
   └──↔ Provedor de IA

SRC · SigPesq · Lattes · CNPq/DGP
                ↓
            ETL Python
                ↓
             dados.db
```

A interface desktop se comunica com o núcleo Python por STDIO (entrada e saída padrão), sem depender de um servidor HTTP local. O aplicativo utiliza dois bancos SQLite:

- `dados.db`: base acadêmica utilizada pelo núcleo em modo somente leitura.
- `app.db`: informações locais da aplicação, como histórico, dashboards e configurações de conhecimento.

### Testes

```bash
make test
```

Outras verificações disponíveis:

| Comando | Finalidade |
| :--- | :--- |
| `make test-front` | Testes unitários do frontend. |
| `make test-e2e` | Testes de interface com Playwright e IPC simulado. |
| `make test-e2e-live` | Testes de integração com o núcleo Python e a base local. |
| `make test-tauri` | Testes da camada Rust/Tauri. |
| `make test-perf` | Avaliação de desempenho do núcleo local. |
| `make test-eval` | Avaliação de acurácia das respostas da IA. |

Os testes E2E exigem o Chromium do Playwright. A avaliação de acurácia com LLM Judge requer configuração da API do Gemini. Consulte `make help` e a documentação técnica para opções e requisitos adicionais.

### Documentação

| Documento | Descrição |
| :--- | :--- |
| [Aplicação desktop](Adito/app/README.md) | Ambiente, execução e estrutura do aplicativo. |
| [ETL](Adito/etl/README.md) | Extração e integração das fontes acadêmicas. |
| [Distribuição e atualizações](Adito/docs/DISTRIBUICAO.md) | Empacotamento, instaladores e distribuição da base. |
| [Documentação técnica](Adito/docs/) | Requisitos, especificações e decisões do projeto. |
| [Arquitetura local](Adito/docs/NUCLEO_LOCAL_SEM_HTTP.md) | Comunicação entre o desktop e o núcleo Python. |
| [Decisões arquiteturais (ADRs)](Docs/ADR/) | Registro das decisões de arquitetura. |
| [Modelos de classes](Docs/ModelosClasses/) | Modelagem das informações acadêmicas. |
| [Identidade visual](Adito/docs/design/Identidade-visual-Adito.md) | Diretrizes visuais da aplicação. |

<div align="center">
  <p>Desenvolvido no <strong>IFES — Campus Serra</strong>.</p>
  <a href="https://serra.ifes.edu.br/">IFES Campus Serra</a> · <a href="https://github.com/SmartIdea-ifes-serra">SmartIdea</a> · <a href="https://github.com/ifesserra-lab">IFES Serra Lab</a>
</div>
