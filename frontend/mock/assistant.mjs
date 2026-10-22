// Asistente IA para el prestamista — endpoints de mercado, noticias y chat.
// Motor híbrido: reglas locales (gratis) + LLM opcional si OPENAI_API_KEY está seteado.
// Datos reales (CoinGecko, Yahoo Finance, Bluelytics, RSS) cacheados en memoria.

const marketCache = { data: null, at: 0 };
const newsCache = { data: null, at: 0 };
const MARKET_TTL = 60 * 1000;
const NEWS_TTL = 5 * 60 * 1000;

const fetchText = async (url, headers = {}) => {
  const res = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0 (PrestoAssistant)", ...headers },
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.text();
};

const fetchJson = async (url, headers = {}) => {
  const res = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0 (PrestoAssistant)", ...headers },
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
};

const round2 = (n) => Math.round(n * 100) / 100;

// ---------- marco legal ----------

function legalOverview() {
  return (
    "⚖️ *Marco legal (Argentina)* — puedo detallarte:\n" +
    "• *Mutuo* entre particulares (CCyC) — prestar de forma aislada es libre\n" +
    "• *Entidades financieras* (Ley 21.526) — captar del público requiere autorización del BCRA\n" +
    "• *PNFC* — encuadre del prestamista profesional ante el BCRA\n" +
    "• *CNV* (Ley 26.831) — si el público invierte para financiar créditos\n" +
    "• *Fideicomiso* — vehículo legal para inversión en créditos\n" +
    "• *Intereses y tasa* (art. 768 CCyC)\n" +
    "• *UIF* — antilavado y KYC\n" +
    "Preguntame por el punto que te interese."
  );
}

function legalDetail(id) {
  const map = {
    "ley-21526": {
      head: "⚖️ *Ley de Entidades Financieras (Ley 21.526)*",
      body: "Solo las entidades autorizadas por el BCRA pueden captar dinero del público y prestarlo de forma habitual. Intermediar sin autorización es una infracción y puede caer en el *art. 309 del Código Penal* (captación no autorizada).",
    },
    "codigo-penal-309": {
      head: "⚖️ *Captación no autorizada (art. 309 CP)*",
      body: "Recibir dinero del público prometiendo rendimiento sin autorización puede ser delito. Por eso la pata de inversión debe ir por entidad autorizada o fiduciario.",
    },
    pnfc: {
      head: "⚖️ *Proveedores No Financieros de Crédito (PNFC)*",
      body: "Las sociedades que otorgan crédito sin ser bancos se inscriben ante el BCRA como PNFC, con deberes de transparencia (TNA/CFT) y protección al usuario. Es el encuadre típico de una app de préstamos operada por un prestamista profesional.",
    },
    "cnv-26831": {
      head: "⚖️ *Oferta pública de inversiones (Ley 26.831 – CNV)*",
      body: "Ofrecer al público instrumentos para invertir en créditos es oferta pública y requiere autorización de la CNV. No se puede prometer rendimiento sin un vehículo autorizado.",
    },
    fideicomiso: {
      head: "⚖️ *Fideicomiso financiero de créditos*",
      body: "Vía habitual para que inversores financien préstamos sin que la app capte dinero: un fiduciario inscripto en la CNV administra un patrimonio separado. Es el modelo recomendado para conectar inversores y créditos de forma legal.",
    },
    "mutuo-ccyc": {
      head: "⚖️ *Mutuo entre particulares (CCyC art. 1520)*",
      body: "El préstamo entre personas se rige por el contrato de mutuo. Prestar de forma ocasional entre particulares es legal sin autorización; conviene instrumentarlo por escrito.",
    },
    "intereses-768": {
      head: "⚖️ *Intereses y tasa (art. 768 CCyC)*",
      body: "La tasa se pacta entre las partes, por leyes especiales o por reglamentaciones del BCRA (Tasa de Intereses Moratorios, TIM). Una tasa usuraria puede reducirse judicialmente. El BCRA fija referencias para préstamos personales y tarjetas.",
    },
    "uif-antilavado": {
      head: "⚖️ *Prevención de lavado (UIF)*",
      body: "La Ley 27.739 impone a los sujetos obligados identificar clientes (KYC), llevar registros y reportar operaciones sospechosas. Alcanza a prestamistas profesionales y vehículos de inversión.",
    },
  };
  const r = map[id];
  if (!r) return legalOverview();
  return `${r.head}\n${r.body}\n\nEsta información es general, no es asesoramiento legal.`;
}

// ---------- mercado ----------

async function fetchCoins() {
  try {
    const data = await fetchJson(
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether&vs_currencies=usd&include_24hr_change=true",
    );
    const pick = (coin, label) => ({
      symbol: label,
      name:
        label === "BTC" ? "Bitcoin" : label === "ETH" ? "Ethereum" : "Tether",
      price_usd: data[coin]?.usd ?? null,
      change_24h_pct: data[coin]?.usd_24h_change ?? null,
    });
    return [
      pick("bitcoin", "BTC"),
      pick("ethereum", "ETH"),
      pick("tether", "USDT"),
    ];
  } catch {
    return [];
  }
}

async function fetchIndex(symbol, label) {
  try {
    const data = await fetchJson(
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=1d&interval=1d`,
    );
    const meta = data?.chart?.result?.[0]?.meta ?? {};
    const price = meta.regularMarketPrice ?? null;
    const prev = meta.chartPreviousClose ?? meta.previousClose ?? null;
    const change = price != null && prev != null ? price - prev : null;
    return {
      symbol: label,
      name: label === "S&P 500" ? "S&P 500" : "Merval",
      price_usd: label === "S&P 500" ? price : null,
      price_local: label === "Merval" ? price : null,
      currency: meta.currency || (label === "Merval" ? "ARS" : "USD"),
      change_24h_pct:
        change != null && prev ? round2((change / prev) * 100) : null,
    };
  } catch {
    return null;
  }
}

async function fetchDollar() {
  try {
    const data = await fetchJson("https://api.bluelytics.com.ar/v2/latest");
    return {
      oficial: data?.oficial?.value_sell ?? null,
      oficial_avg: data?.oficial?.value_avg ?? null,
      blue: data?.blue?.value_sell ?? null,
      blue_avg: data?.blue?.value_avg ?? null,
    };
  } catch {
    return null;
  }
}

async function getMarket() {
  if (marketCache.data && Date.now() - marketCache.at < MARKET_TTL)
    return marketCache.data;
  const [coins, sp500, merval, dollar] = await Promise.all([
    fetchCoins(),
    fetchIndex("^GSPC", "S&P 500"),
    fetchIndex("^MERV", "Merval"),
    fetchDollar(),
  ]);
  const data = {
    updated_at: new Date().toISOString(),
    coins,
    indices: [sp500, merval].filter(Boolean),
    dollar,
  };
  marketCache.data = data;
  marketCache.at = Date.now();
  return data;
}

// ---------- noticias ----------

function parseRss(xml, source) {
  const items = [];
  const blocks = xml.match(/<item[\s\S]*?<\/item>/g) ?? [];
  for (const block of blocks.slice(0, 8)) {
    const title = (block.match(
      /<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/,
    ) ?? [])[1]?.trim();
    const link = (block.match(/<link>([\s\S]*?)<\/link>/) ?? [])[1]?.trim();
    const pubDate = (block.match(/<pubDate>([\s\S]*?)<\/pubDate>/) ??
      [])[1]?.trim();
    if (title)
      items.push({
        title,
        link: link || null,
        published_at: pubDate || null,
        source,
      });
  }
  return items;
}

async function fetchFeed(name, url) {
  try {
    const xml = await fetchText(url);
    return parseRss(xml, name);
  } catch {
    return [];
  }
}

async function getNews() {
  if (newsCache.data && Date.now() - newsCache.at < NEWS_TTL)
    return newsCache.data;
  const feeds = await Promise.all([
    fetchFeed("Ámbito", "https://www.ambito.com/rss/economia.xml"),
    fetchFeed(
      "La Nación",
      "https://contenidos.lanacion.com.ar/herramientas/rss/economia_rss.xml",
    ),
  ]);
  const data = {
    updated_at: new Date().toISOString(),
    items: feeds.flat().slice(0, 12),
  };
  newsCache.data = data;
  newsCache.at = Date.now();
  return data;
}

// ---------- contexto del usuario ----------

function buildUserContext(user, db) {
  const accounts = db.accounts.filter((a) => a.user_id === user.id);
  const offers = db.offers.filter((o) => o.lender_user_id === user.id);
  const loans = db.loans.filter(
    (l) => l.borrower_user_id === user.id || l.lender_user_id === user.id,
  );
  const positions = db.positions.filter((p) => p.user_id === user.id);
  return {
    nombre: user.first_name || user.email,
    billeteras: accounts.map((a) => ({ moneda: a.currency, saldo: a.balance })),
    ofertas_activas: offers.filter((o) => o.status === "active").length,
    ofertas_aceptadas: offers.filter((o) => o.status === "accepted").length,
    prestamos_activos: loans.filter((l) => l.status === "active").length,
    prestamos_pagados: loans.filter((l) => l.status === "paid").length,
    inversiones_activas: positions.filter((p) => p.status === "active").length,
  };
}

// ---------- chat ----------

const normalize = (s) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

const has = (t, ...words) => words.some((w) => t.includes(w));

function fmtUsd(n) {
  return n == null
    ? "—"
    : `USD ${n.toLocaleString("es-AR", { maximumFractionDigits: 2 })}`;
}

function fmtArs(n) {
  return n == null ? "—" : `ARS ${Math.round(n).toLocaleString("es-AR")}`;
}

function marketReply(market) {
  const btc = market.coins.find((c) => c.symbol === "BTC");
  const eth = market.coins.find((c) => c.symbol === "ETH");
  const sp = market.indices.find((i) => i.symbol === "S&P 500");
  const merv = market.indices.find((i) => i.symbol === "Merval");
  const d = market.dollar;
  const lines = [
    "📊 *Resumen de mercado*:",
    `• Bitcoin: ${fmtUsd(btc?.price_usd)} (${btc?.change_24h_pct != null ? btc.change_24h_pct.toFixed(1) + "% 24h" : "—"})`,
    `• Ethereum: ${fmtUsd(eth?.price_usd)} (${eth?.change_24h_pct != null ? eth.change_24h_pct.toFixed(1) + "% 24h" : "—"})`,
    `• S&P 500: ${sp?.price_usd != null ? sp.price_usd.toLocaleString("es-AR") : "—"}`,
    `• Merval: ${merv?.price_local != null ? Math.round(merv.price_local).toLocaleString("es-AR") : "—"}`,
    `• Dólar blue: ${fmtArs(d?.blue)} · oficial: ${fmtArs(d?.oficial)}`,
  ];
  return lines.join("\n");
}

function ruleReply(message, market, news, ctx) {
  const t = normalize(message);

  if (has(t, "hola", "buenas", "hey", "ayuda", "que podes", "que puedes")) {
    return (
      `¡Hola ${ctx.nombre}! Soy tu asistente de Presto. Puedo ayudarte con:\n` +
      "• Estado de tu bolsa (bitcoin, cripto, índices, dólar)\n" +
      "• Noticias financieras\n" +
      "• Resumen de tus inversiones, préstamos y ofertas\n" +
      "• Saldos de tus billeteras\n" +
      'Escribí algo como "¿cómo está bitcoin?" o "resumen".'
    );
  }

  if (has(t, "bitcoin", "btc", "cripto", "crypto", "ethereum", "eth")) {
    const coins = market.coins
      .filter((c) =>
        t.includes("eth") || t.includes("ethereum") ? true : c.symbol === "BTC",
      )
      .filter((c) => c.price_usd != null);
    if (coins.length === 0)
      return "No pude obtener el precio de criptomonedas ahora.";
    return (
      "💰 *Criptomonedas*:\n" +
      coins
        .map(
          (c) =>
            `• ${c.name} (${c.symbol}): ${fmtUsd(c.price_usd)} (${c.change_24h_pct != null ? c.change_24h_pct.toFixed(1) + "% 24h" : "—"})`,
        )
        .join("\n")
    );
  }

  if (has(t, "dolar", "blue", "oficial", "usd", "cotizacion")) {
    const d = market.dollar;
    if (!d) return "No pude obtener la cotización del dólar ahora.";
    return (
      "💵 *Dólar en Argentina*:\n" +
      `• Blue (venta): ${fmtArs(d.blue)}\n` +
      `• Oficial (venta): ${fmtArs(d.oficial)}\n` +
      `Brecha blue/oficial: ${d.blue && d.oficial ? ((d.blue / d.oficial - 1) * 100).toFixed(1) + "%" : "—"}`
    );
  }

  if (
    has(
      t,
      "sp500",
      "sp 500",
      "s&p",
      "s and p",
      "indice",
      "bolsa",
      "wall street",
      "merval",
      "merval",
    )
  ) {
    return marketReply(market);
  }

  if (has(t, "noticia", "titular", "que paso", "actualidad")) {
    if (news.items.length === 0) return "No pude cargar las noticias ahora.";
    return (
      "📰 *Últimas noticias financieras*:\n" +
      news.items
        .slice(0, 6)
        .map((n) => `• [${n.source}] ${n.title}`)
        .join("\n")
    );
  }

  if (
    has(
      t,
      "ley",
      "legal",
      "legislacion",
      "regulacion",
      "regulacion",
      "normativa",
      "requisito",
      "habilitacion",
      "permiso",
      "autorizacion",
      "puedo prestar",
      "que necesito para prestar",
    )
  ) {
    return legalOverview();
  }

  if (
    has(
      t,
      "captar",
      "captacion",
      "fondo del publico",
      "recibir dinero",
      "deposito del publico",
      "captacion no autorizada",
    )
  ) {
    return legalDetail("ley-21526") + "\n\n" + legalDetail("codigo-penal-309");
  }

  if (
    has(
      t,
      "pnfc",
      "proveedor no financiero",
      "sociedad prestamista",
      "empresa de creditos",
    )
  ) {
    return legalDetail("pnfc");
  }

  if (
    has(
      t,
      "cnv",
      "bolsa",
      "oferta publica",
      "crowdfunding",
      "financiamiento colectivo",
      "mercado de capitales",
    )
  ) {
    return legalDetail("cnv-26831");
  }

  if (has(t, "fideicomiso", "fiduciario")) {
    return legalDetail("fideicomiso");
  }

  if (
    has(
      t,
      "mutuo",
      "entre particulares",
      "prestamo entre personas",
      "contrato de prestamo",
    )
  ) {
    return legalDetail("mutuo-ccyc");
  }

  if (has(t, "tasa", "interes", "usura", "usurario", "tna", "cft")) {
    return legalDetail("intereses-768");
  }

  if (has(t, "lavado", "uif", "antilavado", "kyc", "conozca a su cliente")) {
    return legalDetail("uif-antilavado");
  }

  if (has(t, "inversion", "posicion", "cartera", "plazo fijo")) {
    if (ctx.inversiones_activas === 0)
      return "No tenés inversiones activas actualmente. Podés ver los productos disponibles en la sección Inversiones.";
    return `Tenés ${ctx.inversiones_activas} inversión(es) activa(s). Detalle completo en Inversiones → Tus posiciones.`;
  }

  if (has(t, "prestamo", "prestamos", "cuota", "deudor")) {
    return `Estado de préstamos: ${ctx.prestamos_activos} activo(s), ${ctx.prestamos_pagados} pagado(s). Revisá Préstamos para el detalle de cuotas.`;
  }

  if (has(t, "oferta", "publicar", "prestamista")) {
    return `Ofertas: ${ctx.ofertas_activas} activa(s), ${ctx.ofertas_aceptadas} aceptada(s). Podés gestionarlas en Mis ofertas o publicar nuevas en el Marketplace.`;
  }

  if (has(t, "saldo", "billetera", "cuenta", "dinero", "cuanto tengo")) {
    if (ctx.billeteras.length === 0) return "No tenés billeteras creadas.";
    return (
      "👛 *Tus saldos*:\n" +
      ctx.billeteras
        .map(
          (b) =>
            `• ${b.moneda}: ${b.moneda === "USD" ? fmtUsd(parseFloat(b.saldo)) : fmtArs(parseFloat(b.saldo))}`,
        )
        .join("\n")
    );
  }

  if (has(t, "resumen", "como estoy", "estado", "general")) {
    return (
      `📋 *Resumen de ${ctx.nombre}*:\n` +
      ctx.billeteras
        .map(
          (b) =>
            `• Billetera ${b.moneda}: ${b.moneda === "USD" ? fmtUsd(parseFloat(b.saldo)) : fmtArs(parseFloat(b.saldo))}`,
        )
        .join("\n") +
      `\n• Ofertas activas: ${ctx.ofertas_activas}` +
      `\n• Préstamos activos: ${ctx.prestamos_activos}` +
      `\n• Inversiones activas: ${ctx.inversiones_activas}\n\n` +
      marketReply(market)
    );
  }

  return null;
}

const FALLBACK =
  "No estoy seguro de cómo ayudarte con eso. Podés preguntarme por:\n" +
  "• Bitcoin / criptomonedas\n• Dólar / cotizaciones\n• S&P 500 / Merval\n" +
  "• Noticias financieras\n• Tus inversiones, préstamos, ofertas o saldos\n• Un resumen general";

async function askLLM(message, market, news, ctx) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) return null;
  const context = {
    user: ctx,
    market: {
      btc: market.coins.find((c) => c.symbol === "BTC"),
      eth: market.coins.find((c) => c.symbol === "ETH"),
      dollar: market.dollar,
      indices: market.indices,
    },
    news: news.items.slice(0, 6).map((n) => n.title),
  };
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${key}`,
    },
    signal: AbortSignal.timeout(15000),
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "Sos el asistente de Presto, una app de préstamos e inversiones en Argentina. Respondé en español rioplatense, claro y breve (máx 6 líneas). Usá los datos de contexto cuando sean útiles. No inventes datos numéricos que no estén en el contexto.",
        },
        {
          role: "user",
          content: `Contexto JSON: ${JSON.stringify(context)}\n\nMensaje del usuario: ${message}`,
        },
      ],
      max_tokens: 300,
    }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data?.choices?.[0]?.message?.content?.trim() ?? null;
}

export async function handleChat(body, user, db) {
  const message = String(body?.message ?? "").trim();
  if (!message) {
    return { reply: "Escribí tu consulta y te ayudo.", intent: "empty" };
  }
  const market = await getMarket();
  const news = await getNews();
  const ctx = buildUserContext(user, db);

  const rules = ruleReply(message, market, news, ctx);
  if (rules) return { reply: rules, intent: "rules" };

  const llm = await askLLM(message, market, news, ctx).catch(() => null);
  if (llm) return { reply: llm, intent: "llm" };

  return { reply: FALLBACK, intent: "fallback" };
}

export { getMarket, getNews };
