// api/cabos.js - Vercel Serverless Function para Gestão de Cabos de Canindé de São Francisco
// Suporta persistência automática na nuvem com Vercel KV (Redis) ou fallback instantâneo com base oficial

const CABOS_OFICIAIS = [
  { id: 1, ano: 2026, cargo: "Deputado Estadual", nr_candidato: "44111", nm_candidato: "MARCELO OLIVEIRA SOBRAL", nr_local: "1090", local_nome: "Escola Municipal Agrovila", nr_secao: "85", nome_cabo: "Severino da Silva (Biu)", telefone: "(79) 99881-2233", meta_votos: 50, observacao: "Liderança central no Povoado Agrovila" },
  { id: 2, ano: 2026, cargo: "Deputado Estadual", nr_candidato: "44111", nm_candidato: "MARCELO OLIVEIRA SOBRAL", nr_local: "1112", local_nome: "EMEF Maria do Carmo", nr_secao: "1", nome_cabo: "Dona Raimunda Santos", telefone: "(79) 99912-3344", meta_votos: 45, observacao: "Coordenação de mobilização no Centro" },
  { id: 3, ano: 2026, cargo: "Deputado Estadual", nr_candidato: "44000", nm_candidato: "LIDIANE CECÍLIA LUCENA", nr_local: "1090", local_nome: "Escola Municipal Agrovila", nr_secao: "94", nome_cabo: "Marcos Antônio de Jesus", telefone: "(79) 99877-4455", meta_votos: 35, observacao: "Apoio comunitário Bloco B" },
  { id: 4, ano: 2026, cargo: "Deputado Federal", nr_candidato: "4444", nm_candidato: "YANDRA BARRETO FERREIRA", nr_local: "1031", local_nome: "EMEF Domingos Gerônimo", nr_secao: "3", nome_cabo: "Cláudio do Capim Grosso", telefone: "(79) 99122-8899", meta_votos: 80, observacao: "Mobilizador regional Capim Grosso" },
  { id: 5, ano: 2026, cargo: "Governador", nr_candidato: "55", nm_candidato: "FABIO CRUZ MITIDIERI", nr_local: "1023", local_nome: "Colégio Estadual Delmiro Gouveia", nr_secao: "53", nome_cabo: "José Carlos (Zé do Posto)", telefone: "(79) 98833-1122", meta_votos: 100, observacao: "Articulador comercial Bairro Olaria" },
  { id: 6, ano: 2026, cargo: "Senador", nr_candidato: "131", nm_candidato: "ROGERIO CARVALHO SANTOS", nr_local: "1015", local_nome: "Escola Estadual Dom Juvêncio", nr_secao: "9", nome_cabo: "Professora Rita de Cássia", telefone: "(79) 99655-4433", meta_votos: 70, observacao: "Movimento Educação e Assentamentos" }
];

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  const kvUrl = process.env.KV_REST_API_URL;
  const kvToken = process.env.KV_REST_API_TOKEN;

  async function getFromKV() {
    if (!kvUrl || !kvToken) return null;
    try {
      const resp = await fetch(`${kvUrl}/get/cabos_caninde_2026`, {
        headers: { Authorization: `Bearer ${kvToken}` }
      });
      const json = await resp.json();
      if (json && json.result) {
        return typeof json.result === "string" ? JSON.parse(json.result) : json.result;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  async function saveToKV(lista) {
    if (!kvUrl || !kvToken) return false;
    try {
      await fetch(`${kvUrl}/set/cabos_caninde_2026`, {
        method: "POST",
        headers: { Authorization: `Bearer ${kvToken}`, "Content-Type": "application/json" },
        body: JSON.stringify(JSON.stringify(lista))
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  if (req.method === "GET") {
    let cabos = await getFromKV();
    if (!cabos || !Array.isArray(cabos) || cabos.length === 0) {
      cabos = CABOS_OFICIAIS;
      await saveToKV(cabos);
    }
    const ano = parseInt(req.query ? req.query.ano : 2026) || 2026;
    const filtrados = cabos.filter(c => !c.ano || c.ano === ano);
    return res.status(200).json(filtrados);
  }

  if (req.method === "POST") {
    let body = req.body;
    if (typeof body === "string") {
      try { body = JSON.parse(body); } catch (e) {}
    }
    body = body || {};

    let cabos = await getFromKV();
    if (!cabos || !Array.isArray(cabos)) {
      cabos = CABOS_OFICIAIS;
    }

    // Exclusão de cabo
    const isDelete = (req.url && req.url.includes("delete")) || body.acao === "delete" || (body.id && Object.keys(body).length <= 2);
    if (isDelete) {
      const delId = body.id;
      cabos = cabos.filter(c => c.id !== delId);
      await saveToKV(cabos);
      return res.status(200).json({ status: "ok", deleted: delId });
    }

    // Novo cabo
    const novo = {
      id: Date.now(),
      ano: parseInt(body.ano) || 2026,
      cargo: body.cargo || "",
      nr_candidato: String(body.nr_candidato || ""),
      nm_candidato: body.nm_candidato || "",
      nr_local: String(body.nr_local || ""),
      local_nome: body.local_nome || "",
      nr_secao: String(body.nr_secao || "Todas"),
      nome_cabo: body.nome_cabo || "",
      telefone: body.telefone || "",
      meta_votos: parseInt(body.meta_votos) || 0,
      observacao: body.observacao || ""
    };

    cabos.unshift(novo);
    await saveToKV(cabos);
    return res.status(200).json({ status: "ok", id: novo.id });
  }

  return res.status(405).json({ error: "Method not allowed" });
}
