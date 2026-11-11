#!/usr/bin/env python3
"""Compara o banco carregado com o gabarito, registro a registro.

Resultado de cada verificação:

* OK      – o banco tem exatamente o que o gabarito espera;
* FALHA   – o banco diverge da regra documentada do ETL ou da regra de negócio;
* ALERTA  – o ETL aceitou algo sem regra que o cubra e sem avisar no relatório.

Uso:
    export HORIZON_DATABASE_URL=postgresql://horizon:horizon@localhost:5434/horizon
    python validar_carga.py --schema mock_validacao --schema-sonda mock_completa
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import psycopg
from psycopg import sql

from comum import iso, normalizar_texto

AQUI = os.path.dirname(os.path.abspath(__file__))
HOJE = date.today()

CAUSAS = {
    "C1": "Pessoa gravada com nome vazio quando a fonte traz só o e-mail (e casamento indevido entre essas pessoas)",
    "C2": "Parecer 'Não aprovado' é tratado como aprovado (o filtro procura a palavra 'aprovado')",
    "C3": "Valor da bolsa com separador de milhar ou 'R$' vira 0,00",
    "C4": "Coorientador da formação é gravado como orientador",
    "C5": "Ano numérico (int) em projeto do Lattes derruba a carga do Lattes inteira",
}


class Banco:
    """Fotografia do schema carregado, com pessoas identificadas por 'ref'."""

    def __init__(self, conexao: psycopg.Connection, schema: str):
        self.c = conexao
        with self.c.cursor() as cur:
            cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        self.schema = schema
        self._carregar()

    def q(self, consulta: str, params: tuple = ()) -> List[tuple]:
        with self.c.cursor() as cur:
            cur.execute(consulta, params)
            return cur.fetchall()

    def _carregar(self) -> None:
        self.tabelas = [r[0] for r in self.q(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=%s AND table_type='BASE TABLE'",
            (self.schema,))]
        pessoas = self.q("SELECT id, nome FROM pessoas ORDER BY id")
        lattes = dict(self.q("SELECT pessoa_id, codigo FROM identificadores_pessoa WHERE fonte='lattes'"))
        self.lattes_por_pessoa = lattes
        por_nome = defaultdict(list)
        for pid, nome in pessoas:
            por_nome[nome].append(pid)
        self.ref: Dict[int, str] = {}
        for nome, ids in por_nome.items():
            for k, pid in enumerate(sorted(ids)):
                if not (nome or "").strip():
                    self.ref[pid] = f"<sem nome #{pid}>"
                elif k == 0:
                    self.ref[pid] = nome
                else:
                    self.ref[pid] = f"{nome} [lattes {lattes.get(pid, '#' + str(pid))}]"
        self.pessoas = dict(pessoas)
        self.emails = defaultdict(list)
        for pid, email in self.q("SELECT pessoa_id, email FROM emails_pessoa"):
            self.emails[pid].append(email)
        self.orgs = {i: (n, s, t) for i, n, s, t in self.q("SELECT id, nome, sigla, tipo FROM organizacoes")}
        self.unidades = {i for (i,) in self.q("SELECT id FROM unidades_organizacionais")}
        self.papeis = {i: n for i, n in self.q("SELECT id, nome FROM papeis")}
        self.areas = {i: n for i, n in self.q("SELECT id, nome FROM areas_conhecimento")}
        # grupos
        self.grupos = {}
        for gid, nome, sigla, desc, org, url, ini in self.q(
                "SELECT e.id, e.nome, e.sigla, e.descricao, e.organizacao_id, g.url_cnpq, g.data_inicio "
                "FROM equipes e LEFT JOIN grupos_pesquisa g ON g.id=e.id"):
            self.grupos[gid] = {"nome": nome, "sigla": sigla, "descricao": desc, "unidade": self.orgs[org][0],
                                "url_cnpq": url, "data_inicio": iso(ini), "areas": [], "membros": []}
        for eq, pid, papel, ini, fim in self.q(
                "SELECT equipe_id, pessoa_id, papel_id, data_inicio, data_fim FROM membros_equipe"):
            self.grupos[eq]["membros"].append([self.ref[pid], self.papeis[papel], iso(ini), iso(fim)])
        for eq, area in self.q("SELECT equipe_id, area_id FROM areas_conhecimento_equipe"):
            self.grupos[eq]["areas"].append(self.areas[area])
        for g in self.grupos.values():
            g["membros"].sort()
            g["areas"].sort()
        # iniciativas
        tipos = dict(self.q("SELECT id, nome FROM tipos_iniciativa"))
        self.inits = {}
        for iid, nome, tipo, org, sit, desc, ini, fim in self.q(
                "SELECT id, nome, tipo_iniciativa_id, organizacao_id, situacao, descricao, data_inicio, data_fim "
                "FROM iniciativas"):
            self.inits[iid] = {"nome": nome, "tipo": tipos[tipo], "organizacao": self.orgs[org][0],
                               "situacao": sit, "descricao": desc, "data_inicio": iso(ini), "data_fim": iso(fim),
                               "participantes": defaultdict(list), "areas": [], "equipes": [],
                               "organizacoes": [], "pai": None, "bolsas": []}
        part_ref = {}
        for pid_, iid, pes, papel, ini in self.q(
                "SELECT id, iniciativa_id, pessoa_id, papel_id, data_inicio FROM participantes_iniciativa"):
            self.inits[iid]["participantes"][self.papeis[papel]].append([self.ref[pes], iso(ini)])
            part_ref[pid_] = (iid, self.ref[pes])
        for iid, area in self.q("SELECT iniciativa_id, area_id FROM areas_conhecimento_iniciativa"):
            self.inits[iid]["areas"].append(self.areas[area])
        for iid, eq, papel in self.q("SELECT iniciativa_id, equipe_id, papel FROM equipes_iniciativa"):
            self.inits[iid]["equipes"].append([self.grupos[eq]["nome"], papel])
        for iid, org, papel in self.q("SELECT iniciativa_id, organizacao_id, papel FROM organizacoes_iniciativa"):
            self.inits[iid]["organizacoes"].append([self.orgs[org][0], papel])
        for iid, pai in self.q("SELECT iniciativa_id, iniciativa_pai_id FROM hierarquia_iniciativas"):
            self.inits[iid]["pai"] = self.inits[pai]["nome"]
        self.bolsas = {}
        for bid, nome, valor, fin in self.q("SELECT id, nome, valor, financiador_id FROM bolsas"):
            self.bolsas[bid] = {"nome": nome, "valor": float(valor), "financiador": self.orgs[fin][0]}
        for part, bid in self.q("SELECT participante_id, bolsa_id FROM bolsas_participante"):
            iid, ref = part_ref[part]
            b = self.bolsas[bid]
            self.inits[iid]["bolsas"].append([ref, [b["nome"].lower(), b["financiador"]]])
        for v in self.inits.values():
            v["participantes"] = {k: sorted(x) for k, x in v["participantes"].items()}
            for campo in ("areas", "equipes", "organizacoes", "bolsas"):
                v[campo].sort()
        # Lattes
        self.perfis = {p: {"resumo": r, "nomes_citacao": n, "atualizado_em": a.isoformat()}
                       for p, r, n, a in self.q("SELECT pessoa_id, resumo, nomes_citacao, atualizado_em FROM perfis_lattes")}
        self.premios = defaultdict(list)
        for p, t, a in self.q("SELECT pessoa_id, titulo, ano FROM premios"):
            self.premios[p].append([t, a])
        idiomas = dict(self.q("SELECT id, nome FROM idiomas"))
        self.prof = defaultdict(dict)
        for p, i, le, es, fa, co in self.q(
                "SELECT pessoa_id, idioma_id, leitura, escrita, fala, compreensao FROM proficiencias"):
            self.prof[p][idiomas[i]] = {"leitura": le, "escrita": es, "fala": fa, "compreensao": co}
        self.vinculos = defaultdict(list)
        for p, o, pap, ini, fim in self.q(
                "SELECT pessoa_id, organizacao_id, papel_id, data_inicio, data_fim FROM vinculos"):
            self.vinculos[p].append([self.orgs[o][0], self.papeis[pap], iso(ini), iso(fim)])
        tipos_f = dict(self.q("SELECT id, nome FROM tipos_formacao"))
        orient = defaultdict(list)
        for f, p, papel in self.q("SELECT formacao_id, pessoa_id, papel FROM orientadores_formacao"):
            orient[f].append([self.ref[p], papel])
        self.formacoes = defaultdict(list)
        for fid, p, t, o, curso, ai, af, tese in self.q(
                "SELECT id, pessoa_id, tipo_formacao_id, organizacao_id, curso, ano_inicio, ano_fim, titulo_tese "
                "FROM formacoes_academicas"):
            self.formacoes[p].append([tipos_f[t], self.orgs[o][0], curso, ai, af, tese, sorted(orient[fid])])
        tipos_p = dict(self.q("SELECT id, nome FROM tipos_producao"))
        artigos = {i: {"veiculo": v, "volume": vol, "paginas": pag, "doi": doi}
                   for i, v, vol, pag, doi in self.q("SELECT id, veiculo, volume, paginas, doi FROM artigos")}
        autores = defaultdict(list)
        for prod, p in self.q("SELECT producao_id, pessoa_id FROM autores_producao"):
            autores[prod].append(p)
        self.producoes = {}
        for i, t, a, tipo, link in self.q("SELECT id, titulo, ano, tipo_producao_id, link FROM producoes"):
            self.producoes[i] = {"linha": [t, a, tipos_p[tipo], link, artigos.get(i),
                                           sorted(self.ref[p] for p in autores[i])], "autores": set(autores[i])}
        self.areas_pessoa = sorted([self.ref[p], self.areas[a]] for p, a in
                                   self.q("SELECT pessoa_id, area_id FROM areas_conhecimento_pessoa"))

    def pessoa_por_lattes(self, lattes_id: str) -> Optional[int]:
        for p, cod in self.lattes_por_pessoa.items():
            if cod == lattes_id:
                return p
        return None

    def inits_por(self, nome: str, tipo: Optional[str] = None) -> List[int]:
        return [i for i, v in self.inits.items() if v["nome"] == nome and (tipo is None or v["tipo"] == tipo)]

    def grupo_por_nome(self, nome: str) -> List[int]:
        return [i for i, g in self.grupos.items() if normalizar_texto(g["nome"]) == normalizar_texto(nome)]


def diff(esperado: Any, obtido: Any) -> str:
    if isinstance(esperado, list) and isinstance(obtido, list):
        e = Counter(json.dumps(x, sort_keys=True, ensure_ascii=False, default=str) for x in esperado)
        o = Counter(json.dumps(x, sort_keys=True, ensure_ascii=False, default=str) for x in obtido)
        falta, sobra = list((e - o).elements()), list((o - e).elements())
        partes = []
        if falta:
            partes.append("faltando: " + "; ".join(falta))
        if sobra:
            partes.append("sobrando: " + "; ".join(sobra))
        return " | ".join(partes)
    if isinstance(esperado, dict) and isinstance(obtido, dict):
        partes = []
        for k in sorted(set(esperado) | set(obtido)):
            if esperado.get(k) != obtido.get(k):
                d = diff(esperado.get(k, []), obtido.get(k, [])) if isinstance(esperado.get(k, obtido.get(k)), list) \
                    else f"esperado={esperado.get(k)!r} obtido={obtido.get(k)!r}"
                partes.append(f"{k}: {d}")
        return " || ".join(partes)
    return f"esperado={esperado!r} obtido={obtido!r}"


class Validador:
    def __init__(self, banco: Banco, gabarito: dict, catalogo: Dict[str, dict], relatorio: dict):
        self.b = banco
        self.g = gabarito
        self.cat = catalogo
        self.rel = relatorio
        self.checks: List[dict] = []

    def add(self, registro, verificacao, status, esperado=None, obtido=None, detalhe="", regra="documentada", causa=None):
        info = self.cat.get(registro, {})
        if status != "OK" and causa is None:
            causa = self._causa(registro, detalhe)
        self.checks.append({
            "registro": registro, "fonte": info.get("fonte", "global"), "tipo_caso": info.get("tipo_caso", "-"),
            "cenario": info.get("cenario", ""), "verificacao": verificacao, "status": status, "regra": regra,
            "causa": causa, "detalhe": detalhe,
            "esperado": esperado if status != "OK" else None, "obtido": obtido if status != "OK" else None,
        })

    @staticmethod
    def _causa(registro, detalhe) -> Optional[str]:
        if "<sem nome" in detalhe:
            return "C1"
        if registro == "P64":
            return "C2"
        if registro in ("B108", "B109"):
            return "C3"
        if registro == "L49" and "coorientador" in detalhe:
            return "C4"
        return None

    def comparar(self, registro, verificacao, esperado, obtido, regra="documentada", causa=None):
        if esperado == obtido:
            self.add(registro, verificacao, "OK")
        else:
            self.add(registro, verificacao, "FALHA", esperado, obtido, diff(esperado, obtido), regra, causa)

    def comparar_init(self, registro: str, esp: dict, prefixo="") -> Optional[int]:
        ids = self.b.inits_por(esp["nome"], esp["tipo"])
        if len(ids) != 1:
            self.add(registro, f"{prefixo}iniciativa gravada uma única vez", "FALHA", 1, len(ids),
                     f"{len(ids)} iniciativa(s) '{esp['nome'][:60]}' do tipo {esp['tipo']}")
            return None
        self.add(registro, f"{prefixo}iniciativa gravada uma única vez", "OK")
        obt = self.b.inits[ids[0]]
        for campo in ("organizacao", "situacao", "descricao", "data_inicio", "data_fim", "pai"):
            self.comparar(registro, f"{prefixo}{campo}", esp[campo], obt[campo])
        self.comparar(registro, f"{prefixo}participantes", esp["participantes"], obt["participantes"])
        for campo in ("areas", "equipes", "organizacoes", "bolsas"):
            self.comparar(registro, f"{prefixo}{campo}", esp[campo], obt[campo])
        return ids[0]

    # ------------------------------------------------------------------ fontes
    def grupos(self):
        for rid, esp in self.g["registros"].items():
            if not rid.startswith("G"):
                continue
            if esp.get("carregado"):
                ge = esp["grupo"]
                ids = self.b.grupo_por_nome(ge["nome"])
                if len(ids) != 1:
                    self.add(rid, "grupo gravado uma única vez", "FALHA", 1, len(ids))
                    continue
                self.add(rid, "grupo gravado uma única vez", "OK")
                go = self.b.grupos[ids[0]]
                for campo in ("sigla", "unidade", "url_cnpq"):
                    self.comparar(rid, campo, ge[campo], go[campo])
                lideres_e = sorted(m for m in ge["membros"] if m[1] == "lider")
                lideres_o = sorted(m for m in go["membros"] if m[1] == "lider")
                self.comparar(rid, "líderes", lideres_e, lideres_o)
            elif esp.get("repetido"):
                ge = esp["grupo"]
                ids = self.b.grupo_por_nome(ge["nome"])
                self.comparar(rid, "repetido não cria grupo novo", 1, len(ids))
                if len(ids) == 1:
                    self.comparar(rid, "repetido atualiza a URL do grupo existente", ge["url_cnpq"],
                                  self.b.grupos[ids[0]]["url_cnpq"])
            else:
                self.comparar(rid, "grupo sem nome não é gravado", 0,
                              sum(1 for g in self.b.grupos.values() if not (g["nome"] or "").strip()))

    def projetos(self):
        for rid, esp in self.g["registros"].items():
            if not rid.startswith("P"):
                continue
            if esp.get("carregado"):
                self.comparar_init(rid, esp["iniciativa"])
                if "grupo_criado" in esp:
                    ge = esp["grupo_criado"]
                    ids = self.b.grupo_por_nome(ge["nome"])
                    if len(ids) == 1:
                        go = self.b.grupos[ids[0]]
                        for campo in ("unidade", "descricao", "membros", "areas"):
                            self.comparar(rid, f"grupo criado pelo projeto: {campo}", ge[campo], go[campo])
                    else:
                        self.add(rid, "grupo criado pelo projeto", "FALHA", 1, len(ids))
            else:
                titulo = (esp.get("titulo") or "").strip()
                achados = self.b.inits_por(titulo, "projeto_pesquisa") if titulo else []
                regra = esp.get("regra", "documentada")
                self.comparar(rid, "registro não carregado", 0, len(achados), regra=regra)

    def bolsistas(self):
        for rid, esp in self.g["registros"].items():
            if not rid.startswith("B"):
                continue
            if not esp.get("carregado"):
                ok = any(p["registro"] == f"linha {esp['linha']}" and p["passo"] == "bolsistas_sigpesq"
                         for p in self.rel["pendencias"])
                self.add(rid, "linha descartada aparece nas pendências", "OK" if ok else "FALHA",
                         f"linha {esp['linha']}", None)
                continue
            iid = self.comparar_init(rid, esp["iniciativa"])
            bolsa = esp.get("bolsa")
            if bolsa:
                achada = [b for b in self.b.bolsas.values()
                          if b["nome"].lower() == bolsa["nome"].lower() and b["financiador"] == bolsa["financiador"]]
                if len(achada) != 1:
                    self.add(rid, "bolsa (programa + financiador)", "FALHA", 1, len(achada))
                elif bolsa["valor"] is None:
                    self.add(rid, "valor da bolsa", "ALERTA", "valor inválido → pendência", achada[0]["valor"],
                             "valor não numérico na planilha foi gravado como 0,00 sem pendência")
                else:
                    self.comparar(rid, "valor da bolsa", bolsa["valor"], achada[0]["valor"],
                                  regra="negocio" if rid in ("B108", "B109") else "documentada")
            if rid == "B110":
                self.add(rid, "valor divergente da mesma bolsa", "ALERTA", "850,00 registrado ou sinalizado",
                         "mantido o 1º valor (700,00)",
                         "bolsa é única por programa+financiador: um valor diferente é descartado sem aviso")

    def cnpq(self):
        for rid, esp in self.g["registros"].items():
            if not rid.startswith("C"):
                continue
            ge = esp["grupo"]
            ids = self.b.grupo_por_nome(ge["nome"])
            if len(ids) != 1:
                self.add(rid, "grupo do espelho localizado", "FALHA", ge["nome"], len(ids))
                continue
            go = self.b.grupos[ids[0]]
            for campo in ("nome", "descricao", "data_inicio", "url_cnpq"):
                self.comparar(rid, campo, ge[campo], go[campo])
            self.comparar(rid, "membros (papel e datas)", ge["membros"], go["membros"])
            self.comparar(rid, "áreas/linhas de pesquisa", ge["areas"], go["areas"])

    def lattes(self):
        for rid, esp in self.g["registros"].items():
            if not rid.startswith("L"):
                continue
            if esp["sonda_quebra"]:
                continue  # validado na execução com sonda
            pid = self.b.pessoa_por_lattes(esp["lattes_id"])
            if not esp["lido"]:
                pend = any(esp["arquivo"] in (p["registro"] or "") or esp["lattes_id"] in (p["registro"] or "")
                           for p in self.rel["pendencias"])
                self.comparar(rid, "arquivo inválido não gera pessoa", None, pid)
                self.add(rid, "arquivo ignorado aparece no relatório", "OK" if pend else "ALERTA",
                         "pendência com o nome do arquivo", None if not pend else "presente",
                         "arquivo descartado em silêncio por ler_curriculos (não entra nas pendências)")
                continue
            if "pessoa" not in esp:
                self.comparar(rid, "currículo sem nome não gera pessoa", None, pid)
                continue
            if pid is None:
                self.add(rid, "pessoa com o ID Lattes", "FALHA", esp["pessoa"], None)
                continue
            self.comparar(rid, "pessoa (casamento pelo nome / homônimo)", esp["pessoa"], self.b.ref[pid])
            self.comparar(rid, "perfil Lattes", esp["perfil"], self.b.perfis.get(pid))
            self.comparar(rid, "prêmios", esp["premios"], sorted(self.b.premios.get(pid, [])))
            self.comparar(rid, "idiomas e proficiência", esp["proficiencias"], dict(self.b.prof.get(pid, {})))
            self.comparar(rid, "vínculos", esp["vinculos"], sorted(self.b.vinculos.get(pid, [])))
            self.comparar(rid, "formações e orientadores", esp["formacoes"], sorted(self.b.formacoes.get(pid, [])))
            prods = sorted(p["linha"] for p in self.b.producoes.values() if pid in p["autores"])
            self.comparar(rid, "produções, artigos e coautores", esp["producoes"], prods)
            for k, pj in enumerate(esp["projetos"]):
                self.comparar_init(rid, pj, prefixo=f"projeto {k + 1}: ")
            for k, ori in enumerate(esp["orientacoes"]):
                self.comparar_init(rid, ori, prefixo=f"orientação {k + 1}: ")
        # alertas de transformação sem regra
        reg = self.g["registros"]
        for pj in reg["L09"]["projetos"]:
            if pj["nome"].endswith("2027"):
                self.add("L09", "situação de projeto com término futuro", "ALERTA", "em_andamento", pj["situacao"],
                         "Lattes sem 'Atual' vira 'Concluded' mesmo com ano de conclusão no futuro")
        for o in reg["L10"]["orientacoes"]:
            if o["nome"] == "Orientação em andamento mock só com ano":
                self.add("L10", "datas de orientação em andamento", "ALERTA", "data_inicio=2025-01-01, data_fim=None",
                         f"data_inicio={o['data_inicio']}, data_fim={o['data_fim']}",
                         "para orientação em andamento o 'ano' do Lattes é o início, mas vira data de fim")
        for pj in reg["L47"]["projetos"]:
            if not pj["participantes"]:
                self.add("L47", "projeto do Lattes sem integrantes", "ALERTA", "dono do currículo como participante",
                         "nenhum participante", "projeto sem integrantes fica sem nenhum participante, nem o dono")

    def sonda(self, execucao: dict, banco_sonda: Optional[Banco]):
        reg = "L50"
        if execucao is None:
            return
        if execucao["status"] == "concluida":
            self.add(reg, "currículo com ano numérico é carregado", "OK")
            return
        detalhe = execucao.get("erro", "")
        contagens = execucao["relatorio_carga"]["contagens"]
        efeito = []
        if banco_sonda is not None:
            efeito.append(f"perfis Lattes gravados: {len(banco_sonda.perfis)}")
            efeito.append(f"formações gravadas: {sum(len(v) for v in banco_sonda.formacoes.values())}")
            efeito.append(f"produções gravadas: {len(banco_sonda.producoes)}")
            efeito.append("orientações do Lattes: " + str(contagens.get("lattes_orientacoes", {}).get("orientacao_criadas", 0)))
        self.add(reg, "currículo com ano numérico é carregado", "FALHA", "carga concluída",
                 "carga interrompida", f"{detalhe}. Efeito: {', '.join(efeito)}; passo lattes_curriculos "
                 "desfeito por inteiro, orientações do Lattes e enriquecimento PJ não executados", causa="C5")

    # ------------------------------------------------------------------ globais
    def globais(self):
        t = self.g["totais"]
        self.comparar("GLOBAL", "33 tabelas do ModeloLogicoHorizon.sql", 33, len(self.b.tabelas))
        refs = sorted(r for p, r in self.b.ref.items() if not r.startswith("<sem nome"))
        self.comparar("GLOBAL", "pessoas (lista completa, sem duplicidade)", t["pessoas"], refs)
        sem_nome = sorted(r for r in self.b.ref.values() if r.startswith("<sem nome"))
        self.comparar("GLOBAL", "nenhuma pessoa sem nome", [], sem_nome, regra="negocio")
        por_tipo = dict(Counter(v["tipo"] for v in self.b.inits.values()))
        self.comparar("GLOBAL", "iniciativas por tipo", t["iniciativas_por_tipo"], dict(sorted(por_tipo.items())),
                      causa="C2")
        self.comparar("GLOBAL", "equipes (grupos)", t["equipes"], len(self.b.grupos))
        self.comparar("GLOBAL", "grupos com URL do CNPq", t["grupos_com_url"],
                      sum(1 for g in self.b.grupos.values() if g["url_cnpq"]))
        unidades = sorted(self.b.orgs[i][0] for i in self.b.unidades)
        self.comparar("GLOBAL", "unidades (campi)", t["unidades"], unidades)
        orgs = sorted([n, tp] for i, (n, s, tp) in self.b.orgs.items() if tp != "unidade")
        self.comparar("GLOBAL", "organizações (nome e tipo)", sorted(t["organizacoes"]), orgs)
        bolsas = sorted([b["nome"], b["financiador"], b["valor"]] for b in self.b.bolsas.values())
        esperadas = sorted([n, f, v if v is not None else 0.0] for n, f, v in t["bolsas"])
        self.comparar("GLOBAL", "bolsas (programa, financiador, valor)", esperadas, bolsas, regra="negocio",
                      causa="C3")
        self.comparar("GLOBAL", "áreas de conhecimento", sorted(t["areas"]), sorted(self.b.areas.values()))
        self.comparar("GLOBAL", "produções", t["producoes"], len(self.b.producoes))
        self.comparar("GLOBAL", "áreas das pessoas", t["areas_pessoa"], self.b.areas_pessoa)
        # LGPD
        crus = [e for lst in self.b.emails.values() for e in lst if not e.endswith("@anon.lgpd")]
        self.comparar("GLOBAL", "LGPD: todo e-mail gravado em hash", [], crus)
        com_arroba = [n for n in self.b.pessoas.values() if n and "@" in n]
        self.comparar("GLOBAL", "LGPD: nenhum e-mail em nome de pessoa", [], com_arroba)
        # e-mails da fonte que não foram gravados
        faltando = 0
        pessoas_afetadas = 0
        for ref, emails in t["emails_por_pessoa"].items():
            gravados = len(t["emails_gravados_por_pessoa"].get(ref, []))
            if len(emails) > gravados:
                pessoas_afetadas += 1
                faltando += len(emails) - gravados
        pid_por_ref = {r: p for p, r in self.b.ref.items()}
        gravados_banco = sum(len(self.b.emails.get(pid_por_ref.get(r), [])) for r in t["emails_gravados_por_pessoa"])
        self.comparar("GLOBAL", "e-mails gravados na criação da pessoa",
                      sum(len(v) for v in t["emails_gravados_por_pessoa"].values()), gravados_banco)
        if faltando:
            self.add("GLOBAL", "e-mails vistos nas fontes x gravados", "ALERTA",
                     f"{sum(len(v) for v in t['emails_por_pessoa'].values())} e-mails",
                     f"{faltando} e-mail(s) de {pessoas_afetadas} pessoa(s) não gravados",
                     "e-mail só é gravado quando a pessoa é criada; se ela já existia (casada pelo nome), "
                     "o e-mail da nova fonte fica só no cache da execução")
        dup = [n for n, c in Counter((v["nome"], v["tipo"]) for v in self.b.inits.values()).items() if c > 1]
        self.comparar("GLOBAL", "nenhuma iniciativa duplicada (nome + tipo)", [], [list(d) for d in dup])
        fomento_ifes = [n for n, s, tp in self.b.orgs.values() if normalizar_texto(n) == "ifes" and tp == "fomento"]
        if fomento_ifes:
            self.add("GLOBAL", "IFES como agência financiadora", "ALERTA", "reaproveitar a organização IFES",
                     "organização 'IFES' (fomento) separada de 'Instituto Federal do Espírito Santo'",
                     "AgFinanciadora='IFES' não casa com a sigla da instituição e cria outra organização")
        p69 = self.g["registros"]["P69"]["iniciativa"]
        if p69["data_fim"] and p69["data_inicio"] and p69["data_fim"] < p69["data_inicio"]:
            self.add("P69", "data de fim anterior ao início", "ALERTA", "pendência ou revisão",
                     f"gravado {p69['data_inicio']} → {p69['data_fim']}", "não há validação de período")

    def relatorio(self):
        obtidas = [(p["passo"], p["motivo"], p["registro"]) for p in self.rel["pendencias"]]
        for p in self.g["pendencias"]:
            chave = (p["passo"], p["motivo"], p["registro"])
            ok = chave in obtidas
            self.add("RELATORIO", f"pendência: {p['passo']} / {p['motivo']} / {p['registro'][:70]}",
                     "OK" if ok else "FALHA", "presente", None if ok else "ausente",
                     regra=p["regra"], causa=None if ok else ("C1" if "sem nome" in p["motivo"] else None))
        esperadas = {(p["passo"], p["motivo"], p["registro"]) for p in self.g["pendencias"]}
        for extra in [o for o in obtidas if o not in esperadas]:
            self.add("RELATORIO", f"pendência inesperada: {' / '.join(extra)}", "FALHA", "ausente", "presente")
        obt_rev = [(p["passo"], p["motivo"], p["registro"]) for p in self.rel["revisar"]]
        esp_rev = [(p["passo"], p["motivo"], p["registro"]) for p in self.g["revisoes"]]
        self.comparar("RELATORIO", "itens para revisão humana", sorted(map(list, esp_rev)), sorted(map(list, obt_rev)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dados", default=os.path.join(AQUI, "dados"))
    ap.add_argument("--resultados", default=os.path.join(AQUI, "resultados"))
    ap.add_argument("--schema", default="mock_validacao")
    ap.add_argument("--schema-sonda", default="mock_completa")
    args = ap.parse_args()

    with open(os.path.join(args.dados, "gabarito.json"), encoding="utf-8") as fh:
        gabarito = json.load(fh)
    with open(os.path.join(args.dados, "catalogo_registros.csv"), encoding="utf-8") as fh:
        catalogo = {r["id"]: r for r in csv.DictReader(fh)}
    with open(os.path.join(args.resultados, "execucao_principal.json"), encoding="utf-8") as fh:
        execucao = json.load(fh)
    caminho_sonda = os.path.join(args.resultados, "execucao_completa_com_sonda.json")
    execucao_sonda = json.load(open(caminho_sonda, encoding="utf-8")) if os.path.exists(caminho_sonda) else None

    with psycopg.connect(os.environ["HORIZON_DATABASE_URL"]) as conexao:
        banco = Banco(conexao, args.schema)
        banco_sonda = Banco(conexao, args.schema_sonda) if execucao_sonda else None
        v = Validador(banco, gabarito, catalogo, execucao["relatorio_carga"])
        v.grupos()
        v.projetos()
        v.bolsistas()
        v.cnpq()
        v.lattes()
        v.sonda(execucao_sonda, banco_sonda)
        v.globais()
        v.relatorio()

    checks = v.checks
    por_registro = defaultdict(list)
    for c in checks:
        por_registro[c["registro"]].append(c["status"])
    resumo_registros = {}
    for rid, info in catalogo.items():
        st = por_registro.get(rid, [])
        resumo_registros[rid] = "FALHA" if "FALHA" in st else ("ALERTA" if "ALERTA" in st else ("OK" if st else "SEM VERIFICAÇÃO"))
    saida = {
        "executado_em": datetime.now().isoformat(timespec="seconds"),
        "schema": args.schema,
        "totais": dict(Counter(c["status"] for c in checks)),
        "registros": dict(Counter(resumo_registros.values())),
        "causas": CAUSAS,
        "resumo_por_registro": resumo_registros,
        "verificacoes": checks,
    }
    os.makedirs(args.resultados, exist_ok=True)
    with open(os.path.join(args.resultados, "resultado_validacao.json"), "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(args.resultados, "resultado_validacao.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["registro", "fonte", "tipo_caso", "cenario", "verificacao", "status",
                                           "regra", "causa", "detalhe"], extrasaction="ignore")
        w.writeheader()
        w.writerows(checks)
    print(f"verificações: {saida['totais']}")
    print(f"registros:    {saida['registros']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
