import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "caninde_votos.db")
JSON_PATH = os.path.join(BASE_DIR, "data_caninde.json")
JS_PATH = os.path.join(BASE_DIR, "data_caninde.js")

def export_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Locais
    locais = {}
    for r in cur.execute("SELECT nr_local, ano, nome, bairro, apelido FROM locais ORDER BY nr_local, ano"):
        nr, ano, nome, bairro, apelido = r
        if nr not in locais:
            locais[nr] = {
                "nr_local": nr,
                "nome": nome,
                "bairro": bairro,
                "apelido": apelido,
                "secoes_2022": [],
                "secoes_2024": [],
                "secoes_2026": []
            }
        else:
            # Atualiza nome e apelido mais recentes
            locais[nr]["nome"] = nome
            locais[nr]["bairro"] = bairro
            locais[nr]["apelido"] = apelido

    # Secoes por local
    for r in cur.execute("SELECT ano, nr_secao, nr_local FROM secoes_locais ORDER BY ano, CAST(nr_secao AS INTEGER)"):
        ano, secao, nr = r
        if nr in locais:
            key = f"secoes_{ano}"
            if key not in locais[nr]:
                locais[nr][key] = []
            if secao not in locais[nr][key]:
                locais[nr][key].append(secao)
                
    # Totais por local e cargo
    totais_locais = {}
    for r in cur.execute("""
        SELECT ano, turno, cargo, nr_local, sum(qt_aptos), sum(qt_comparecimento), sum(qt_abstencoes)
        FROM totais_secao
        GROUP BY ano, turno, cargo, nr_local
    """):
        ano, turno, cargo, nr_local, aptos, comp, abst = r
        k = f"{ano}_{turno}_{cargo}_{nr_local}"
        totais_locais[k] = {"aptos": aptos, "comparecimento": comp, "abstencoes": abst}

    # Candidatos por cargo e ano (Geral do Município)
    candidatos_geral = {}
    for r in cur.execute("""
        SELECT ano, turno, cargo, nr_votavel, nm_votavel, partido_sg, tipo_votavel, sum(qt_votos) as total
        FROM boletim_urna
        GROUP BY ano, turno, cargo, nr_votavel, nm_votavel, partido_sg, tipo_votavel
        ORDER BY ano, cargo, total DESC
    """):
        ano, turno, cargo, nr_vot, nm_vot, partido, tipo, total = r
        k = f"{ano}_{turno}_{cargo}"
        if k not in candidatos_geral:
            candidatos_geral[k] = []
        candidatos_geral[k].append({
            "nr": nr_vot,
            "nome": nm_vot,
            "partido": partido,
            "tipo": tipo,
            "votos": total
        })

    # Candidatos por Local de Votação
    candidatos_por_local = {}
    for r in cur.execute("""
        SELECT ano, turno, cargo, nr_local, nr_votavel, nm_votavel, partido_sg, sum(qt_votos) as total
        FROM boletim_urna
        WHERE tipo_votavel = 'Nominal'
        GROUP BY ano, turno, cargo, nr_local, nr_votavel, nm_votavel, partido_sg
        ORDER BY ano, cargo, nr_local, total DESC
    """):
        ano, turno, cargo, nr_local, nr_vot, nm_vot, partido, total = r
        k = f"{ano}_{turno}_{cargo}_{nr_local}"
        if k not in candidatos_por_local:
            candidatos_por_local[k] = []
        candidatos_por_local[k].append({
            "nr": nr_vot,
            "nome": nm_vot,
            "partido": partido,
            "votos": total
        })

    # Votos por Seção Eleitoral
    votos_por_secao = {}
    for r in cur.execute("""
        SELECT ano, turno, cargo, nr_secao, nr_local, nr_votavel, nm_votavel, partido_sg, tipo_votavel, qt_votos
        FROM boletim_urna
        ORDER BY ano, cargo, CAST(nr_secao AS INTEGER), qt_votos DESC
    """):
        ano, turno, cargo, secao, nr_local, nr_vot, nm_vot, partido, tipo, votos = r
        k = f"{ano}_{turno}_{cargo}_{secao}"
        if k not in votos_por_secao:
            votos_por_secao[k] = {
                "ano": ano,
                "turno": turno,
                "cargo": cargo,
                "secao": secao,
                "nr_local": nr_local,
                "votos": []
            }
        votos_por_secao[k]["votos"].append({
            "nr": nr_vot,
            "nome": nm_vot,
            "partido": partido,
            "tipo": tipo,
            "qtd": votos
        })

    data = {
        "municipio": "Canindé de São Francisco",
        "uf": "SE",
        "codigo_tse": "31232",
        "zona": "28ª Zona Eleitoral",
        "locais": locais,
        "totais_locais": totais_locais,
        "candidatos_geral": candidatos_geral,
        "candidatos_por_local": candidatos_por_local,
        "votos_por_secao": votos_por_secao
    }
    
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        
    with open(JS_PATH, "w", encoding="utf-8") as f:
        f.write("window.CANINDE_DATA = " + json.dumps(data, ensure_ascii=False) + ";")
        
    print(f"Exported JSON ({os.path.getsize(JSON_PATH)} bytes) and JS ({os.path.getsize(JS_PATH)} bytes) successfully!")
    conn.close()

if __name__ == '__main__':
    export_all()
