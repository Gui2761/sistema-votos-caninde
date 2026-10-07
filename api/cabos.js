// In-memory store fallback across serverless container invocations
if (!globalThis.__CABOS_MEM_STORE__) {
  globalThis.__CABOS_MEM_STORE__ = [];
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  const kvUrl = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const kvToken = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

  async function getFromKV() {
    if (!kvUrl || !kvToken) {
      return globalThis.__CABOS_MEM_STORE__ || [];
    }
    try {
      // 1. Comando oficial Upstash Redis REST: ["GET", "key"]
      const resp = await fetch(kvUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${kvToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(["GET", "cabos_caninde_2026"])
      });
      const json = await resp.json();
      if (json && json.result !== undefined && json.result !== null) {
        return typeof json.result === "string" ? JSON.parse(json.result) : json.result;
      }

      // 2. Fallback rota /get/key
      const respAlt = await fetch(`${kvUrl}/get/cabos_caninde_2026`, {
        headers: { Authorization: `Bearer ${kvToken}` }
      });
      const jsonAlt = await respAlt.json();
      if (jsonAlt && jsonAlt.result !== undefined && jsonAlt.result !== null) {
        return typeof jsonAlt.result === "string" ? JSON.parse(jsonAlt.result) : jsonAlt.result;
      }
      return globalThis.__CABOS_MEM_STORE__ || [];
    } catch (e) {
      return globalThis.__CABOS_MEM_STORE__ || [];
    }
  }

  async function saveToKV(lista) {
    const arr = Array.isArray(lista) ? [...lista] : [];
    globalThis.__CABOS_MEM_STORE__ = arr;
    if (!kvUrl || !kvToken) return true;
    try {
      const dataStr = JSON.stringify(arr);
      // 1. Comando oficial Upstash Redis REST: ["SET", "key", "value"]
      await fetch(kvUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${kvToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(["SET", "cabos_caninde_2026", dataStr])
      });
      // 2. Fallback rota /set/key
      await fetch(`${kvUrl}/set/cabos_caninde_2026`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${kvToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(dataStr)
      }).catch(() => {});
      return true;
    } catch (e) {
      return false;
    }
  }

  if (req.method === "GET") {
    let cabos = await getFromKV();
    if (!cabos || !Array.isArray(cabos)) {
      cabos = globalThis.__CABOS_MEM_STORE__ || [];
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
      cabos = [];
    }

    // Suporte a substituição/sincronização autoritativa (replace_all)
    if (body.acao === "replace_all" && Array.isArray(body.cabos)) {
      cabos = body.cabos;
      await saveToKV(cabos);
      return res.status(200).json({ status: "ok", count: cabos.length });
    }

    // Suporte a importação/sincronização em lote (Array de cabos)
    if (Array.isArray(body)) {
      const map = new Map();
      cabos.forEach(c => map.set(c.id, c));
      body.forEach(c => map.set(c.id, c));
      cabos = Array.from(map.values());
      await saveToKV(cabos);
      return res.status(200).json({ status: "ok", count: cabos.length });
    }

    // Exclusão de cabo
    const isDelete = (req.url && req.url.includes("delete")) || body.acao === "delete" || (body.id && Object.keys(body).length <= 2);
    if (isDelete) {
      const delId = String(body.id);
      cabos = cabos.filter(c => String(c.id) !== delId);
      await saveToKV(cabos);
      return res.status(200).json({ status: "ok", deleted: delId, total: cabos.length });
    }

    // Novo cabo ou atualização
    const novo = {
      id: body.id || Date.now(),
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

    const idx = cabos.findIndex(c => c.id === novo.id);
    if (idx >= 0) {
      cabos[idx] = novo;
    } else {
      cabos.unshift(novo);
    }
    await saveToKV(cabos);
    return res.status(200).json({ status: "ok", id: novo.id });
  }

  return res.status(405).json({ error: "Method not allowed" });
}
