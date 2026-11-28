import sqlite3
import subprocess
import sys
from pathlib import Path
import pytest


def test_popular_banco_sqlite_execution(tmp_path):
    """Valida execução autocontida do popular_banco.py gerando e validando dados.db temporário."""
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "popular_banco.py"
    etl_dir = repo_root / "etl"
    temp_db = tmp_path / "teste_dados.db"

    if not (etl_dir / "brutos").exists() or not (etl_dir / "trabalho" / "pessoas.json").exists():
        pytest.skip("ainda não há brutos/pessoas.json nesta máquina")

    cmd = [
        sys.executable,
        str(script_path),
        "--etl", str(etl_dir),
        "--banco", str(temp_db)
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Falha ao executar popular_banco.py:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"

    assert temp_db.exists(), "Arquivo dados.db temporário não foi gerado!"
    assert temp_db.stat().st_size > 1024 * 1024, "Banco dados.db gerado está com tamanho inesperadamente reduzido (< 1 MB)!"

    # Inspeciona banco gerado via sqlite3 read-only
    conn = sqlite3.connect(f"file:{temp_db}?mode=ro", uri=True)

    # 1. Integridade de chaves estrangeiras
    fk_errors = list(conn.execute("PRAGMA foreign_key_check;"))
    assert len(fk_errors) == 0, f"Erros de Foreign Key: {fk_errors}"

    # 1b. Contrato de tabelas da ADR-0003 revisada: 82 tabelas 3FN, sem tabelas PII vazias
    tables = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
    ]
    assert len(tables) == 82, f"Esperadas 82 tabelas 3FN (ADR-0003), encontradas {len(tables)}"
    for pii_table in ("email", "fax", "telefone"):
        assert pii_table not in tables, f"Tabela PII '{pii_table}' não deve existir em dados.db"

    # 2. As 6 views analíticas dinâmicas
    views = [
        "vfact_extensao_acao_resolved",
        "vfact_extensao_participacao_resolved",
        "vfact_grupo_pesquisa_membro_resolved",
        "vfact_orientacao_bolsa_resolved",
        "vfact_producao_cientifica_resolved",
        "vfact_projeto_pesquisa_resolved"
    ]
    for v in views:
        qtd = conn.execute(f"SELECT COUNT(*) FROM {v};").fetchone()[0]
        assert qtd > 0, f"View {v} está vazia!"

    # 3. Validações de sanidade de regras P1 a P12
    # P1: Nenhuma ocorrência de FAPES ou UFES na coluna campus de produção científica
    fapes_ufes = conn.execute(
        "SELECT COUNT(*) FROM vfact_producao_cientifica_resolved WHERE campus IN ('FAPES', 'UFES');"
    ).fetchone()[0]
    assert fapes_ufes == 0, f"P1 violado: {fapes_ufes} registros com campus FAPES/UFES"

    # Flag líder > 0
    lideres = conn.execute("SELECT SUM(flag_lider) FROM vfact_grupo_pesquisa_membro_resolved;").fetchone()[0]
    assert lideres > 0, "Nenhum líder identificado nas lideranças de grupo CNPq"

    # Tempo de participação dias >= 0 ou nulo
    neg_dias = conn.execute(
        "SELECT COUNT(*) FROM vfact_grupo_pesquisa_membro_resolved WHERE tempo_participacao_dias < 0;"
    ).fetchone()[0]
    assert neg_dias == 0, f"P3 violado: {neg_dias} registros com dias negativos"

    # Obra única
    row_prod = conn.execute(
        "SELECT SUM(flag_obra_unica), COUNT(DISTINCT id_producao) FROM vfact_producao_cientifica_resolved;"
    ).fetchone()
    assert row_prod[0] == row_prod[1], f"P4 violado: flag_obra_unica ({row_prod[0]}) != distinct id_producao ({row_prod[1]})"

    # Unicidade de orientacao por id_origem
    dup_orient = conn.execute(
        "SELECT COUNT(*) FROM (SELECT id_origem FROM orientacao WHERE id_origem IS NOT NULL GROUP BY id_origem HAVING COUNT(*) > 1);"
    ).fetchone()[0]
    assert dup_orient == 0, f"orientacao possui {dup_orient} id_origem duplicado(s)"

    conn.close()


def test_deduplicacao_orientacao_por_id_origem_preserva_estado_mais_recente(tmp_path):
    """Mesma orientação em dois arquivos anuais deve virar 1 registro com o estado mais recente."""
    import importlib.util
    import json

    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "popular_banco.py"
    spec = importlib.util.spec_from_file_location("popular_banco_mod", script_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)

    etl_dir = tmp_path / "etl"
    (etl_dir / "brutos" / "sigpesq" / "orientacoes").mkdir(parents=True)
    (etl_dir / "trabalho").mkdir(parents=True)

    pessoas = [
        {
            "nome": "Thiago Meireles Paixão",
            "nome_normalizado": "thiago meireles paixao",
            "variantes": [],
            "fontes": {"sigpesq": [{"id_fonte": None}]},
        },
        {
            "nome": "Gabriela Prajo Beretta",
            "nome_normalizado": "gabriela prajo beretta",
            "variantes": [],
            "fontes": {"sigpesq": [{"id_fonte": None}]},
        },
        {
            "nome": "Aluno Exemplo Segundo",
            "nome_normalizado": "aluno exemplo segundo",
            "variantes": [],
            "fontes": {"sigpesq": [{"id_fonte": None}]},
        },
    ]
    (etl_dir / "trabalho" / "pessoas.json").write_text(json.dumps(pessoas, ensure_ascii=False), encoding="utf-8")

    linha_base = {
        "Id": 9636,
        "Ano": 2025,
        "Gerenciamento": "Reitoria",
        "Modalidade": "Bolsista",
        "Programa": "Pibic",
        "Valor": "900,00",
        "Inicio": "01-09-25",
        "Fim": "31-08-26",
        "AgFinanciadora": "Fapes",
        "Cancelado": False,
        "CanceladoPor": None,
        "AvaliacaoRelatorio": "Não enviado",
        "CampusExecucao": "Serra",
        "Orientador": "Thiago Meireles Paixão",
        "CampusOrientador": "Serra",
        "Orientado": "Gabriela Prajo Beretta",
        "Curso": "Sistemas de Informação",
        "Campus": "Serra",
        "Edital": "04/2025 - Picti",
        "CodPT": "PT 17339",
        "TituloPT": "Plano de Trabalho A",
        "CodPJ": "PJ 8302",
        "TituloPJ": "Projeto A",
        "AreaConhecimento": "Ciência da Computação",
        "GradeArea": "Ciências Exatas e da Terra",
    }
    linha_atualizada = dict(
        linha_base,
        Cancelado=True,
        CanceladoPor="Por Fulano em 15/03/2026",
        AvaliacaoRelatorio="Enviado",
    )
    linha_distinta = dict(
        linha_base,
        Id=9637,
        Orientado="Aluno Exemplo Segundo",
    )
    (etl_dir / "brutos" / "sigpesq" / "orientacoes" / "2025.json").write_text(
        json.dumps({"linhas": [linha_base]}, ensure_ascii=False), encoding="utf-8"
    )
    (etl_dir / "brutos" / "sigpesq" / "orientacoes" / "2026.json").write_text(
        json.dumps({"linhas": [linha_atualizada, linha_distinta]}, ensure_ascii=False), encoding="utf-8"
    )

    carga = mod.Carga(etl_dir)
    carga.carregar_pessoas()
    carga.sigpesq()
    carga.completar_areas()

    db_path = tmp_path / "orient_dedup.db"
    conn = mod.inicializar_banco_sqlite(db_path)
    try:
        conn.executescript(carga.sql())
        rows = conn.execute(
            "SELECT id_origem, cancelado, relatorio_enviado, nome_cancelador, data_cancelado "
            "FROM orientacao ORDER BY id_origem"
        ).fetchall()
        assert len(rows) == 2
        assert rows[0] == (9636, 1, 1, "Fulano", "2026-03-15")
        assert rows[1][0] == 9637
        assert rows[1][1] == 0
    finally:
        conn.close()


def test_makefile_db_dispara_cruzar_quando_brutos_mais_novo():
    """Garante que o alvo `db` do Makefile checa arquivos em brutos/ mais novos que pessoas.json."""
    makefile_path = Path(__file__).resolve().parents[3] / "Makefile"
    text = makefile_path.read_text(encoding="utf-8")
    assert '-newer "$(ETL_DIR)/trabalho/pessoas.json"' in text

