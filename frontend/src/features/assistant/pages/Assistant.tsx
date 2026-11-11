import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type {
  Account,
  InvestmentProduct,
  KYCVerification,
  MarketSnapshot,
  NewsFeed,
  RegulationsResponse,
} from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import { formatDate, formatMoney, formatRate } from "@/shared/lib/format";
import { SendIcon } from "@/shared/ui/icons";
import Mascot from "@/shared/ui/Mascot";

interface ChatEntry {
  role: "user" | "assistant";
  text: string;
}

const SUGGESTIONS = [
  "¿Cómo está bitcoin?",
  "Cotización del dólar",
  "Resumen de mi cuenta",
  "Últimas noticias",
  "¿Qué necesito para prestar?",
  "¿Puedo captar fondos?",
];

const INVESTOR_SUGGESTIONS = [
  "¿Cómo está bitcoin?",
  "¿Cómo está el mercado?",
  "¿Qué es invertir en Presto?",
  "¿Cómo van mis inversiones?",
  "Marco legal de inversiones",
  "¿Qué acciones me convienen?",
];

const GREETING =
  "¡Hola! Soy Presti, tu mago de finanzas. Te leo el mercado en la bola de cristal: dólar, bitcoin, acciones, tu cuenta y el marco legal para operar. ¿Qué querés saber?";

const INVESTOR_GREETING =
  "¡Hola! Soy Presti, tu asesor de inversiones. Te ayudo con mercado, acciones, bitcoin, tus posiciones en Presto y el marco legal. ¿Qué querés analizar?";

function formatPrice(n: number | null | undefined, currency = "USD"): string {
  if (n == null) return "—";
  return `${currency} ${n.toLocaleString("es-AR", {
    maximumFractionDigits: currency === "USD" ? 2 : 0,
  })}`;
}

function changeBadge(pct: number | null | undefined) {
  if (pct == null) return <span className="text-muted">—</span>;
  const up = pct >= 0;
  return (
    <span className={up ? "text-success-500" : "text-error-500"}>
      {up ? "▲" : "▼"} {Math.abs(pct).toFixed(2)}%
    </span>
  );
}

function InvestorGuide({
  kyc,
  accounts,
  products,
}: {
  kyc: KYCVerification | null;
  accounts: Account[];
  products: InvestmentProduct[];
}) {
  const [productId, setProductId] = useState("");
  const [amount, setAmount] = useState("");

  useEffect(() => {
    if (!productId && products.length > 0) {
      setProductId(products[0].id);
    }
  }, [productId, products]);

  const product =
    products.find((item) => item.id === productId) ?? products[0] ?? null;
  const arsWallet = accounts.find((account) => account.currency === "ARS");
  const balance = arsWallet?.balance ?? "0";
  const amountNumber = Number(amount.replace(",", "."));
  const minimum = Number(product?.min_amount ?? 0);
  const balanceNumber = Number(balance);
  const hasAmount = Number.isFinite(amountNumber) && amountNumber > 0;
  const interest =
    product && hasAmount
      ? amountNumber * (Number(product.annual_rate_tna) / 100) * (product.term_days / 365)
      : 0;
  const total = hasAmount ? amountNumber + interest : 0;
  const maturity =
    product != null
      ? new Date(Date.now() + product.term_days * 86_400_000)
      : null;
  const kycApproved = kyc?.status === "approved";
  const cheapest = products.reduce<InvestmentProduct | null>(
    (current, item) =>
      current == null || Number(item.min_amount) < Number(current.min_amount)
        ? item
        : current,
    null,
  );

  const warnings: string[] = [];
  if (product && hasAmount && amountNumber < minimum) {
    warnings.push(
      `El mínimo de ${product.name} es ${formatMoney(product.min_amount, product.currency)}.`,
    );
  }
  if (product && hasAmount && amountNumber > balanceNumber) {
    warnings.push(
      `Saldo insuficiente: tenés ${formatMoney(balance, "ARS")} en tu billetera ARS.`,
    );
  }

  return (
    <div className="card mb-6">
      <div className="section-header">
        <h2 className="mt-0 mb-0">Guía rápida para invertir</h2>
        <span className="badge info">Presti te guía</span>
      </div>

      <div className="card-grid">
        <div className="stat-card">
          <div className="label">1. Perfil</div>
          <div className="value">Inversor ✅</div>
          <div className="small text-muted">Tu perfil ya permite invertir.</div>
        </div>
        <div className="stat-card">
          <div className="label">2. KYC</div>
          <div className="value">{kycApproved ? "Aprobado ✅" : "Pendiente ⚠️"}</div>
          {!kycApproved && (
            <Link className="small text-brand-500" to="/perfil">
              Completar en Perfil y KYC
            </Link>
          )}
        </div>
        <div className="stat-card">
          <div className="label">3. Saldo ARS</div>
          <div className="value">{formatMoney(balance, "ARS")}</div>
          {balanceNumber <= 0 && (
            <Link className="small text-brand-500" to="/billetera">
              Depositar fondos
            </Link>
          )}
        </div>
        <div className="stat-card">
          <div className="label">4. Productos</div>
          <div className="value">{products.length}</div>
          <div className="small text-muted">
            {cheapest
              ? `Mínimo más bajo: ${formatMoney(cheapest.min_amount, cheapest.currency)}`
              : "No hay productos activos"}
          </div>
        </div>
      </div>

      <div className="alert warning">
        Antes de confirmar: el monto debe ser <strong>igual o mayor al mínimo</strong>,
        la moneda del producto debe coincidir con tu billetera y{" "}
        <strong>no vas a poder retirar el dinero antes del vencimiento</strong>.
      </div>

      <div className="rounded-xl border border-gray-200 p-4">
        <h3 className="mt-0">Simulador de inversión</h3>
        <div className="form-grid">
          <label className="field">
            Producto
            <select
              value={productId}
              onChange={(event) => setProductId(event.target.value)}
            >
              {products.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} · {item.term_days} días · {formatRate(item.annual_rate_tna)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Monto a invertir ({product?.currency ?? "ARS"})
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              placeholder="Ej. 10000"
            />
          </label>
        </div>

        {warnings.map((warning) => (
          <div className="alert error mt-2" key={warning}>
            {warning}
          </div>
        ))}

        {product && hasAmount && warnings.length === 0 && (
          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="stat-card">
              <div className="label">Interés estimado</div>
              <div className="value">{formatMoney(interest, product.currency)}</div>
            </div>
            <div className="stat-card">
              <div className="label">Total al vencimiento</div>
              <div className="value">{formatMoney(total, product.currency)}</div>
            </div>
            <div className="stat-card">
              <div className="label">Vencimiento</div>
              <div className="value" style={{ fontSize: "1rem" }}>
                {maturity ? formatDate(maturity.toISOString()) : "—"}
              </div>
            </div>
          </div>
        )}

        <div className="btn-row mt-3">
          <Link className="btn" to="/inversiones">
            Ir a invertir
          </Link>
          <span className="small text-muted">
            TNA nominal; la TEA equivalente puede ser distinta. No incluye impuestos.
          </span>
        </div>
      </div>

      <p className="small text-muted mb-0 mt-3">
        Presti muestra condiciones y riesgos, pero no hace recomendaciones
        personalizadas. Invertí solo dinero que no necesites antes del vencimiento.
      </p>
    </div>
  );
}

function AssistantReply({ text }: { text: string }) {
  return (
    <div className="flex flex-col gap-1">
      {text.split("\n").map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-1" />;
        const bold = line.match(/^\*(.+)\*$/);
        if (bold) {
          return (
            <div key={i} className="font-semibold text-gray-800">
              {bold[1]}
            </div>
          );
        }
        return (
          <div key={i} className="text-sm text-gray-700">
            {line}
          </div>
        );
      })}
    </div>
  );
}

function MarketCard({ market }: { market: MarketSnapshot | null }) {
  const coins = market?.coins ?? [];
  const btc = coins.find((c) => c.symbol === "BTC");
  const eth = coins.find((c) => c.symbol === "ETH");
  const sp = market?.indices.find((i) => i.symbol === "S&P 500");
  const merv = market?.indices.find((i) => i.symbol === "Merval");
  const dollar = market?.dollar;

  return (
    <div className="card">
      <div className="section-header">
        <h2 className="mt-0 mb-0">Mercado</h2>
        {market && (
          <span className="small text-muted">
            Actualizado{" "}
            {new Date(market.updated_at).toLocaleTimeString("es-AR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        )}
      </div>
      {market ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-xl bg-warning-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-gray-800">Bitcoin</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatPrice(btc?.price_usd)}
              </div>
            </div>
            <div className="text-sm font-medium">
              {changeBadge(btc?.change_24h_pct)}
            </div>
          </div>
          <div className="flex items-center justify-between rounded-xl bg-brand-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-gray-800">Ethereum</div>
              <div className="text-lg font-semibold text-gray-900">
                {formatPrice(eth?.price_usd)}
              </div>
            </div>
            <div className="text-sm font-medium">
              {changeBadge(eth?.change_24h_pct)}
            </div>
          </div>
          <div className="flex items-center justify-between rounded-xl bg-gray-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-gray-800">
                S&amp;P 500
              </div>
              <div className="text-lg font-semibold text-gray-900">
                {sp?.price_usd != null
                  ? sp.price_usd.toLocaleString("es-AR")
                  : "—"}
              </div>
            </div>
            <div className="text-sm font-medium">
              {changeBadge(sp?.change_24h_pct)}
            </div>
          </div>
          <div className="flex items-center justify-between rounded-xl bg-gray-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-gray-800">Merval</div>
              <div className="text-lg font-semibold text-gray-900">
                {merv?.price_local != null
                  ? Math.round(merv.price_local).toLocaleString("es-AR")
                  : "—"}
              </div>
            </div>
            <div className="text-sm font-medium">
              {changeBadge(merv?.change_24h_pct)}
            </div>
          </div>
          <div className="rounded-xl border border-gray-200 px-4 py-3">
            <div className="text-sm font-medium text-gray-800">
              Dólar en Argentina
            </div>
            <div className="mt-1 grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted">Blue venta: </span>
                <span className="font-semibold">
                  {formatPrice(dollar?.blue, "ARS")}
                </span>
              </div>
              <div>
                <span className="text-muted">Oficial venta: </span>
                <span className="font-semibold">
                  {formatPrice(dollar?.oficial, "ARS")}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="loading">Cargando mercado…</div>
      )}
    </div>
  );
}

function NewsCard({ news }: { news: NewsFeed | null }) {
  return (
    <div className="card">
      <div className="section-header">
        <h2 className="mt-0 mb-0">Noticias</h2>
      </div>
      {news && news.items.length > 0 ? (
        <ul className="space-y-3">
          {news.items.slice(0, 8).map((item, i) => (
            <li
              key={i}
              className="border-b border-gray-100 pb-3 last:border-0 last:pb-0"
            >
              {item.link ? (
                <a
                  href={item.link}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-gray-800 hover:text-brand-500"
                >
                  {item.title}
                </a>
              ) : (
                <span className="text-sm font-medium text-gray-800">
                  {item.title}
                </span>
              )}
              <div className="mt-1">
                <span className="badge info">{item.source}</span>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="loading">Cargando noticias…</div>
      )}
    </div>
  );
}

function ChatPanel({
  market,
  news,
  onOpenLegal,
}: {
  market: MarketSnapshot | null;
  news: NewsFeed | null;
  onOpenLegal: () => void;
}) {
  const { activeProfile } = useAuth();
  const isInvestor = activeProfile === "investor";
  const suggestions = isInvestor ? INVESTOR_SUGGESTIONS : SUGGESTIONS;
  const [messages, setMessages] = useState<ChatEntry[]>([
    { role: "assistant", text: isInvestor ? INVESTOR_GREETING : GREETING },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || sending) return;
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text: message }]);
    setSending(true);
    try {
      const res = await api.sendChat({ message });
      setMessages((prev) => [...prev, { role: "assistant", text: res.reply }]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo enviar el mensaje. Reintentá.",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <div className="xl:col-span-2">
        <div className="card flex h-[640px] flex-col">
          <div className="section-header">
            <h2 className="mt-0 mb-0 flex items-center gap-2">
              <span className="flex size-8 items-center justify-center rounded-full bg-brand-50">
                <Mascot
                  mood={sending ? "talking" : "idle"}
                  className="size-7 presti-speak"
                />
              </span>
              Presti
            </h2>
            <button
              type="button"
              className="btn secondary small"
              onClick={onOpenLegal}
            >
              Ver marco legal
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto p-1">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={
                  msg.role === "user"
                    ? "flex justify-end"
                    : "flex items-end gap-2"
                }
              >
                {msg.role === "assistant" && (
                  <Mascot
                    mood={
                      sending && i === messages.length - 1 ? "talking" : "idle"
                    }
                    className="size-9 shrink-0"
                  />
                )}
                <div
                  className={
                    msg.role === "user"
                      ? "max-w-[80%] rounded-2xl rounded-br-sm bg-brand-500 px-4 py-2.5 text-sm text-white"
                      : "max-w-[85%] rounded-2xl rounded-bl-sm border border-brand-100 bg-brand-50/50 px-4 py-2.5"
                  }
                >
                  {msg.role === "assistant" ? (
                    <AssistantReply text={msg.text} />
                  ) : (
                    <span className="text-sm">{msg.text}</span>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex items-end gap-2">
                <Mascot mood="talking" className="size-9 shrink-0" />
                <div className="rounded-2xl rounded-bl-sm border border-brand-100 bg-brand-50/50 px-4 py-2.5 text-sm text-muted">
                  Presti está consultando la bola de cristal…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {error && <div className="alert error mt-2">{error}</div>}

          <form
            className="mt-3 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <input
              type="text"
              className="flex-1"
              placeholder="Preguntale algo a Presti…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button
              type="submit"
              className="btn"
              disabled={sending || !input.trim()}
              aria-label="Enviar"
            >
              <SendIcon className="size-5" />
            </button>
          </form>
        </div>
      </div>

      <div className="space-y-6">
        <div className="card overflow-visible">
          <div className="flex flex-col items-center">
            <div className="presti-bubble rounded-2xl border border-brand-100 bg-white px-4 py-2 text-center text-sm font-medium text-gray-700">
              ¡Elegí una pregunta y te la respondo!
            </div>
            <Mascot
              mood={sending ? "talking" : "happy"}
              className="presti-float mt-4 h-44"
            />
            <div className="mt-2 text-center">
              <div className="font-semibold text-gray-800">Presti</div>
              <div className="small text-muted">Mago de finanzas de Presto</div>
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  className="presti-bubble rounded-full border border-brand-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-600 shadow-xs transition hover:bg-brand-50 disabled:opacity-50"
                  onClick={() => send(s)}
                  disabled={sending}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        <MarketCard market={market} />
        <NewsCard news={news} />
      </div>
    </div>
  );
}

function RegulationsPanel({
  market,
  news,
}: {
  market: MarketSnapshot | null;
  news: NewsFeed | null;
}) {
  const [data, setData] = useState<RegulationsResponse | null>(null);
  const [category, setCategory] = useState<string>("");
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const t = setTimeout(() => {
      api
        .getRegulations({
          category: category || undefined,
          q: query || undefined,
        })
        .then((res) => {
          if (!cancelled) setData(res);
        })
        .catch(() => {})
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [category, query]);

  const CATEGORY_COLORS: Record<string, string> = {
    prestamos: "bg-brand-50 text-brand-600 border-brand-200",
    entidades: "bg-warning-50 text-warning-600 border-warning-100",
    inversion: "bg-success-50 text-success-600 border-success-100",
    consumidor: "bg-gray-100 text-gray-600 border-gray-200",
    antilavado: "bg-error-50 text-error-600 border-error-100",
    general: "bg-gray-100 text-gray-600 border-gray-200",
  };

  const catLabel = (id: string) =>
    data?.categories.find((c) => c.id === id)?.label ?? id;

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <div className="xl:col-span-2">
        <div className="card">
          <div className="section-header">
            <h2 className="mt-0 mb-0">Marco legal</h2>
            <span className="small text-muted">
              {data ? `${data.items.length} normas` : ""}
            </span>
          </div>

          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <input
              type="text"
              placeholder="Buscar por ley, tema o palabra…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1"
            />
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className={
                "rounded-full border px-3 py-1 text-xs font-medium " +
                (!category
                  ? "border-brand-500 bg-brand-500 text-white"
                  : "border-gray-200 bg-white text-gray-600 hover:border-brand-300")
              }
              onClick={() => setCategory("")}
            >
              Todas
            </button>
            {data?.categories.map((c) => (
              <button
                key={c.id}
                type="button"
                className={
                  "rounded-full border px-3 py-1 text-xs font-medium " +
                  (category === c.id
                    ? "border-brand-500 bg-brand-500 text-white"
                    : "border-gray-200 bg-white text-gray-600 hover:border-brand-300")
                }
                onClick={() => setCategory(c.id)}
              >
                {c.label}
              </button>
            ))}
          </div>

          <div className="mt-4 space-y-3">
            {loading && !data && (
              <div className="loading">Cargando normas…</div>
            )}
            {data && data.items.length === 0 && (
              <div className="empty-state">
                No encontramos normas para tu búsqueda.
              </div>
            )}
            {data?.items.map((item) => {
              const open = openId === item.id;
              return (
                <div
                  key={item.id}
                  className="rounded-xl border border-gray-200 p-4 transition hover:border-brand-200"
                >
                  <button
                    type="button"
                    className="flex w-full items-start justify-between gap-3 text-left"
                    onClick={() => setOpenId(open ? null : item.id)}
                  >
                    <div>
                      <span
                        className={
                          "mb-1 inline-block rounded-full border px-2 py-0.5 text-[11px] font-medium " +
                          (CATEGORY_COLORS[item.category] ??
                            CATEGORY_COLORS.general)
                        }
                      >
                        {catLabel(item.category)}
                      </span>
                      <div className="font-semibold text-gray-800">
                        {item.title}
                      </div>
                    </div>
                    <span className="mt-1 text-gray-400">
                      {open ? "−" : "+"}
                    </span>
                  </button>

                  <p className="mt-2 text-sm text-gray-600">{item.summary}</p>

                  {open && (
                    <div className="mt-3 space-y-3 border-t border-gray-100 pt-3">
                      <ul className="space-y-1.5">
                        {item.key_points.map((p, i) => (
                          <li
                            key={i}
                            className="flex gap-2 text-sm text-gray-700"
                          >
                            <span className="text-brand-500">•</span>
                            <span>{p}</span>
                          </li>
                        ))}
                      </ul>

                      <div>
                        <div className="mb-1 text-xs font-semibold text-gray-500 uppercase">
                          Normas
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {item.norms.map((n, i) => (
                            <span key={i} className="badge info">
                              {n.code}
                              {n.note ? ` · ${n.note}` : ""}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="small text-muted">
                        <strong>Aplica a:</strong> {item.applies_to}
                      </div>

                      {item.links.length > 0 && (
                        <div className="flex flex-wrap gap-3">
                          {item.links.map((l, i) => (
                            <a
                              key={i}
                              href={l.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sm font-medium text-brand-500 hover:underline"
                            >
                              {l.label} ↗
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {data && (
            <div className="alert error mt-4 text-xs">
              <strong>Aviso:</strong> {data.disclaimer}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-6">
        <div className="card overflow-visible">
          <div className="flex flex-col items-center">
            <div className="presti-bubble rounded-2xl border border-brand-100 bg-white px-4 py-2 text-center text-sm font-medium text-gray-700">
              Conocé tus derechos y obligaciones
            </div>
            <Mascot mood="happy" className="presti-float mt-4 h-40" />
            <div className="mt-2 text-center">
              <div className="font-semibold text-gray-800">
                Presti te orienta
              </div>
              <div className="small text-muted">
                Información general basada en normativa argentina
              </div>
            </div>
          </div>
        </div>

        <MarketCard market={market} />
        <NewsCard news={news} />
      </div>
    </div>
  );
}

export default function Assistant() {
  const { activeProfile } = useAuth();
  const isInvestor = activeProfile === "investor";
  const [tab, setTab] = useState<"chat" | "legal">("chat");
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [news, setNews] = useState<NewsFeed | null>(null);
  const [investorKyc, setInvestorKyc] = useState<KYCVerification | null>(null);
  const [investorAccounts, setInvestorAccounts] = useState<Account[]>([]);
  const [investorProducts, setInvestorProducts] = useState<InvestmentProduct[]>([]);

  useEffect(() => {
    if (!isInvestor) return;
    let cancelled = false;
    Promise.all([
      api.getKyc().catch(() => null),
      api.listAccounts().catch(() => [] as Account[]),
      api.listProducts().catch(() => [] as InvestmentProduct[]),
    ]).then(([kyc, accounts, products]) => {
      if (cancelled) return;
      setInvestorKyc(kyc);
      setInvestorAccounts(accounts);
      setInvestorProducts(products);
    });
    return () => {
      cancelled = true;
    };
  }, [isInvestor]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [m, n] = await Promise.all([
        api.getMarket().catch(() => null),
        api.getNews().catch(() => null),
      ]);
      if (cancelled) return;
      setMarket(m);
      setNews(n);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <h1>Conocé a Presti</h1>
      <p className="page-subtitle">
        {isInvestor
          ? "Tu asesor de inversiones. Mercado en vivo, acciones, bitcoin, tus posiciones en Presto y el marco legal."
          : "Tu mago de finanzas. Mercado en vivo, noticias, tu cuenta y el marco legal para operar."}
      </p>

      {isInvestor && (
        <InvestorGuide
          kyc={investorKyc}
          accounts={investorAccounts}
          products={investorProducts}
        />
      )}

      <div className="mb-5 inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1">
        <button
          type="button"
          className={
            "rounded-md px-4 py-1.5 text-sm font-medium transition " +
            (tab === "chat"
              ? "bg-white text-brand-600 shadow-xs"
              : "text-gray-500")
          }
          onClick={() => setTab("chat")}
        >
          Chat
        </button>
        <button
          type="button"
          className={
            "rounded-md px-4 py-1.5 text-sm font-medium transition " +
            (tab === "legal"
              ? "bg-white text-brand-600 shadow-xs"
              : "text-gray-500")
          }
          onClick={() => setTab("legal")}
        >
          Marco legal
        </button>
      </div>

      {tab === "chat" ? (
        <ChatPanel
          market={market}
          news={news}
          onOpenLegal={() => setTab("legal")}
        />
      ) : (
        <RegulationsPanel market={market} news={news} />
      )}
    </>
  );
}
