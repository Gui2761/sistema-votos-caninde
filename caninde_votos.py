#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Análise e Consulta de Votos por Seção e Local de Votação
Município: Canindé de São Francisco / SE (28ª Zona Eleitoral - Código TSE: 31232)
Desenvolvido sob o Ecossistema Master Skill (BMad Method, Spec-Kit, Antigravity Kit)
"""

import os
import sys
import json
import sqlite3
import argparse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Configura encoding do console do Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "caninde_votos.db")
JSON_PATH = os.path.join(BASE_DIR, "data_caninde.json")

def get_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Banco de dados não encontrado em {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cabos_eleitorais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano INTEGER DEFAULT 2026,
            cargo TEXT,
            nr_candidato TEXT,
            nm_candidato TEXT,
            nr_local TEXT,
            local_nome TEXT,
            nr_secao TEXT,
            nome_cabo TEXT NOT NULL,
            telefone TEXT,
            observacao TEXT,
            meta_votos INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# ==========================================
# FUNÇÕES DE CONSULTA DO SISTEMA
# ==========================================

def list_locais(ano=2026):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.nr_local, l.apelido, l.nome, l.bairro,
               GROUP_CONCAT(s.nr_secao, ', ') as secoes
        FROM locais l
        JOIN secoes_locais s ON l.nr_local = s.nr_local AND l.ano = s.ano
        WHERE l.ano = ?
        GROUP BY l.nr_local, l.apelido, l.nome, l.bairro
        ORDER BY l.apelido
    """, (ano,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_ranking(ano=2026, cargo="Deputado Estadual", nr_local=None, nr_secao=None, top_n=9):
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT nr_votavel, nm_votavel, partido_sg, cargo, SUM(qt_votos) as total_votos
        FROM boletim_urna
        WHERE ano = ? AND tipo_votavel = 'Nominal'
    """
    params = [ano]
    
    if cargo and cargo not in ("ALL", "Todos", "Todos os Cargos"):
        query += " AND cargo = ?"
        params.append(cargo)
    
    if nr_local:
        query += " AND nr_local = ?"
        params.append(str(nr_local))
        
    if nr_secao:
        query += " AND nr_secao = ?"
        params.append(str(nr_secao))
        
    query += " GROUP BY nr_votavel, nm_votavel, partido_sg, cargo ORDER BY total_votos DESC LIMIT ?"
    params.append(top_n)
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_secao_detail(ano=2026, nr_secao="85", cargo=None):
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT b.ano, b.cargo, b.nr_secao, b.nr_local, l.apelido as local_nome,
               b.nr_votavel, b.nm_votavel, b.partido_sg, b.tipo_votavel, b.qt_votos
        FROM boletim_urna b
        LEFT JOIN locais l ON b.nr_local = l.nr_local AND b.ano = l.ano
        WHERE b.ano = ? AND b.nr_secao = ?
    """
    params = [ano, str(nr_secao)]
    
    if cargo:
        query += " AND b.cargo = ?"
        params.append(cargo)
        
    query += " ORDER BY b.cargo, b.qt_votos DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# ==========================================
# GESTÃO DE CABOS ELEITORAIS
# ==========================================

def add_cabo(ano=2026, cargo="Deputado Estadual", nr_candidato="44111", nm_candidato="MARCELO SOBRAL",
             nr_local="1090", local_nome="Agrovila", nr_secao="85", nome_cabo="", telefone="", observacao="", meta_votos=0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO cabos_eleitorais (ano, cargo, nr_candidato, nm_candidato, nr_local, local_nome, nr_secao, nome_cabo, telefone, observacao, meta_votos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ano, cargo, nr_candidato, nm_candidato, nr_local, local_nome, nr_secao, nome_cabo, telefone, observacao, meta_votos))
    cabo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return cabo_id

def list_cabos(ano=2026, nr_local=None, nr_secao=None, nr_candidato=None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM cabos_eleitorais WHERE ano = ?"
    params = [ano]
    if nr_local and nr_local != "ALL":
        query += " AND nr_local = ?"
        params.append(str(nr_local))
    if nr_secao and nr_secao != "ALL":
        query += " AND nr_secao = ?"
        params.append(str(nr_secao))
    if nr_candidato:
        query += " AND nr_candidato = ?"
        params.append(str(nr_candidato))
    query += " ORDER BY id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_cabo(cabo_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM cabos_eleitorais WHERE id = ?", (cabo_id,))
    rows_affected = cur.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def seed_sample_cabos():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM cabos_eleitorais")
    count = cur.fetchone()[0]
    if count == 0:
        samples = [
            (2026, "Deputado Estadual", "44111", "MARCELO OLIVEIRA SOBRAL", "1090", "Escola Municipal Agrovila", "85", "Severino da Silva (Biu)", "(79) 99881-2233", "Liderança central no Povoado Agrovila", 50),
            (2026, "Deputado Estadual", "44111", "MARCELO OLIVEIRA SOBRAL", "1112", "EMEF Maria do Carmo", "1", "Dona Raimunda Santos", "(79) 99912-3344", "Coordenação de mobilização no Centro", 45),
            (2026, "Deputado Estadual", "44000", "LIDIANE CECÍLIA LUCENA", "1090", "Escola Municipal Agrovila", "94", "Marcos Antônio de Jesus", "(79) 99877-4455", "Apoio comunitário Bloco B", 35),
            (2026, "Deputado Federal", "4444", "YANDRA BARRETO FERREIRA", "1031", "EMEF Domingos Gerônimo", "3", "Cláudio do Capim Grosso", "(79) 99122-8899", "Mobilizador regional Capim Grosso", 80),
            (2026, "Governador", "55", "FABIO CRUZ MITIDIERI", "1023", "Colégio Estadual Delmiro Gouveia", "53", "José Carlos (Zé do Posto)", "(79) 98833-1122", "Articulador comercial Bairro Olaria", 100),
            (2026, "Senador", "131", "ROGERIO CARVALHO SANTOS", "1015", "Escola Estadual Dom Juvêncio", "9", "Professora Rita de Cássia", "(79) 99655-4433", "Movimento Educação e Assentamentos", 70)
        ]
        cur.executemany("""
            INSERT INTO cabos_eleitorais (ano, cargo, nr_candidato, nm_candidato, nr_local, local_nome, nr_secao, nome_cabo, telefone, observacao, meta_votos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, samples)
        conn.commit()
    conn.close()

def get_relatorio_candidatos_cabos(ano=2026, nr_candidato=None, cargo=None):
    seed_sample_cabos()
    conn = get_db()
    cur = conn.cursor()

    query_cands = "SELECT DISTINCT nr_candidato, nm_candidato, cargo FROM cabos_eleitorais WHERE ano = ?"
    params_cands = [ano]
    if nr_candidato:
        query_cands += " AND nr_candidato = ?"
        params_cands.append(str(nr_candidato))
    if cargo and cargo not in ("ALL", "Todos"):
        query_cands += " AND cargo = ?"
        params_cands.append(cargo)
    query_cands += " ORDER BY cargo, nm_candidato"

    cur.execute(query_cands, params_cands)
    cands_rows = cur.fetchall()

    relatorio = []
    tot_meta_global = 0
    tot_votos_urnas_global = 0
    tot_cabos_global = 0

    for nr, nm, cg in cands_rows:
        cur.execute("SELECT SUM(qt_votos) FROM boletim_urna WHERE ano = ? AND nr_votavel = ?", (ano, nr))
        votos_gerais = cur.fetchone()[0] or 0

        cur.execute("SELECT partido_sg FROM boletim_urna WHERE ano = ? AND nr_votavel = ? LIMIT 1", (ano, nr))
        partido_row = cur.fetchone()
        partido = partido_row[0] if partido_row else ""

        cur.execute("""
            SELECT id, nome_cabo, telefone, local_nome, nr_secao, meta_votos, observacao, nr_local
            FROM cabos_eleitorais
            WHERE ano = ? AND nr_candidato = ?
            ORDER BY local_nome, nr_secao
        """, (ano, nr))
        cabos = cur.fetchall()

        cand_cabos = []
        meta_cand = 0
        votos_urnas_cand = 0

        for c in cabos:
            cid, nome_cabo, tel, local_nome, nr_secao, meta, obs, nr_local = c
            meta = meta or 0
            meta_cand += meta
            tot_cabos_global += 1

            if nr_local == "ALL":
                cur.execute("SELECT SUM(qt_votos) FROM boletim_urna WHERE ano = ? AND nr_votavel = ?", (ano, nr))
            elif nr_secao == "Todas":
                cur.execute("SELECT SUM(qt_votos) FROM boletim_urna WHERE ano = ? AND nr_votavel = ? AND nr_local = ?", (ano, nr, nr_local))
            else:
                cur.execute("SELECT SUM(qt_votos) FROM boletim_urna WHERE ano = ? AND nr_votavel = ? AND nr_secao = ?", (ano, nr, nr_secao))
            v_real = cur.fetchone()[0] or 0
            votos_urnas_cand += v_real

            pct = round((v_real / meta * 100), 1) if meta > 0 else 0
            cand_cabos.append({
                "id": cid,
                "nome_cabo": nome_cabo,
                "telefone": tel,
                "local_nome": local_nome,
                "nr_secao": nr_secao,
                "meta_votos": meta,
                "votos_reais": v_real,
                "desempenho_pct": pct,
                "observacao": obs
            })

        tot_meta_global += meta_cand
        tot_votos_urnas_global += votos_urnas_cand
        eficacia_cand = round((votos_urnas_cand / meta_cand * 100), 1) if meta_cand > 0 else 0

        relatorio.append({
            "nr_candidato": nr,
            "nm_candidato": nm,
            "cargo": cg,
            "partido": partido,
            "votos_gerais": votos_gerais,
            "meta_total": meta_cand,
            "votos_urnas_cabos": votos_urnas_cand,
            "eficacia_pct": eficacia_cand,
            "qtd_cabos": len(cand_cabos),
            "cabos": cand_cabos
        })

    conn.close()
    return {
        "ano": ano,
        "tot_candidatos": len(relatorio),
        "tot_cabos": tot_cabos_global,
        "tot_meta_global": tot_meta_global,
        "tot_votos_urnas_global": tot_votos_urnas_global,
        "eficacia_global_pct": round((tot_votos_urnas_global / tot_meta_global * 100), 1) if tot_meta_global > 0 else 0,
        "candidatos": relatorio
    }

# ==========================================
# SERVIDOR HTTP REST & WEB DASHBOARD
# ==========================================

class CanindeRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            response_data = {}
            try:
                if path == "/api/info":
                    response_data = {
                        "municipio": "Canindé de São Francisco",
                        "uf": "SE",
                        "zona": "28ª Zona Eleitoral",
                        "codigo_tse": "31232"
                    }
                elif path == "/api/locais":
                    ano = int(query.get("ano", [2022])[0])
                    locais = list_locais(ano)
                    response_data = [dict(r) for r in locais]
                elif path == "/api/ranking":
                    ano = int(query.get("ano", [2022])[0])
                    cargo = query.get("cargo", ["Deputado Estadual"])[0]
                    local = query.get("local", [None])[0]
                    secao = query.get("secao", [None])[0]
                    top = int(query.get("top", [9])[0])
                    ranking = get_ranking(ano, cargo, local, secao, top)
                    response_data = [dict(r) for r in ranking]
                elif path == "/api/secao":
                    ano = int(query.get("ano", [2022])[0])
                    secao = query.get("secao", ["85"])[0]
                    cargo = query.get("cargo", [None])[0]
                    detalhes = get_secao_detail(ano, secao, cargo)
                    response_data = [dict(r) for r in detalhes]
                elif path == "/api/cabos":
                    ano = int(query.get("ano", [2026])[0])
                    local = query.get("local", [None])[0]
                    secao = query.get("secao", [None])[0]
                    cand = query.get("candidato", [None])[0]
                    cabos = list_cabos(ano, local, secao, cand)
                    response_data = [dict(r) for r in cabos]
                elif path == "/api/relatorio":
                    ano = int(query.get("ano", [2026])[0])
                    cand = query.get("candidato", [None])[0]
                    cargo = query.get("cargo", [None])[0]
                    response_data = get_relatorio_candidatos_cabos(ano, cand, cargo)
                elif path == "/api/data_json":
                    if os.path.exists(JSON_PATH):
                        with open(JSON_PATH, "r", encoding="utf-8") as f:
                            self.wfile.write(f.read().encode("utf-8"))
                        return
                    else:
                        response_data = {"error": "data_caninde.json not found"}
                else:
                    response_data = {"error": f"Endpoint {path} desconhecido"}
            except Exception as e:
                response_data = {"error": str(e)}

            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            response_data = {}
            try:
                data = json.loads(post_body)
                if path == "/api/cabos":
                    cid = add_cabo(
                        ano=int(data.get("ano", 2026)),
                        cargo=data.get("cargo", "Deputado Estadual"),
                        nr_candidato=str(data.get("nr_candidato", "")),
                        nm_candidato=data.get("nm_candidato", ""),
                        nr_local=str(data.get("nr_local", "")),
                        local_nome=data.get("local_nome", ""),
                        nr_secao=str(data.get("nr_secao", "Todas")),
                        nome_cabo=data.get("nome_cabo", ""),
                        telefone=data.get("telefone", ""),
                        observacao=data.get("observacao", ""),
                        meta_votos=int(data.get("meta_votos", 0))
                    )
                    response_data = {"success": True, "id": cid, "message": "Cabo eleitoral cadastrado com sucesso!"}
                elif path == "/api/cabos/delete":
                    cid = int(data.get("id", 0))
                    ok = delete_cabo(cid)
                    response_data = {"success": ok, "message": "Cabo eleitoral removido!" if ok else "Não encontrado"}
                else:
                    response_data = {"error": f"POST {path} não implementado"}
            except Exception as e:
                response_data = {"error": str(e), "success": False}

            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def start_server(port=8088, open_browser=True):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CanindeRequestHandler)
    url = f"http://localhost:{port}/index.html"
    print("=" * 65)
    print(f"[OK] Sistema de Votos Caninde de Sao Francisco (SE)")
    print(f"[URL] Servidor ativo em: {url}")
    print("=" * 65)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor finalizado pelo usuário.")

# ==========================================
# CLI COMMAND LINE
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Análise de Votos por Seção e Local - Canindé de São Francisco (SE)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: serve
    serve_parser = subparsers.add_parser("serve", help="Inicia o painel Web e o servidor da API")
    serve_parser.add_argument("--port", type=int, default=8088, help="Porta HTTP (padrão: 8088)")
    serve_parser.add_argument("--no-browser", action="store_true", help="Não abrir o navegador automaticamente")

    # Comando: locais
    locais_parser = subparsers.add_parser("locais", help="Lista todos os locais de votação e seções")
    locais_parser.add_argument("--ano", type=int, default=2026, choices=[2026, 2024, 2022], help="Ano da eleição")

    # Comando: ranking
    ranking_parser = subparsers.add_parser("ranking", help="Exibe os mais votados (Top X)")
    ranking_parser.add_argument("--ano", type=int, default=2026, choices=[2026, 2024, 2022], help="Ano da eleição")
    ranking_parser.add_argument("--cargo", type=str, default="Deputado Estadual", help="Cargo em disputa")
    ranking_parser.add_argument("--local", type=str, default=None, help="Número do local de votação (ex: 1090 para Agrovila)")
    ranking_parser.add_argument("--secao", type=str, default=None, help="Número da seção eleitoral")
    ranking_parser.add_argument("--top", type=int, default=9, help="Quantidade de candidatos (padrão: 9)")

    # Comando: secao
    secao_parser = subparsers.add_parser("secao", help="Consulta o boletim completo de uma seção")
    secao_parser.add_argument("--ano", type=int, default=2026, choices=[2026, 2024, 2022], help="Ano da eleição")
    secao_parser.add_argument("--secao", type=str, required=True, help="Número da seção eleitoral")
    secao_parser.add_argument("--cargo", type=str, default=None, help="Filtrar por cargo")

    # Comando: export
    export_parser = subparsers.add_parser("export", help="Exporta dados para CSV")
    export_parser.add_argument("--ano", type=int, default=2026, help="Ano da eleição")
    export_parser.add_argument("--output", type=str, default="export_votos_caninde.csv", help="Nome do arquivo CSV")

    # Comando: cabo-add
    cabo_add_parser = subparsers.add_parser("cabo-add", help="Adiciona um cabo eleitoral vinculado a candidato, local e seção")
    cabo_add_parser.add_argument("--nome", type=str, required=True, help="Nome do cabo eleitoral")
    cabo_add_parser.add_argument("--candidato", type=str, required=True, help="Número do candidato")
    cabo_add_parser.add_argument("--nm-candidato", type=str, default="", help="Nome do candidato")
    cabo_add_parser.add_argument("--cargo", type=str, default="Deputado Estadual", help="Cargo")
    cabo_add_parser.add_argument("--local", type=str, required=True, help="Código do local de votação (ex: 1090 para Agrovila)")
    cabo_add_parser.add_argument("--nm-local", type=str, default="", help="Nome amigável do local de votação")
    cabo_add_parser.add_argument("--secao", type=str, default="Todas", help="Seção eleitoral ou 'Todas'")
    cabo_add_parser.add_argument("--telefone", type=str, default="", help="Telefone / WhatsApp")
    cabo_add_parser.add_argument("--meta", type=int, default=0, help="Meta de votos combinada")
    cabo_add_parser.add_argument("--obs", type=str, default="", help="Observação ou bairro")
    cabo_add_parser.add_argument("--ano", type=int, default=2026, help="Ano da eleição")

    # Comando: cabo-list
    cabo_list_parser = subparsers.add_parser("cabo-list", help="Lista todos os cabos eleitorais cadastrados")
    cabo_list_parser.add_argument("--ano", type=int, default=2026, help="Ano da eleição")
    cabo_list_parser.add_argument("--local", type=str, default=None, help="Filtrar por local de votação")
    cabo_list_parser.add_argument("--secao", type=str, default=None, help="Filtrar por seção")
    cabo_list_parser.add_argument("--candidato", type=str, default=None, help="Filtrar por número do candidato")

    # Comando: cabo-del
    cabo_del_parser = subparsers.add_parser("cabo-del", help="Remove um cabo eleitoral pelo ID")
    cabo_del_parser.add_argument("--id", type=int, required=True, help="ID do cabo eleitoral")

    # Comando: relatorio
    rel_parser = subparsers.add_parser("relatorio", help="Gera relatório detalhado agrupado por Candidatos e Cabos Eleitorais")
    rel_parser.add_argument("--ano", type=int, default=2026, help="Ano da eleição")
    rel_parser.add_argument("--candidato", type=str, default=None, help="Filtrar por número do candidato")
    rel_parser.add_argument("--cargo", type=str, default=None, help="Filtrar por cargo")

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        if args.command is None:
            print("Nenhum comando fornecido. Iniciando servidor web padrão...")
            start_server(port=8088, open_browser=True)
        else:
            start_server(port=args.port, open_browser=not args.no_browser)

    elif args.command == "cabo-add":
        cid = add_cabo(
            ano=args.ano, cargo=args.cargo, nr_candidato=args.candidato,
            nm_candidato=args.nm_candidato, nr_local=args.local,
            local_nome=args.nm_local, nr_secao=args.secao,
            nome_cabo=args.nome, telefone=args.telefone,
            observacao=args.obs, meta_votos=args.meta
        )
        print(f"\n[OK] Cabo eleitoral '{args.nome}' cadastrado com sucesso! ID: {cid}")

    elif args.command == "cabo-list":
        rows = list_cabos(args.ano, args.local, args.secao, args.candidato)
        print(f"\n=== CABOS ELEITORAIS CADASTRADOS ({args.ano}) ===")
        print(f"{'ID':<4} | {'Nome do Cabo':<22} | {'Candidato':<20} | {'Local / Colégio':<20} | {'Seção':<7} | {'Telefone':<14} | {'Meta'}")
        print("-" * 105)
        for r in rows:
            cand_str = f"{r['nr_candidato']} - {r['nm_candidato'][:12]}" if r['nm_candidato'] else r['nr_candidato']
            print(f"{r['id']:<4} | {r['nome_cabo'][:20]:<22} | {cand_str:<20} | {r['local_nome'][:18]:<20} | {r['nr_secao']:<7} | {r['telefone']:<14} | {r['meta_votos']}")

    elif args.command == "cabo-del":
        ok = delete_cabo(args.id)
        if ok:
            print(f"[OK] Cabo eleitoral ID {args.id} removido com sucesso!")
        else:
            print(f"[ERRO] Cabo eleitoral ID {args.id} não encontrado.")

    elif args.command == "relatorio":
        rel = get_relatorio_candidatos_cabos(args.ano, args.candidato, args.cargo)
        print(f"\n" + "=" * 95)
        print(f"RELATÓRIO DE CAMPANHA: CANDIDATOS E CABOS ELEITORAIS ({args.ano})")
        print(f"Canindé de São Francisco • 28ª Zona Eleitoral")
        print(f"Candidatos: {rel['tot_candidatos']} | Cabos Ativos: {rel['tot_cabos']} | Meta Total: {rel['tot_meta_global']} | Votos nas Urnas: {rel['tot_votos_urnas_global']} ({rel['eficacia_global_pct']}%)")
        print("=" * 95 + "\n")
        
        for c in rel["candidatos"]:
            print(f">>> CANDIDATO: {c['nm_candidato']} (Nº {c['nr_candidato']}) - {c['cargo']} - {c['partido']}")
            print(f"    Votos Totais Canindé: {c['votos_gerais']} | Cabos: {c['qtd_cabos']} | Meta: {c['meta_total']} | Real Urnas: {c['votos_urnas_cabos']} ({c['eficacia_pct']}% atingido)")
            print(f"    {'Nome do Cabo':<24} | {'WhatsApp / Tel':<15} | {'Local / Colégio':<26} | {'Seção':<7} | {'Meta':<5} | {'Real':<5} | {'% Ating.'}")
            print(f"    " + "-" * 92)
            for cabo in c["cabos"]:
                print(f"    {cabo['nome_cabo'][:22]:<24} | {cabo['telefone']:<15} | {cabo['local_nome'][:24]:<26} | {cabo['nr_secao']:<7} | {cabo['meta_votos']:<5} | {cabo['votos_reais']:<5} | {cabo['desempenho_pct']}%")
            print()

    elif args.command == "locais":
        rows = list_locais(args.ano)
        print(f"\n=== LOCAIS DE VOTAÇÃO DE CANINDÉ DE SÃO FRANCISCO ({args.ano}) ===")
        print(f"{'Cód':<6} | {'Nome Popular / Caderno':<25} | {'Colégio Oficial':<38} | {'Seções'}")
        print("-" * 105)
        for r in rows:
            print(f"{r['nr_local']:<6} | {r['apelido']:<25} | {r['nome'][:36]:<38} | {r['secoes']}")

    elif args.command == "ranking":
        rows = get_ranking(args.ano, args.cargo, args.local, args.secao, args.top)
        loc_str = f"Local {args.local}" if args.local else ("Seção " + args.secao if args.secao else "Geral do Município")
        cargo_title = "Todos os Cargos" if args.cargo in ("ALL", "Todos") else args.cargo
        print(f"\n=== TOP {args.top} MAIS VOTADOS: {cargo_title} ({args.ano}) - {loc_str} ===")
        print(f"{'#':<3} | {'Nº':<6} | {'Nome do Candidato':<28} | {'Cargo':<20} | {'Partido':<10} | {'Votos'}")
        print("-" * 85)
        for idx, r in enumerate(rows, 1):
            cargo_r = r['cargo'] if 'cargo' in r.keys() else args.cargo
            print(f"{idx:<3} | {r['nr_votavel']:<6} | {r['nm_votavel'][:28]:<28} | {cargo_r:<20} | {r['partido_sg']:<10} | {r['total_votos']}")

    elif args.command == "secao":
        rows = get_secao_detail(args.ano, args.secao, args.cargo)
        print(f"\n=== BOLETIM DE URNA: SEÇÃO {args.secao} ({args.ano}) ===")
        print(f"{'Cargo':<20} | {'Nº':<6} | {'Nome':<28} | {'Partido':<10} | {'Tipo':<8} | {'Votos'}")
        print("-" * 85)
        for r in rows:
            print(f"{r['cargo']:<20} | {r['nr_votavel']:<6} | {r['nm_votavel']:<28} | {r['partido_sg']:<10} | {r['tipo_votavel']:<8} | {r['qt_votos']}")

    elif args.command == "export":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT b.ano, b.cargo, b.nr_secao, b.nr_local, l.apelido as local_nome,
                   b.nr_votavel, b.nm_votavel, b.partido_sg, b.tipo_votavel, b.qt_votos
            FROM boletim_urna b
            LEFT JOIN locais l ON b.nr_local = l.nr_local AND b.ano = l.ano
            WHERE b.ano = ?
            ORDER BY b.cargo, CAST(b.nr_secao AS INTEGER), b.qt_votos DESC
        """, (args.ano,))
        rows = cur.fetchall()
        import csv
        with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Ano", "Cargo", "Secao", "Cod_Local", "Local_Votacao", "Numero", "Candidato", "Partido", "Tipo", "Votos"])
            for r in rows:
                writer.writerow(list(r))
        conn.close()
        print(f"Exportado com sucesso para {args.output}")

if __name__ == "__main__":
    main()
