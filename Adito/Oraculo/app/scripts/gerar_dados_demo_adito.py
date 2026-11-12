"""Gera uma base SQLite fictícia para o contexto exemplo-adito.

Uso: python3 scripts/gerar_dados_demo_adito.py caminho/do/dados.db
"""
import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


# OFFSET 0 mantém o escopo das views nas leituras autorizadas pelo SQLite.
# LIMIT -1 permite retornar todas as linhas.
SCHEMA = """
CREATE TABLE demo_campus (
    id INTEGER PRIMARY KEY, nome TEXT NOT NULL, municipio TEXT NOT NULL, uf TEXT NOT NULL
);
CREATE TABLE demo_area (
    id INTEGER PRIMARY KEY, nome TEXT NOT NULL, grande_area TEXT NOT NULL
);
CREATE TABLE demo_ano (ano INTEGER PRIMARY KEY);
CREATE TABLE demo_pesquisador (
    id INTEGER PRIMARY KEY, nome TEXT NOT NULL, titulacao TEXT NOT NULL,
    campus_id INTEGER NOT NULL REFERENCES demo_campus(id),
    area_id INTEGER NOT NULL REFERENCES demo_area(id),
    orientacoes_concluidas INTEGER NOT NULL,
    orientacoes_em_andamento INTEGER NOT NULL,
    bolsa_produtividade TEXT NOT NULL
);
CREATE TABLE demo_grupo (
    id INTEGER PRIMARY KEY, nome TEXT NOT NULL,
    area_id INTEGER NOT NULL REFERENCES demo_area(id),
    campus_id INTEGER NOT NULL REFERENCES demo_campus(id),
    lider_id INTEGER NOT NULL REFERENCES demo_pesquisador(id),
    ano_formacao INTEGER NOT NULL, situacao TEXT NOT NULL,
    linhas_pesquisa INTEGER NOT NULL, membros_ativos INTEGER NOT NULL
);
CREATE TABLE demo_iniciativa (
    id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, tipo TEXT NOT NULL,
    natureza TEXT NOT NULL, status TEXT NOT NULL,
    ano INTEGER NOT NULL REFERENCES demo_ano(ano),
    data_inicio TEXT NOT NULL, data_fim TEXT,
    area_id INTEGER NOT NULL REFERENCES demo_area(id),
    campus_id INTEGER NOT NULL REFERENCES demo_campus(id),
    coordenador_id INTEGER NOT NULL REFERENCES demo_pesquisador(id),
    grupo_id INTEGER NOT NULL REFERENCES demo_grupo(id),
    orcamento REAL NOT NULL, carga_horaria INTEGER NOT NULL,
    participantes INTEGER NOT NULL, certificados INTEGER NOT NULL
);
CREATE TABLE demo_producao (
    id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, tipo TEXT NOT NULL,
    ano INTEGER NOT NULL REFERENCES demo_ano(ano),
    pesquisador_id INTEGER NOT NULL REFERENCES demo_pesquisador(id),
    iniciativa_id INTEGER NOT NULL REFERENCES demo_iniciativa(id),
    citacoes INTEGER NOT NULL
);
CREATE VIEW demo_dim_campus AS
    SELECT id AS campus_id, nome AS campus, municipio, uf FROM demo_campus LIMIT -1 OFFSET 0;
CREATE VIEW demo_dim_area AS
    SELECT id AS area_id, nome AS area_conhecimento, grande_area FROM demo_area LIMIT -1 OFFSET 0;
CREATE VIEW demo_dim_ano AS SELECT ano FROM demo_ano LIMIT -1 OFFSET 0;
CREATE VIEW demo_dim_pesquisador AS
    SELECT p.id AS pesquisador_id, p.nome AS pesquisador, p.titulacao,
           p.campus_id, c.nome AS campus, p.area_id, a.nome AS area_conhecimento,
           p.orientacoes_concluidas, p.orientacoes_em_andamento, p.bolsa_produtividade
    FROM demo_pesquisador p
    JOIN demo_campus c ON c.id = p.campus_id
    JOIN demo_area a ON a.id = p.area_id LIMIT -1 OFFSET 0;
CREATE VIEW demo_dim_grupo AS
    SELECT g.id AS grupo_id, g.nome AS grupo, g.area_id, a.nome AS area_conhecimento,
           g.campus_id, c.nome AS campus, g.lider_id, p.nome AS lider,
           g.ano_formacao, g.situacao, g.linhas_pesquisa, g.membros_ativos
    FROM demo_grupo g
    JOIN demo_area a ON a.id = g.area_id
    JOIN demo_campus c ON c.id = g.campus_id
    JOIN demo_pesquisador p ON p.id = g.lider_id LIMIT -1 OFFSET 0;
CREATE VIEW demo_fato_iniciativa AS
    SELECT i.id AS iniciativa_id, i.titulo, i.tipo, i.natureza, i.status,
           i.ano, i.data_inicio, i.data_fim, i.area_id, a.nome AS area_conhecimento,
           a.grande_area, i.campus_id, c.nome AS campus, i.coordenador_id,
           p.nome AS coordenador, i.grupo_id, g.nome AS grupo, i.orcamento,
           i.carga_horaria, i.participantes, i.certificados
    FROM demo_iniciativa i
    JOIN demo_area a ON a.id = i.area_id
    JOIN demo_campus c ON c.id = i.campus_id
    JOIN demo_pesquisador p ON p.id = i.coordenador_id
    JOIN demo_grupo g ON g.id = i.grupo_id LIMIT -1 OFFSET 0;
CREATE VIEW demo_fato_producao AS
    SELECT r.id AS producao_id, r.titulo, r.tipo, r.ano, r.pesquisador_id,
           p.nome AS pesquisador, p.titulacao, p.area_id, a.nome AS area_conhecimento,
           a.grande_area, p.campus_id, c.nome AS campus, r.iniciativa_id,
           i.titulo AS iniciativa, r.citacoes
    FROM demo_producao r
    JOIN demo_pesquisador p ON p.id = r.pesquisador_id
    JOIN demo_area a ON a.id = p.area_id
    JOIN demo_campus c ON c.id = p.campus_id
    JOIN demo_iniciativa i ON i.id = r.iniciativa_id LIMIT -1 OFFSET 0;
"""

AREAS = [
    (1, 'Ciência da Computação', 'Ciências Exatas e da Terra'),
    (2, 'Engenharia Elétrica', 'Engenharias'),
    (3, 'Educação', 'Ciências Humanas'),
    (4, 'Engenharia de Produção', 'Engenharias'),
]
GRUPOS = [
    (1, 'Dados e Inteligência Artificial — fictício', 1),
    (2, 'Automação e Energia — fictício', 2),
    (3, 'Educação e Inclusão — fictício', 3),
    (4, 'Gestão e Sustentabilidade — fictício', 4),
    (5, 'Sistemas e Sociedade — fictício', 1),
    (6, 'Robótica Educacional — fictício', 2),
]
TEMAS = {
    1: ['Análise de dados abertos', 'Inteligência artificial acessível', 'Inclusão digital'],
    2: ['Eficiência energética', 'Robótica aplicada', 'Sensores e automação'],
    3: ['Aprendizagem inclusiva', 'Formação de educadores', 'Tecnologia na educação'],
    4: ['Logística sustentável', 'Gestão de processos', 'Economia circular'],
}


def populate(conn):
    conn.execute('INSERT INTO demo_campus VALUES (1, ?, ?, ?)', ('IFES Campus Serra', 'Serra', 'ES'))
    conn.executemany('INSERT INTO demo_area VALUES (?, ?, ?)', AREAS)
    conn.executemany('INSERT INTO demo_ano VALUES (?)', [(year,) for year in range(2023, 2027)])
    for number in range(1, 13):
        conn.execute('INSERT INTO demo_pesquisador VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
            number, f'Pesquisador fictício {number:02d}',
            ['Doutorado', 'Mestrado', 'Especialização'][number % 3],
            1, (number - 1) % 4 + 1, number * 2, number % 5 + 1,
            'Sim' if number % 4 == 0 else 'Não',
        ))
    for number, name, area in GRUPOS:
        conn.execute('INSERT INTO demo_grupo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (
            number, name, area, 1, area, 2010 + number * 2,
            'Em atualização' if number == 6 else 'Certificado', 2 + number % 3, 6 + number * 3,
        ))
    for number in range(1, 61):
        group = GRUPOS[(number - 1) % len(GRUPOS)]
        area = group[2]
        year = 2023 + (number - 1) % 4
        month = (number - 1) % 10 + 1
        research = (number - 1) % 5 < 3
        status = ['Concluído', 'Em andamento', 'Planejado'][((number - 1) // 5) % 3]
        # Anos anteriores ficam concluídos, mantendo datas e situação coerentes.
        if year < 2026:
            status = 'Concluído'
        topic = TEMAS[area][((number - 1) // 6) % 3]
        participants = 0 if research else 20 + number * 2
        certificates = participants - number % 7 if status == 'Concluído' else 0
        conn.execute('INSERT INTO demo_iniciativa VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
            number, f'{topic} — demonstração {number:02d}',
            'Pesquisa' if research else 'Extensão',
            ['Aplicada', 'Básica'][number % 2] if research else ['Curso', 'Projeto', 'Evento'][number % 3],
            status, year, f'{year}-{month:02d}-01',
            f'{year}-{month + 2:02d}-28' if status == 'Concluído' else None,
            area, 1, area + 4 * (number % 3), group[0],
            float(15000 + (number * 7350) % 100000), 20 + number % 12 * 10,
            participants, max(0, certificates),
        ))
    research_ids = [row[0] for row in conn.execute("SELECT id FROM demo_iniciativa WHERE tipo = 'Pesquisa' ORDER BY id")]
    for number in range(1, 121):
        initiative_id = research_ids[(number - 1) % len(research_ids)]
        year, researcher_id, area = conn.execute(
            'SELECT ano, coordenador_id, area_id FROM demo_iniciativa WHERE id = ?', (initiative_id,),
        ).fetchone()
        conn.execute('INSERT INTO demo_producao VALUES (?, ?, ?, ?, ?, ?, ?)', (
            number, f'{TEMAS[area][number % 3]} — produção fictícia {number:03d}',
            ['Artigo', 'Trabalho em evento', 'Livro', 'Capítulo', 'Patente'][number % 5],
            year, researcher_id, initiative_id, number * 7 % 50,
        ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destino', type=Path, help='Novo arquivo SQLite de demonstração.')
    target = parser.parse_args().destino.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    # Reserva exclusiva para que uma base existente nunca seja sobrescrita.
    with target.open('xb'):
        pass
    try:
        with closing(sqlite3.connect(target)) as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            conn.executescript(SCHEMA)
            populate(conn)
            if conn.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('A demonstração contém referências inválidas.')
            conn.commit()
    except Exception:
        target.unlink(missing_ok=True)
        raise
    print(f'Base fictícia criada em {target}')
    print('60 iniciativas, 120 produções, 12 pesquisadores, 6 grupos, 4 áreas, 1 campus e 4 anos.')


if __name__ == '__main__':
    main()
