// Mock server de la Presto API (schema.yml — OpenAPI 3.0.3)
// Implementa todos los endpoints con datos en memoria para probar el frontend.
// Uso: node mock/server.mjs   →  http://localhost:8000/api/v1
//
// Usuarios de prueba:
//   demo@presto.com  / demo123456   (prestatario, con billeteras ARS/USD)
//   lender@presto.com / lender123456 (prestamista con ofertas publicadas)

import http from "node:http";
import { randomUUID } from "node:crypto";
import { handleChat, getMarket, getNews } from "./assistant.mjs";
import {
  listRegulations,
  getRegulation,
  CATEGORIES,
  DISCLAIMER,
} from "./regulations.mjs";

const PORT = Number(process.env.PORT ?? 8001);

// ---------- helpers ----------

const round2 = (n) => Math.round(n * 100) / 100;
const money = (n) => round2(n).toFixed(2);
const uuid = () => randomUUID();
const iso = (d = new Date()) => d.toISOString();
const ymd = (d) => d.toISOString().slice(0, 10);

function addMonths(date, n) {
  const d = new Date(date);
  d.setMonth(d.getMonth() + n);
  return d;
}

function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

/** Amortización francesa: devuelve filas {principal, interest, payment}. */
function schedule(amount, annualRatePct, months) {
  const i = annualRatePct / 100 / 12;
  const payment =
    i === 0 ? amount / months : (amount * i) / (1 - Math.pow(1 + i, -months));
  const rows = [];
  let balance = amount;
  for (let k = 1; k <= months; k++) {
    let interest = round2(balance * i);
    let principal = round2(payment - interest);
    if (k === months) {
      principal = round2(balance);
      interest =
        round2(payment * 1 - principal) === 0
          ? interest
          : round2(payment - principal);
    }
    balance = round2(balance - principal);
    rows.push({
      principal,
      interest,
      payment: round2(principal + interest),
    });
  }
  return rows;
}

// ---------- datos en memoria ----------

const db = {
  users: [],
  accounts: [],
  transactions: [],
  offers: [],
  loans: [],
  positions: [],
  products: [],
  kyc: [],
  payments: [],
  categories: [],
  budgets: [],
  expenses: [],
  notifications: [],
};

function seed() {
  const demo = {
    id: uuid(),
    email: "demo@presto.com",
    password: "demo123456",
    first_name: "Demo",
    last_name: "Presto",
    phone_number: "",
    date_of_birth: null,
    country: "AR",
  };
  const lender = {
    id: uuid(),
    email: "lender@presto.com",
    password: "lender123456",
    first_name: "Laura",
    last_name: "Prestamista",
    phone_number: "",
    date_of_birth: null,
    country: "AR",
  };
  db.users.push(demo, lender);

  const mkAccount = (user, currency, balance) => {
    const acc = {
      id: uuid(),
      user_id: user.id,
      currency,
      kind: "user_wallet",
      balance,
      created_at: iso(),
    };
    db.accounts.push(acc);
    return acc;
  };
  const demoArs = mkAccount(demo, "ARS", money(500000));
  mkAccount(demo, "USD", money(1000));
  mkAccount(lender, "ARS", money(750000));

  db.transactions.push({
    id: uuid(),
    type: "deposit",
    amount: money(500000),
    currency: "ARS",
    idempotency_key: uuid(),
    created_by_user_id: demo.id,
    destination_account_id: demoArs.id,
    occurred_at: iso(),
    description: "Depósito inicial de bienvenida",
    reverses: null,
    created_at: iso(),
  });

  const mkOffer = (
    lenderUser,
    amount,
    currency,
    rate,
    term,
    reqs,
    status = "active",
  ) => {
    const offer = {
      id: uuid(),
      lender_user_id: lenderUser.id,
      amount: money(amount),
      currency,
      interest_rate: rate.toFixed(2),
      term_months: term,
      requirements: reqs,
      status,
      created_at: iso(),
    };
    db.offers.push(offer);
    return offer;
  };
  mkOffer(
    lender,
    100000,
    "ARS",
    24,
    12,
    "Recibo de sueldo y score crediticio mayor a 600",
  );
  mkOffer(lender, 50000, "ARS", 30, 6, "Sin garantía · Aprobación en 24 hs");
  mkOffer(lender, 3000, "USD", 8, 24, "Acepta garantía en dólares");
  mkOffer(lender, 200000, "ARS", 18, 3, "Oferta de corto plazo", "expired");

  db.products.push(
    {
      id: uuid(),
      type: "fixed_term",
      currency: "ARS",
      term_days: 30,
      annual_rate_tna: "21.00",
      min_amount: money(1000),
      status: "active",
      created_at: iso(),
    },
    {
      id: uuid(),
      type: "fixed_term",
      currency: "ARS",
      term_days: 90,
      annual_rate_tna: "25.00",
      min_amount: money(5000),
      status: "active",
      created_at: iso(),
    },
    {
      id: uuid(),
      type: "fixed_term",
      currency: "USD",
      term_days: 30,
      annual_rate_tna: "4.50",
      min_amount: money(100),
      status: "active",
      created_at: iso(),
    },
  );
  // ---- presupuestos y pagos de ejemplo ----
  const supermercado = {
    id: uuid(),
    user_id: demo.id,
    name: "Supermercado",
    created_at: iso(),
  };
  db.categories.push(supermercado);

  db.budgets.push({
    id: uuid(),
    user_id: demo.id,
    category_id: supermercado.id,
    category: supermercado,
    period: "monthly",
    limit_amount: money(80000),
    currency: "ARS",
    alert_threshold: 50,
    created_at: iso(),
  });

  const gasto = db.transactions[0];
  db.expenses.push({
    id: uuid(),
    user_id: demo.id,
    category_id: supermercado.id,
    ledger_transaction_id: gasto.id,
    created_at: iso(),
  });

  db.payments.push({
    id: uuid(),
    user_id: demo.id,
    direction: "deposit",
    amount: money(25000),
    currency: "ARS",
    provider: "simulated",
    provider_reference: uuid(),
    status: "confirmed",
    ledger_transaction_id: null,
    checkout_url: "",
    created_at: iso(),
    updated_at: iso(),
    idempotency_key: uuid(),
  });

  db.notifications.push({
    id: uuid(),
    user_id: demo.id,
    event_type: "budget_alert",
    reference_id: supermercado.id,
    status: "pending",
    created_at: iso(),
    sent_at: null,
    error: "",
  });
}
seed();

// ---------- auth / tokens ----------

const publicUser = (u) => ({
  id: u.id,
  email: u.email,
  first_name: u.first_name,
  last_name: u.last_name,
});

const issueTokens = (user) => ({
  access: `${user.id}.${uuid()}`,
  refresh: `${user.id}.${uuid()}`,
});

function userFromRequest(req) {
  const header = req.headers["authorization"] ?? "";
  const token = header.replace(/^Bearer\s+/i, "");
  const userId = token.split(".")[0];
  return db.users.find((u) => u.id === userId) ?? null;
}

function requireAuth(req, res) {
  const user = userFromRequest(req);
  if (!user) {
    send(res, 401, {
      detail: "Credenciales de autenticación no proporcionadas.",
    });
    return null;
  }
  return user;
}

// ---------- http helpers ----------

// El mock es una herramienta de desarrollo: acepta cualquier origen local
// (Vite usa puertos distintos en dev y en E2E) y los extras que se le pasen
// por MOCK_ALLOWED_ORIGINS.
const EXTRA_ORIGINS = (process.env.MOCK_ALLOWED_ORIGINS ?? "")
  .split(",")
  .map((o) => o.trim())
  .filter(Boolean);
const ALLOWED_ORIGINS = [
  "http://localhost:5173",
  "http://127.0.0.1:5173",
  ...EXTRA_ORIGINS,
];
const LOCAL_ORIGIN = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

const CORS = {
  "Access-Control-Allow-Methods": "GET, POST, PATCH, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers":
    "Authorization, Content-Type, Idempotency-Key",
  // Con `credentials: "include"` el origin no puede ser "*".
  "Access-Control-Allow-Credentials": "true",
};

function corsHeaders(req) {
  const origin = req.headers.origin;
  const allowed =
    origin && (ALLOWED_ORIGINS.includes(origin) || LOCAL_ORIGIN.test(origin));
  return {
    ...CORS,
    ...(allowed ? { "Access-Control-Allow-Origin": origin } : {}),
  };
}

function parseCookies(req) {
  const header = req.headers.cookie ?? "";
  const out = {};
  for (const part of header.split(";")) {
    const idx = part.indexOf("=");
    if (idx === -1) continue;
    out[part.slice(0, idx).trim()] = decodeURIComponent(
      part.slice(idx + 1).trim(),
    );
  }
  return out;
}

const REFRESH_COOKIE = "presto_refresh";

function refreshCookie(value) {
  return `${REFRESH_COOKIE}=${encodeURIComponent(value)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=1209600`;
}

function clearRefreshCookie() {
  return `${REFRESH_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`;
}

function send(res, status, data, extraHeaders = {}) {
  const payload = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(payload),
    ...extraHeaders,
  });
  res.end(payload);
}

async function readJson(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  if (chunks.length === 0) return {};
  const raw = Buffer.concat(chunks).toString("utf8");
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function accountOf(userId, currency) {
  return db.accounts.find(
    (a) => a.user_id === userId && a.currency === currency,
  );
}

function moveBalance(account, delta) {
  account.balance = money(parseFloat(account.balance) + delta);
}

function pushTransaction(fields) {
  const tx = {
    id: uuid(),
    idempotency_key: uuid(),
    reverses: null,
    occurred_at: iso(),
    created_at: iso(),
    destination_account_id: null,
    description: "",
    ...fields,
  };
  db.transactions.push(tx);
  return tx;
}

// ---------- router ----------

const server = http.createServer(async (req, res) => {
  for (const [key, value] of Object.entries(corsHeaders(req))) {
    res.setHeader(key, value);
  }
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, "http://localhost");
  const path = url.pathname.replace(/\/+$/, "") || "/";
  const m = req.method;
  const seg = path.startsWith("/api/v1/") ? path.slice(8).split("/") : [];
  const [a, b, c, d, e] = seg;

  // ---- auth ----
  if (m === "POST" && a === "auth" && b === "login") {
    const body = await readJson(req);
    const user = db.users.find(
      (u) => u.email === body?.email && u.password === body?.password,
    );
    if (!user) {
      return send(res, 401, { detail: "Email o contraseña incorrectos." });
    }
    const tokens = issueTokens(user);
    return send(
      res,
      200,
      { access: tokens.access, user: publicUser(user) },
      {
        "Set-Cookie": refreshCookie(tokens.refresh),
      },
    );
  }

  if (m === "POST" && a === "auth" && b === "logout") {
    res.writeHead(204, { "Set-Cookie": clearRefreshCookie() });
    res.end();
    return;
  }

  if (m === "POST" && a === "auth" && b === "register") {
    const body = await readJson(req);
    const errors = {};
    if (!body?.email || !/^\S+@\S+\.\S+$/.test(body.email)) {
      errors.email = ["Ingresá un email válido."];
    }
    if (!body?.password || body.password.length < 10) {
      errors.password = ["La contraseña debe tener al menos 10 caracteres."];
    }
    if (db.users.some((u) => u.email === body?.email)) {
      errors.email = ["Ya existe una cuenta con ese email."];
    }
    if (Object.keys(errors).length > 0) return send(res, 400, errors);
    const user = {
      id: uuid(),
      email: body.email,
      password: body.password,
      first_name: "",
      last_name: "",
      phone_number: "",
      date_of_birth: null,
      country: "",
    };
    db.users.push(user);
    return send(res, 201, publicUser(user));
  }

  if (m === "POST" && a === "auth" && b === "token" && c === "refresh") {
    const cookies = parseCookies(req);
    const body = await readJson(req);
    const raw = cookies[REFRESH_COOKIE] ?? body?.refresh ?? "";
    const userId = String(raw).split(".")[0];
    const user = db.users.find((u) => u.id === userId);
    if (!user)
      return send(res, 401, { detail: "Refresh token inválido o expirado." });
    const tokens = issueTokens(user);
    return send(
      res,
      200,
      { access: tokens.access, user: publicUser(user) },
      {
        "Set-Cookie": refreshCookie(tokens.refresh),
      },
    );
  }

  if (a === "auth" && b === "me") {
    const user = requireAuth(req, res);
    if (!user) return;
    if (m === "GET") return send(res, 200, publicUser(user));
    if (m === "PATCH") {
      const body = await readJson(req);
      if (body == null) return send(res, 400, { detail: "JSON inválido." });
      if (body.phone_number !== undefined)
        user.phone_number = body.phone_number;
      if (body.date_of_birth !== undefined)
        user.date_of_birth = body.date_of_birth;
      if (body.country !== undefined) user.country = body.country;
      return send(res, 200, publicUser(user));
    }
  }

  // ---- ledger ----
  if (a === "ledger" && b === "accounts" && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const list = db.accounts.filter((x) => x.user_id === user.id);
    if (m === "GET") return send(res, 200, list);
    if (m === "POST") {
      const body = await readJson(req);
      const currency = body?.currency;
      if (currency !== "ARS" && currency !== "USD") {
        return send(res, 400, { currency: ["Moneda inválida (ARS o USD)."] });
      }
      if (list.some((x) => x.currency === currency)) {
        return send(res, 400, {
          detail: `Ya tenés una billetera en ${currency}.`,
        });
      }
      const acc = {
        id: uuid(),
        user_id: user.id,
        currency,
        kind: "user_wallet",
        balance: money(0),
        created_at: iso(),
      };
      db.accounts.push(acc);
      return send(res, 201, acc);
    }
  }

  if (
    m === "GET" &&
    a === "ledger" &&
    b === "accounts" &&
    c &&
    d === "balance"
  ) {
    const user = requireAuth(req, res);
    if (!user) return;
    const acc = db.accounts.find((x) => x.id === c && x.user_id === user.id);
    if (!acc) return send(res, 404, { detail: "Cuenta no encontrada." });
    return send(res, 200, {
      account_id: acc.id,
      balance: acc.balance,
      currency: acc.currency,
    });
  }

  if (a === "ledger" && b === "transactions") {
    const user = requireAuth(req, res);
    if (!user) return;
    const own = db.transactions
      .filter((t) => t.created_by_user_id === user.id)
      .sort((x, y) => y.created_at.localeCompare(x.created_at));
    if (m === "GET" && !c) return send(res, 200, own);
    if (m === "POST" && !c) {
      const body = await readJson(req);
      const type = body?.type;
      const currency = body?.currency;
      const amount = parseFloat(body?.amount);
      const errors = {};
      if (!["deposit", "withdrawal", "transfer"].includes(type)) {
        errors.type = ["Tipo inválido (deposit, withdrawal, transfer)."];
      }
      if (currency !== "ARS" && currency !== "USD") {
        errors.currency = ["Moneda inválida (ARS o USD)."];
      }
      if (!Number.isFinite(amount) || amount <= 0) {
        errors.amount = ["El importe debe ser mayor a cero."];
      }
      if (Object.keys(errors).length > 0) return send(res, 400, errors);

      const source = accountOf(user.id, currency);
      if (!source && type !== "deposit") {
        return send(res, 400, {
          detail: `No tenés billetera en ${currency}. Creala primero.`,
        });
      }
      let destination = null;
      if (type === "transfer") {
        destination = db.accounts.find(
          (x) => x.id === body?.destination_account_id && x.user_id === user.id,
        );
        if (!destination) {
          return send(res, 400, {
            destination_account_id: ["Cuenta destino inválida."],
          });
        }
        if (parseFloat(source.balance) < amount) {
          return send(res, 400, {
            detail: "Saldo insuficiente para transferir.",
          });
        }
      }
      if (type === "withdrawal" && parseFloat(source.balance) < amount) {
        return send(res, 400, { detail: "Saldo insuficiente para el retiro." });
      }

      if (type === "deposit") {
        if (!source) {
          const acc = {
            id: uuid(),
            user_id: user.id,
            currency,
            kind: "user_wallet",
            balance: money(0),
            created_at: iso(),
          };
          db.accounts.push(acc);
          moveBalance(acc, amount);
        } else {
          moveBalance(source, amount);
        }
      } else if (type === "withdrawal") {
        moveBalance(source, -amount);
      } else {
        moveBalance(source, -amount);
        moveBalance(destination, amount);
      }

      const created = pushTransaction({
        type,
        amount: money(amount),
        currency,
        created_by_user_id: user.id,
        destination_account_id: destination
          ? destination.id
          : type === "deposit"
            ? (accountOf(user.id, currency)?.id ?? null)
            : null,
        description: body?.description || "",
      });
      return send(res, 201, created);
    }
    if (m === "GET" && c) {
      const tx = own.find((t) => t.id === c);
      if (!tx) return send(res, 404, { detail: "Movimiento no encontrado." });
      return send(res, 200, tx);
    }
  }

  // ---- ofertas propias ----
  if (a === "offers" && !b) {
    const user = requireAuth(req, res);
    if (!user) return;
    const own = db.offers.filter((o) => o.lender_user_id === user.id);
    if (m === "GET") return send(res, 200, own);
    if (m === "POST") {
      const body = await readJson(req);
      const amount = parseFloat(body?.amount);
      const rate = parseFloat(body?.interest_rate);
      const term = parseInt(body?.term_months, 10);
      const errors = {};
      if (!Number.isFinite(amount) || amount <= 0) {
        errors.amount = ["Ingresá un monto mayor a cero."];
      }
      if (!["ARS", "USD"].includes(body?.currency)) {
        errors.currency = ["Moneda inválida (ARS o USD)."];
      }
      if (!Number.isFinite(rate) || rate < 0) {
        errors.interest_rate = ["Ingresá una tasa válida."];
      }
      if (!Number.isInteger(term) || term < 1) {
        errors.term_months = ["El plazo debe ser al menos 1 mes."];
      }
      if (Object.keys(errors).length > 0) return send(res, 400, errors);
      const offer = {
        id: uuid(),
        lender_user_id: user.id,
        amount: money(amount),
        currency: body.currency,
        interest_rate: rate.toFixed(2),
        term_months: term,
        requirements: body?.requirements ?? "",
        status: "active",
        created_at: iso(),
      };
      db.offers.push(offer);
      return send(res, 201, offer);
    }
  }

  if (a === "offers" && b && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const offer = db.offers.find(
      (o) => o.id === b && o.lender_user_id === user.id,
    );
    if (!offer) return send(res, 404, { detail: "Oferta no encontrada." });
    if (m === "GET") return send(res, 200, offer);
    if (m === "PATCH") {
      const body = await readJson(req);
      if (body == null) return send(res, 400, { detail: "JSON inválido." });
      if (body.status !== undefined) {
        if (body.status !== "expired") {
          return send(res, 400, {
            status: ["Solo se puede expirar la oferta."],
          });
        }
        offer.status = "expired";
      }
      if (body.amount !== undefined)
        offer.amount = money(parseFloat(body.amount));
      if (body.interest_rate !== undefined) {
        offer.interest_rate = parseFloat(body.interest_rate).toFixed(2);
      }
      if (body.term_months !== undefined)
        offer.term_months = parseInt(body.term_months, 10);
      if (body.requirements !== undefined)
        offer.requirements = body.requirements;
      return send(res, 200, offer);
    }
  }

  // ---- matching ----
  if (m === "GET" && a === "matching" && b === "offers") {
    const user = requireAuth(req, res);
    if (!user) return;
    let list = db.offers.filter((o) => o.status === "active");
    const q = url.searchParams;
    const fAmountMin = q.get("amount_min");
    const fAmountMax = q.get("amount_max");
    const fCurrency = q.get("currency");
    const fMaxRate = q.get("max_rate");
    const fTerm = q.get("term_months");
    const ordering = q.get("ordering");
    if (fAmountMin)
      list = list.filter((o) => parseFloat(o.amount) >= parseFloat(fAmountMin));
    if (fAmountMax)
      list = list.filter((o) => parseFloat(o.amount) <= parseFloat(fAmountMax));
    if (fCurrency) list = list.filter((o) => o.currency === fCurrency);
    if (fMaxRate)
      list = list.filter(
        (o) => parseFloat(o.interest_rate) <= parseFloat(fMaxRate),
      );
    if (fTerm) list = list.filter((o) => o.term_months === parseInt(fTerm, 10));
    if (ordering === "rate")
      list.sort(
        (x, y) => parseFloat(x.interest_rate) - parseFloat(y.interest_rate),
      );
    if (ordering === "term") list.sort((x, y) => x.term_months - y.term_months);
    if (ordering === "amount")
      list.sort((x, y) => parseFloat(x.amount) - parseFloat(y.amount));
    return send(res, 200, list);
  }

  if (m === "POST" && a === "matching" && b === "comparisons") {
    const user = requireAuth(req, res);
    if (!user) return;
    const body = await readJson(req);
    const ids = body?.offer_ids;
    if (!Array.isArray(ids) || ids.length < 2) {
      return send(res, 400, {
        offer_ids: ["Seleccioná al menos 2 ofertas para comparar."],
      });
    }
    const rows = ids
      .map((id) => db.offers.find((o) => o.id === id))
      .filter(Boolean)
      .map((o) => {
        const rows = schedule(
          parseFloat(o.amount),
          parseFloat(o.interest_rate),
          o.term_months,
        );
        const installment = rows[0]?.payment ?? 0;
        const totalCost = round2(installment * o.term_months);
        return {
          id: o.id,
          lender_user_id: o.lender_user_id,
          amount: o.amount,
          currency: o.currency,
          interest_rate: o.interest_rate,
          term_months: o.term_months,
          requirements: o.requirements,
          installment: money(installment),
          total_interest: money(totalCost - parseFloat(o.amount)),
          total_cost: money(totalCost),
        };
      });
    return send(res, 200, rows);
  }

  // ---- préstamos ----
  if (a === "loans" && !b) {
    const user = requireAuth(req, res);
    if (!user) return;
    if (m === "GET") {
      const list = db.loans.filter(
        (l) => l.borrower_user_id === user.id || l.lender_user_id === user.id,
      );
      return send(
        res,
        200,
        list.map(({ installments, terms_snapshot, ...loan }) => loan),
      );
    }
    if (m === "POST") {
      const body = await readJson(req);
      const offer = db.offers.find((o) => o.id === body?.offer_id);
      if (!offer) return send(res, 404, { detail: "Oferta no encontrada." });
      if (offer.status !== "active") {
        return send(res, 400, { detail: "La oferta ya no está activa." });
      }
      if (offer.lender_user_id === user.id) {
        return send(res, 400, { detail: "No podés aceptar tu propia oferta." });
      }
      offer.status = "accepted";
      const now = new Date();
      const rows = schedule(
        parseFloat(offer.amount),
        parseFloat(offer.interest_rate),
        offer.term_months,
      );
      const installments = rows.map((row, idx) => ({
        id: uuid(),
        number: idx + 1,
        due_date: ymd(addMonths(now, idx + 1)),
        principal_amount: money(row.principal),
        interest_amount: money(row.interest),
        amount: money(row.payment),
        status: "pending",
        paid_at: null,
      }));
      const loan = {
        id: uuid(),
        borrower_user_id: user.id,
        lender_user_id: offer.lender_user_id,
        offer_id: offer.id,
        principal: offer.amount,
        currency: offer.currency,
        interest_rate: offer.interest_rate,
        term_months: offer.term_months,
        status: "active",
        accepted_at: iso(now),
        installments,
        terms_snapshot: {
          id: uuid(),
          accepted_at: iso(now),
          accepted_by_user_id: user.id,
          snapshot_data: {
            amount: offer.amount,
            currency: offer.currency,
            interest_rate: offer.interest_rate,
            term_months: offer.term_months,
            requirements: offer.requirements,
          },
          is_immutable: true,
        },
      };
      db.loans.push(loan);
      const { installments: _i, terms_snapshot: _s, ...publicLoan } = loan;
      return send(res, 201, publicLoan);
    }
  }

  if (m === "GET" && a === "loans" && b && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const loan = db.loans.find(
      (l) =>
        l.id === b &&
        (l.borrower_user_id === user.id || l.lender_user_id === user.id),
    );
    if (!loan) return send(res, 404, { detail: "Préstamo no encontrado." });
    const { installments, terms_snapshot, ...publicLoan } = loan;
    return send(res, 200, { ...publicLoan, terms_snapshot, installments });
  }

  if (
    m === "POST" &&
    a === "loans" &&
    b &&
    c === "installments" &&
    e === "pay"
  ) {
    const user = requireAuth(req, res);
    if (!user) return;
    const loan = db.loans.find(
      (l) => l.id === b && l.borrower_user_id === user.id,
    );
    if (!loan) return send(res, 404, { detail: "Préstamo no encontrado." });
    const number = parseInt(d, 10);
    const inst = loan.installments.find((x) => x.number === number);
    if (!inst) return send(res, 404, { detail: "Cuota no encontrada." });
    if (inst.status === "paid") {
      return send(res, 400, { detail: "La cuota ya está pagada." });
    }
    const account = accountOf(user.id, loan.currency);
    const amount = parseFloat(inst.amount);
    if (!account || parseFloat(account.balance) < amount) {
      return send(res, 400, {
        detail: `Saldo insuficiente en tu billetera ${loan.currency} para pagar esta cuota.`,
      });
    }
    moveBalance(account, -amount);
    inst.status = "paid";
    inst.paid_at = iso();
    pushTransaction({
      type: "withdrawal",
      amount: money(amount),
      currency: loan.currency,
      created_by_user_id: user.id,
      destination_account_id: null,
      description: `Pago de cuota ${number} · préstamo ${loan.id.slice(0, 8)}`,
    });
    if (loan.installments.every((x) => x.status === "paid"))
      loan.status = "paid";
    return send(res, 200, inst);
  }

  // ---- inversiones ----
  if (m === "GET" && a === "investments" && b === "products" && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    return send(res, 200, db.products);
  }

  if (a === "investments" && b === "positions") {
    const user = requireAuth(req, res);
    if (!user) return;
    const own = db.positions.filter((p) => p.user_id === user.id);
    if (m === "GET" && !c) {
      return send(
        res,
        200,
        own.map(({ product_detail, ...p }) => p),
      );
    }
    if (m === "POST" && !c) {
      const body = await readJson(req);
      const product = db.products.find((p) => p.id === body?.product_id);
      if (!product)
        return send(res, 404, { detail: "Producto no encontrado." });
      if (product.status !== "active") {
        return send(res, 400, { detail: "El producto no está activo." });
      }
      const amount = parseFloat(body?.amount);
      if (!Number.isFinite(amount) || amount < parseFloat(product.min_amount)) {
        return send(res, 400, {
          amount: [
            `El monto mínimo es ${product.min_amount} ${product.currency}.`,
          ],
        });
      }
      const account = accountOf(user.id, product.currency);
      if (!account || parseFloat(account.balance) < amount) {
        return send(res, 400, {
          detail: `Saldo insuficiente en tu billetera ${product.currency}.`,
        });
      }
      moveBalance(account, -amount);
      const now = new Date();
      const interest =
        ((amount * parseFloat(product.annual_rate_tna)) / 100) *
        (product.term_days / 360);
      const position = {
        id: uuid(),
        user_id: user.id,
        product: product.id,
        amount: money(amount),
        status: "active",
        opened_at: iso(now),
        maturity_date: ymd(addDays(now, product.term_days)),
        interest_amount: money(interest),
        product_detail: product,
      };
      db.positions.push(position);
      pushTransaction({
        type: "withdrawal",
        amount: money(amount),
        currency: product.currency,
        created_by_user_id: user.id,
        destination_account_id: null,
        description: `Inversión a plazo fijo (${product.term_days} días)`,
      });
      const { product_detail, ...publicPos } = position;
      return send(res, 201, publicPos);
    }
    if (m === "GET" && c) {
      const pos = own.find((p) => p.id === c);
      if (!pos) return send(res, 404, { detail: "Posición no encontrada." });
      return send(res, 200, pos);
    }
  }

  // ---- kyc ----
  if (a === "kyc" && !b) {
    const user = requireAuth(req, res);
    if (!user) return;
    const list = db.kyc.filter((k) => k.user_id === user.id);
    if (m === "GET") {
      return send(res, 200, list.length > 0 ? list[list.length - 1] : null);
    }
    if (m === "POST") {
      const body = await readJson(req);
      if (body?.documents === undefined) {
        return send(res, 400, { documents: ["Este campo es obligatorio."] });
      }
      const existing = list.find((k) => k.status === "pending");
      if (existing) return send(res, 200, stripKyc(existing));
      const kyc = {
        id: uuid(),
        user_id: user.id,
        status: "pending",
        requested_at: iso(),
        resolved_at: null,
        resolved_by_user_id: null,
        documents: body.documents,
      };
      db.kyc.push(kyc);
      return send(res, 201, stripKyc(kyc));
    }
  }

  if (m === "GET" && a === "kyc" && b) {
    const user = requireAuth(req, res);
    if (!user) return;
    const kyc = db.kyc.find((k) => k.id === b && k.user_id === user.id);
    if (!kyc)
      return send(res, 404, { detail: "Verificación KYC no encontrada." });
    return send(res, 200, stripKyc(kyc));
  }

  // ---- meta ----
  if (m === "GET" && a === "meta") {
    return send(res, 200, {
      mode: "demo",
      simulated_money: true,
      compliance: {
        legal_review_pending: false,
        acknowledged: false,
        items: [],
      },
    });
  }

  // ---- pagos ----
  if (a === "payments" && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    if (m === "GET") {
      const list = db.payments.filter((p) => p.user_id === user.id);
      return send(res, 200, { count: list.length, results: list });
    }
    if (m === "POST") {
      const body = await readJson(req);
      const key = req.headers["idempotency-key"];
      if (!key) {
        return send(res, 400, {
          idempotency_key: ["El header `Idempotency-Key` es obligatorio."],
        });
      }
      const errors = {};
      if (!body?.direction) errors.direction = ["Este campo es obligatorio."];
      if (!body?.amount) errors.amount = ["Este campo es obligatorio."];
      if (!body?.currency) errors.currency = ["Este campo es obligatorio."];
      if (body?.direction === "transfer" && !body?.destination_user_id) {
        errors.destination_user_id = ["Este campo es obligatorio."];
      }
      if (Object.keys(errors).length > 0) return send(res, 400, errors);
      const existing = db.payments.find((p) => p.idempotency_key === key);
      if (existing) return send(res, 201, existing);
      const account = db.accounts.find(
        (acc) => acc.user_id === user.id && acc.currency === body.currency,
      );
      if (!account) {
        return send(res, 400, {
          currency: ["No tenés una billetera en esa moneda."],
        });
      }
      const payment = {
        id: uuid(),
        user_id: user.id,
        direction: body.direction,
        amount: money(Number(body.amount)),
        currency: body.currency,
        provider: "simulated",
        provider_reference: uuid(),
        status: "confirmed",
        ledger_transaction_id: null,
        checkout_url: "",
        created_at: iso(),
        updated_at: iso(),
        idempotency_key: key,
      };
      db.payments.push(payment);
      account.balance = money(Number(account.balance) - Number(payment.amount));
      db.transactions.push({
        id: uuid(),
        account_id: account.id,
        user_id: user.id,
        type: body.direction,
        amount: payment.amount,
        currency: payment.currency,
        description: body.description ?? `Pago ${body.direction}`,
        created_at: iso(),
        idempotency_key: key,
      });
      return send(res, 201, payment);
    }
  }

  if (m === "GET" && a === "payments" && b && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const payment = db.payments.find(
      (p) => p.id === b && p.user_id === user.id,
    );
    if (!payment) return send(res, 404, { detail: "Pago no encontrado." });
    return send(res, 200, payment);
  }

  // ---- presupuestos ----
  if (a === "budgets" && b === "categories" && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const list = db.categories.filter((cat) => cat.user_id === user.id);
    if (m === "GET")
      return send(res, 200, { count: list.length, results: list });
    if (m === "POST") {
      const body = await readJson(req);
      if (!body?.name)
        return send(res, 400, { name: ["Este campo es obligatorio."] });
      const category = {
        id: uuid(),
        user_id: user.id,
        name: body.name,
        created_at: iso(),
      };
      db.categories.push(category);
      return send(res, 201, category);
    }
  }

  if (a === "budgets" && b === "expenses" && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const list = db.expenses.filter((e) => e.user_id === user.id);
    if (m === "GET")
      return send(res, 200, { count: list.length, results: list });
    if (m === "POST") {
      const body = await readJson(req);
      if (!body?.category_id || !body?.ledger_transaction_id) {
        return send(res, 400, {
          detail: ["Faltan category_id o ledger_transaction_id."],
        });
      }
      const category = db.categories.find(
        (cat) => cat.id === body.category_id && cat.user_id === user.id,
      );
      if (!category)
        return send(res, 404, { detail: "Categoría no encontrada." });
      const expense = {
        id: uuid(),
        user_id: user.id,
        category_id: category.id,
        ledger_transaction_id: body.ledger_transaction_id,
        created_at: iso(),
      };
      db.expenses.push(expense);
      return send(res, 201, { ...expense, category });
    }
  }

  if (a === "budgets" && b && c === "status") {
    const user = requireAuth(req, res);
    if (!user) return;
    const budget = db.budgets.find((x) => x.id === b && x.user_id === user.id);
    if (!budget)
      return send(res, 404, { detail: "Presupuesto no encontrado." });
    const spent = db.expenses
      .filter(
        (e) => e.user_id === user.id && e.category_id === budget.category_id,
      )
      .reduce((acc, e) => {
        const tx = db.transactions.find(
          (t) => t.id === e.ledger_transaction_id,
        );
        return acc + Number(tx?.amount ?? 0);
      }, 0);
    const limit = Number(budget.limit_amount);
    const threshold = (limit * Number(budget.alert_threshold)) / 100;
    const now = new Date();
    return send(res, 200, {
      budget_id: budget.id,
      category_id: budget.category_id,
      period: budget.period,
      currency: budget.currency,
      year: now.getUTCFullYear(),
      month: now.getUTCMonth() + 1,
      limit_amount: budget.limit_amount,
      spent_amount: money(spent),
      remaining_amount: money(limit - spent),
      threshold_amount: money(threshold),
      alert_triggered: spent >= threshold,
    });
  }

  if (a === "budgets" && !b) {
    const user = requireAuth(req, res);
    if (!user) return;
    const list = db.budgets.filter((x) => x.user_id === user.id);
    if (m === "GET")
      return send(res, 200, { count: list.length, results: list });
    if (m === "POST") {
      const body = await readJson(req);
      const errors = {};
      if (!body?.category_id)
        errors.category_id = ["Este campo es obligatorio."];
      if (!body?.limit_amount)
        errors.limit_amount = ["Este campo es obligatorio."];
      if (!body?.currency) errors.currency = ["Este campo es obligatorio."];
      if (Object.keys(errors).length > 0) return send(res, 400, errors);
      const category = db.categories.find(
        (cat) => cat.id === body.category_id && cat.user_id === user.id,
      );
      if (!category)
        return send(res, 404, { detail: "Categoría no encontrada." });
      const budget = {
        id: uuid(),
        user_id: user.id,
        category_id: category.id,
        category,
        period: "monthly",
        limit_amount: money(Number(body.limit_amount)),
        currency: body.currency,
        alert_threshold: Number(body.alert_threshold ?? 50),
        created_at: iso(),
      };
      db.budgets.push(budget);
      return send(res, 201, budget);
    }
  }

  // ---- notificaciones ----
  if (m === "GET" && a === "notifications") {
    const user = requireAuth(req, res);
    if (!user) return;
    const list = db.notifications.filter((n) => n.user_id === user.id);
    return send(res, 200, { count: list.length, results: list });
  }

  // ---- reportes ----
  if (m === "GET" && a === "reports" && b) {
    const user = requireAuth(req, res);
    if (!user) return;
    const currency = url.searchParams.get("currency");
    if (!currency) {
      return send(res, 400, {
        currency: ["El parámetro currency es obligatorio (ARS o USD)."],
      });
    }
    const movements = db.transactions
      .filter((t) => t.user_id === user.id && t.currency === currency)
      .map((t) => ({
        id: t.id,
        type: t.type,
        amount: t.amount,
        currency: t.currency,
        occurred_at: t.created_at,
        description: t.description ?? "",
        is_reversed: false,
      }));
    if (b === "movements") {
      if (url.searchParams.get("export") === "csv") {
        res.writeHead(200, { "Content-Type": "text/csv; charset=utf-8" });
        res.end("id,type,amount,currency,occurred_at,description\n");
        return;
      }
      return send(res, 200, {
        currency,
        from: url.searchParams.get("from"),
        to: url.searchParams.get("to"),
        rows: movements,
        totals: { count: movements.length },
      });
    }
    if (b === "spending") {
      const byCategory = {};
      for (const movement of movements) {
        byCategory[movement.description] =
          (byCategory[movement.description] ?? 0) + Number(movement.amount);
      }
      return send(res, 200, {
        currency,
        categories: Object.entries(byCategory).map(([name, amount]) => ({
          name,
          amount: money(amount),
        })),
        total: money(movements.reduce((a, m2) => a + Number(m2.amount), 0)),
      });
    }
    if (b === "loans") {
      return send(res, 200, {
        currency,
        totals: { active: 0, paid: 0 },
        rows: [],
      });
    }
    if (b === "investments") {
      return send(res, 200, { currency, totals: { invested: 0 }, rows: [] });
    }
  }
  // ---- asistente IA ----
  if (a === "assistant" && b === "market" && m === "GET") {
    const user = requireAuth(req, res);
    if (!user) return;
    try {
      return send(res, 200, await getMarket());
    } catch {
      return send(res, 503, { detail: "No se pudo obtener el mercado." });
    }
  }

  if (a === "assistant" && b === "news" && m === "GET") {
    const user = requireAuth(req, res);
    if (!user) return;
    try {
      return send(res, 200, await getNews());
    } catch {
      return send(res, 503, { detail: "No se pudieron obtener las noticias." });
    }
  }

  if (a === "assistant" && b === "regulations" && m === "GET" && !c) {
    const user = requireAuth(req, res);
    if (!user) return;
    const items = listRegulations({
      category: url.searchParams.get("category") ?? undefined,
      q: url.searchParams.get("q") ?? undefined,
    });
    return send(res, 200, {
      disclaimer: DISCLAIMER,
      categories: CATEGORIES,
      items,
    });
  }

  if (a === "assistant" && b === "regulations" && c && m === "GET") {
    const user = requireAuth(req, res);
    if (!user) return;
    const item = getRegulation(c);
    if (!item) return send(res, 404, { detail: "Norma no encontrada." });
    return send(res, 200, { disclaimer: DISCLAIMER, item });
  }

  if (a === "assistant" && b === "chat" && m === "POST") {
    const user = requireAuth(req, res);
    if (!user) return;
    const body = await readJson(req);
    if (body == null) return send(res, 400, { detail: "JSON inválido." });
    try {
      return send(res, 200, await handleChat(body, user, db));
    } catch {
      return send(res, 503, {
        detail: "El asistente no está disponible ahora.",
      });
    }
  }

  return send(res, 404, { detail: "Ruta no encontrada." });
});

function stripKyc({ user_id, ...kyc }) {
  return kyc;
}

server.listen(PORT, () => {
  console.log(`Presto mock API escuchando en http://localhost:${PORT}/api/v1`);
  console.log("Usuarios de prueba:");
  console.log("  demo@presto.com   / demo123456   (prestatario)");
  console.log("  lender@presto.com / lender123456 (prestamista)");
});
