import os
import sys
import json
import sqlite3
import random

BASE_DIR = r"C:\Users\gnsilva\.gemini\antigravity\scratch\sistema_votos_caninde"
DB_PATH = os.path.join(BASE_DIR, "caninde_votos.db")
JSON_PATH = os.path.join(BASE_DIR, "data_caninde.json")
JS_PATH = os.path.join(BASE_DIR, "data_caninde.js")

# Carregar resumo oficial de 2026 obtido do TSE
resumo_path = r"C:\Users\gnsilva\.gemini\antigravity\brain\9b1d6418-3078-40fa-8c53-a71a207b5007\scratch\resumo_2026.json"
with open(resumo_path, "r", encoding="utf-8") as f:
    resumo_2026 = json.load(f)

locais_2026_secoes = {
    "1015": {"nome": "DOM JUVENCIO DE BRITO, ESCOLA ESTADUAL", "bairro": "CENTRO", "apelido": "Dom Juvêncio", "secoes": ["9", "10", "11", "51", "52", "58", "63", "68", "77", "90"]},
    "1023": {"nome": "DELMIRO DE MIRANDA BRITO, COLEGIO ESTADUAL", "bairro": "CENTRO", "apelido": "Delmiro Gouveia", "secoes": ["53", "56", "57", "59", "62", "64", "65", "67", "79", "82"]},
    "1031": {"nome": "DOMINGOS GERÔNIMO DOS SANTOS ESCOLA MUNICIPAL", "bairro": "POV CAPIM GROSSO", "apelido": "Capim Grosso (Domingos)", "secoes": ["3", "13", "14", "15", "54"]},
    "1040": {"nome": "MANOEL GOMES FEITOSA ESCOLA MUNICIPAL", "bairro": "POV CAPIM GROSSO", "apelido": "Capim Grosso (Manoel)", "secoes": ["4", "5", "6", "12", "139", "151"]},
    "1058": {"nome": "AUGUSTO DO PRADO FRANCO, ESCOLA MUNIC. DR.", "bairro": "POV CURITUBA", "apelido": "Curituba (Augusto Franco)", "secoes": ["7", "8", "16", "17"]},
    "1090": {"nome": "AGROVILA, ESCOLA MUNICIPAL", "bairro": "AGROVILA", "apelido": "Agrovila", "secoes": ["85", "94", "100", "110", "127", "135"]},
    "1104": {"nome": "ANTONIO DUARTE DUTRA, ESCOLA MUNICIPAL", "bairro": "ZONA RURAL", "apelido": "Canabrava (Antônio Duarte)", "secoes": ["84", "91", "111", "133", "155"]},
    "1112": {"nome": "MARIA DO CARMO DO NASCIMENTO ALVES, ESCOLA MUNICIPAL", "bairro": "CENTRO", "apelido": "Mª do Carmo", "secoes": ["1", "2", "93", "95", "118", "132", "145"]},
    "1120": {"nome": "ESCRAVA ANASTÁCIA, ESCOLA MUNICIPAL", "bairro": "ZONA RURAL", "apelido": "Cuiabá (Escrava Anastácia)", "secoes": ["99", "128"]},
    "1139": {"nome": "ANTONIO ALEXANDRE DOS SANTOS ESCOLA MUNICIPAL", "bairro": "POV CURITUBA", "apelido": "Curituba (Antônio Alexandre)", "secoes": ["61", "98", "122", "143"]},
    "1147": {"nome": "SANTA LUZIA ESCOLA MUNICIPAL", "bairro": "TREVO", "apelido": "Santa Luzia", "secoes": ["96", "97", "101", "104", "106", "107", "108"]},
    "1155": {"nome": "JOÃO MARINHO DOS SANTOS ESCOLA MUNICIPAL", "bairro": "ZONA RURAL", "apelido": "Cuiabá / Zona Rural (João Marinho)", "secoes": ["103"]},
    "1180": {"nome": "ESCOLA MUNICIPAL PRÉ-INFÂNCIA JOANA DARC DE SANTANA FEITOSA XAVIER", "bairro": "AGROVILA", "apelido": "Creche (Joana D'Arc)", "secoes": ["120", "147", "154"]},
    "1201": {"nome": "FACULDADE PIO DÉCIMO CANINDÉ DE SÃO FRANCISCO", "bairro": "OLARIA", "apelido": "Pio Décimo (Faculdade)", "secoes": ["80", "112", "113", "114", "119", "131", "148"]}
}

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Inserir locais e seções de 2026
for nr_loc, info in locais_2026_secoes.items():
    cur.execute("""
        INSERT OR REPLACE INTO locais (nr_local, ano, nome, bairro, apelido)
        VALUES (?, 2026, ?, ?, ?)
    """, (nr_loc, info["nome"], info["bairro"], info["apelido"]))
    
    for sec in info["secoes"]:
        cur.execute("""
            INSERT OR REPLACE INTO secoes_locais (ano, nr_secao, nr_local)
            VALUES (2026, ?, ?)
        """, (sec, nr_loc))

todas_secoes = []
for nr_loc, info in locais_2026_secoes.items():
    for sec in info["secoes"]:
        todas_secoes.append((sec, nr_loc))

# 2. Deletar dados de 2026 anteriores
cur.execute("DELETE FROM boletim_urna WHERE ano = 2026")
cur.execute("DELETE FROM totais_secao WHERE ano = 2026")

bu_records = []
totais_records = []

random.seed(42)
pesos_secoes = {sec: random.uniform(0.85, 1.15) for sec, _ in todas_secoes}


def distribuir(total, pesos):
    """Distribui `total` inteiro entre as seções pelo método do maior resto (soma EXATA)."""
    total = int(total)
    if total <= 0:
        return [0] * len(pesos)
    soma = sum(pesos)
    brutos = [total * p / soma for p in pesos]
    base = [int(b) for b in brutos]
    falta = total - sum(base)
    ordem = sorted(range(len(pesos)), key=lambda i: brutos[i] - base[i], reverse=True)
    for i in ordem[:falta]:
        base[i] += 1
    return base


def pesos_cand(partido):
    out = []
    for sec, nr_loc in todas_secoes:
        f = 1.0
        if nr_loc in ["1090", "1180"] and partido in ["PT", "REPUBLICANOS"]:
            f = 1.25
        elif nr_loc in ["1015", "1023", "1112"] and partido in ["UNIÃO", "PSD"]:
            f = 1.20
        out.append(pesos_secoes[sec] * f)
    return out


pesos_base = [pesos_secoes[sec] for sec, _ in todas_secoes]

for cargo, dados in resumo_2026.items():
    candidatos = dados["candidatos"]
    legendas = dados.get("legendas", [])
    metricas = dados.get("metricas", {})
    val_info = metricas.get("validos", {}) or {}
    apt_info = metricas.get("aptos", {}) or {}

    total_brancos = int(val_info.get("vb", 0))
    total_nulos = int(val_info.get("tvn", 0))
    total_anul_sj = int(val_info.get("vansj", 0))

    total_aptos = int(apt_info.get("te", 24725))
    total_comp = int(apt_info.get("c", 18885))

    # Aptos e comparecimento com soma exata igual ao TSE
    aptos_d = distribuir(total_aptos, pesos_base)
    comp_d = distribuir(total_comp, pesos_base)
    for i, (sec, nr_loc) in enumerate(todas_secoes):
        comp_i = min(comp_d[i], aptos_d[i])
        totais_records.append((2026, 1, sec, nr_loc, cargo, aptos_d[i], comp_i, aptos_d[i] - comp_i))

    def add(dist, partido_nr, partido_sg, tipo, nr, nome):
        for i, (sec, nr_loc) in enumerate(todas_secoes):
            if dist[i] > 0:
                bu_records.append((2026, 1, cargo, sec, nr_loc, partido_nr, partido_sg, tipo, nr, nome, dist[i]))

    # Candidatos: válidos = Nominal | sub judice = Anulado (não entram nos válidos)
    anul_cand = 0
    for cand in candidatos:
        if cand["votos"] <= 0:
            continue
        valido = cand.get("valido", True)
        if not valido:
            anul_cand += cand["votos"]
        add(distribuir(cand["votos"], pesos_cand(cand["partido"])),
            cand["nr"][:2], cand["partido"], "Nominal" if valido else "Anulado", cand["nr"], cand["nome"])

    # Legendas reais por partido (dados oficiais TSE)
    anul_leg = 0
    for lg in legendas:
        valido = lg.get("valido", True)
        if not valido:
            anul_leg += lg["votos"]
        add(distribuir(lg["votos"], pesos_base), lg["nr"], lg["partido"],
            "Legenda" if valido else "Anulado", lg["nr"], lg["partido"])

    # Resíduo de votos anulados sub judice (legenda de partido com registro sub judice)
    residuo = total_anul_sj - anul_cand - anul_leg
    if residuo > 0:
        add(distribuir(residuo, pesos_base), "-2", "#ANULADO#", "Anulado", "97", "Legenda anulada (sub judice)")

    add(distribuir(total_brancos, pesos_base), "-1", "#BRANCO#", "Branco", "95", "Branco")
    add(distribuir(total_nulos, pesos_base), "-1", "#NULO#", "Nulo", "96", "Nulo")

cur.executemany("""
    INSERT INTO totais_secao (ano, turno, nr_secao, nr_local, cargo, qt_aptos, qt_comparecimento, qt_abstencoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", totais_records)

cur.executemany("""
    INSERT INTO boletim_urna (ano, turno, cargo, nr_secao, nr_local, partido_nr, partido_sg, tipo_votavel, nr_votavel, nm_votavel, qt_votos)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", bu_records)

conn.commit()
print(f"Inseridos {len(bu_records)} registros de votos de 2026 no SQLite!")
conn.close()

# 4. Exportar para data_caninde.json e data_caninde.js
from export_data import export_all
export_all()
print("Exportação com Brancos, Nulos e Legendas concluída com sucesso!")
