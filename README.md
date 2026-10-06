# 🗳️ Sistema de Apuração e Mapa de Votos — Canindé de São Francisco (SE)
> **28ª Zona Eleitoral de Sergipe • Código TSE do Município: 31232**  
> *Orquestrado no Ecossistema Master Skill (BMad Method, Spec-Kit & Antigravity Kit)*

---

## 📌 Visão Geral do Projeto

Este sistema foi desenvolvido sob demanda para responder com rigor científico e máxima precisão aos requisitos levantados a partir do mapa eleitoral manuscrito do município de **Canindé de São Francisco / SE**.

O sistema integra dados oficiais de **Boletins de Urna (BU)** e do cadastro de **Locais de Votação e Seções** do Tribunal Superior Eleitoral (TSE), cobrindo:
- **Eleições Gerais 2022**: Deputado Estadual, Deputado Federal, Governador, Senador e Presidente.
- **Eleições Municipais 2024**: Prefeito e Vereador.

---

## 🗺️ Mapeamento dos 11 Locais do Caderno para os Dados Oficiais do TSE

| # | Local Anotado no Caderno | Código TSE | Nome Oficial do Estabelecimento | Bairro / Povoado | Seções Eleitorais Vinculadas |
|---|---|---|---|---|---|
| 1 | **AGROVILA** | `1090` | Escola Municipal Agrovila | Bairro Agrovila | 85, 94, 100, 110, 127, 135, 147 |
| 2 | **Mª DO CARMO** | `1112` | EMEF Maria do Carmo do Nascimento Alves | Centro | 1, 2, 93, 95, 118, 132, 145 |
| 3 | **DELMIRO** | `1023` | Colégio Estadual Delmiro de Miranda Brito | Centro | 53, 56, 57, 59, 62, 64, 65, 67, 79, 80, 82 |
| 4 | **DOM JUVÊNCIO** | `1015` | Escola Estadual Dom Juvêncio de Britto | Centro | 9, 10, 11, 51, 52, 58, 63, 68, 77, 90 |
| 5 | **SANTA LUZIA** | `1147` | Escola Municipal Santa Luzia | Trevo | 96, 97, 101, 104, 106, 107, 108 |
| 6 | **PIO DÉCIMO** | `1171 / 1201` | Colégio Pio Décimo / Faculdade Pio Décimo | Olaria | 112, 113, 114, 119, 131 (+80, 148) |
| 7 | **CRECHE** | `1180 / 1198` | EMEF Pré-Infância Joana D'Arc de S. Feitosa Xavier | Agrovila | 120, 147, 154 |
| 8 | **CAPIM GROSSO** | `1031 / 1040` | EMEF Domingos Gerônimo & EMEF Manoel Gomes Feitosa | Povoado Capim Grosso | 3, 4, 5, 6, 12, 13, 14, 15, 54, 139, 151 |
| 9 | **CURITUBA** | `1058 / 1139` | EMEF Dr. Augusto do Prado Franco & EMEF Antônio Alexandre | Povoado Curituba | 7, 8, 16, 17, 61, 98, 122, 143 |
| 10 | **CANABRAVA / CANABÁ** | `1104` | EMEF Antônio Duarte Dutra | Povoado Canabrava / Zona Rural | 84, 91, 111, 133, 155 |
| 11 | **CUIABÁ** | `1120 / 1155` | EMEF Escrava Anastácia & EMEF João Marinho dos Santos | Povoado Cuiabá / Zona Rural | 99, 103, 128 |

---

## 🚀 Como Executar o Sistema

### 1. Painel Web Interativo (Dashboard Completo)
Você pode abrir o painel de duas formas simples:

#### Opção A (Direto no Navegador — Sem dependências):
Basta dar **duplo clique** no arquivo `index.html` na pasta do projeto!
Ele carrega imediatamente todos os dados, gráficos, filtros e relatórios.

#### Opção B (Servidor Local Integrado - Acesso no PC e no Celular):
Abra o terminal na pasta do projeto e execute:
```bash
python caninde_votos.py serve --port 8088
```
- **No Computador:** Abra no navegador: [http://localhost:8088/index.html](http://localhost:8088/index.html)
- **No Celular (mesmo Wi-Fi):** Abra no navegador do seu smartphone: `http://172.23.6.112:8088/index.html`

### 📱 Experiência Mobile-First no Celular
- **Barra de Navegação Inferior (App Native Style):** Acesse Ranking, Seções, 11 Locais, Cabos e Dobradinhas na ponta do polegar.
- **Chips Rápidos de Cargos:** Alterne entre Estadual, Federal, Governador, Senador e Presidente com um toque.
- **Filtros Inteligentes Recolhíveis:** Barra compacta que não ocupa a tela do celular.
- **Botão Flutuante (+ Cabo):** Cadastre lideranças de qualquer tela com gaveta estilo Bottom Sheet.
- **Botão Direto de WhatsApp:** Dispare conversas com cabos eleitorais diretamente no app do WhatsApp.

---

### 2. Gestão de Cabos Eleitorais & Lideranças
```bash
# Adicionar cabo eleitoral
python caninde_votos.py cabo-add --nome "Severino da Agrovila" --candidato "44111" --local "1090" --secao "85" --meta 50 --telefone "79998887766"

# Listar cabos cadastrados
python caninde_votos.py cabo-list --ano 2026

# Remover cabo por ID
python caninde_votos.py cabo-del --id 1
```

---

### 3. Consultas Rápidas via Linha de Comando (CLI)

#### Listar os mais votados (Top 9) para Deputado Estadual:
```bash
python caninde_votos.py ranking --ano 2026 --cargo "Deputado Estadual" --local 1090 --top 9
```

#### Listar os mais votados para Deputado Federal no Geral de Canindé:
```bash
python caninde_votos.py ranking --ano 2026 --cargo "Deputado Federal" --top 9
```

#### Consultar o Boletim de Urna de uma Seção específica:
```bash
python caninde_votos.py secao --ano 2026 --secao 85 --cargo "Deputado Estadual"
```

#### Listar todos os Locais de Votação e suas respectivas Seções:
```bash
python caninde_votos.py locais --ano 2026
```

#### Exportar todos os dados para CSV (compatível com Excel):
```bash
python caninde_votos.py export --ano 2026 --output votos_caninde_2026.csv
```
---

## 🖨️ Relatório Oficial & Dossiê A4 (Cartorial)
- **Cabeçalho Timbrado Oficial:** Brasão da República Federativa do Brasil, 28ª Zona Eleitoral TRE-SE (Canindé de São Francisco, Cód. 31232).
- **Metadados de Auditoria:** Carimbo de data/hora oficial e protocolo único rastreável.
- **Quadro Macro de Indicadores:** 24.725 eleitores aptos, total de candidatos, cabos ativos, metas e urnas com eficácia calculada.
- **Anti-quebra A4:** Normas `@page { size: A4 portrait; margin: 10mm 12mm; }`, tabelas com `break-inside: avoid` e repetição de cabeçalhos.
- **Termo de Homologação:** Espaço formal de assinatura para a *Coordenação Geral de Campanha* e *Coordenação de Mobilização e Território*.

---

## 🌐 Deploy no Vercel & GitHub

O projeto é 100% autossuficiente e compatível com hospedagem estática de alta velocidade no Vercel:
- **GitHub:** Repositório sincronizado com CI/CD.
- **Vercel:** `vercel.json` pré-configurado com roteamento limpo e suporte a PWA/Mobile.
- **Armazenamento Híbrido:** Persistência em SQLite local e sincronização automática via `localStorage` no navegador para uso em qualquer dispositivo.

---

## 🏗️ Estrutura de Arquivos

```
sistema_votos_caninde/
├── index.html            # Dashboard Web Mobile-First, responsivo e Dossiê A4
├── caninde_votos.py      # Servidor HTTP REST (porta 8088) e ferramenta CLI em Python
├── caninde_votos.db      # Banco de dados SQLite indexado (11.159 registros + cabos)
├── data_caninde.json     # Dataset consolidado em formato JSON
├── data_caninde.js       # Script com dados embutidos (garante abertura off-line direta)
├── vercel.json           # Configuração de deploy no Vercel
├── .gitignore            # Regras de exclusão de arquivos temporários
└── README.md             # Esta documentação
```


