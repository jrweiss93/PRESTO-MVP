import {
  apiGet,
  apiPost,
  apiPatch,
  apiPostWithIdempotency,
  asArray,
} from "./client";
import type {
  Account,
  AcceptOffer,
  Balance,
  Budget,
  BudgetStatus,
  Category,
  ChatMessage,
  ChatReply,
  CompareOffers,
  Compliance,
  CreateAccount,
  CreateBudget,
  CreateCategory,
  CreateExpense,
  CreateOffer,
  CreatePayment,
  CreateTransaction,
  DetailMessage,
  EmailVerification,
  EmailVerificationResponse,
  Expense,
  Installment,
  InvestmentProduct,
  KYCRequest,
  KYCVerification,
  LedgerTransaction,
  Loan,
  LoanDetail,
  Login,
  LoginResponse,
  MarketSnapshot,
  Meta,
  NewsFeed,
  Notification,
  Offer,
  OfferComparison,
  OfferMatch,
  OpenPosition,
  OrderingField,
  PasswordResetConfirm,
  PasswordResetRequest,
  PatchedMeUpdate,
  PatchedUpdateOffer,
  Payment,
  Position,
  PositionDetail,
  RegulationCard,
  RegulationsResponse,
  Register,
  User,
} from "./types";

// Ordenamientos admitidos por `GET /matching/offers/` (query param).
export type { OrderingField };

// ---- auth ----

export function login(payload: Login): Promise<LoginResponse> {
  return apiPost<LoginResponse>("/auth/login/", payload);
}

export function register(payload: Register): Promise<User> {
  return apiPost<User>("/auth/register/", payload);
}

export function me(): Promise<User> {
  return apiGet<User>("/auth/me/");
}

export function updateMe(payload: PatchedMeUpdate): Promise<User> {
  return apiPatch<User>("/auth/me/", payload);
}

/** Cierra la sesión: el backend blacklistea el refresh y borra la cookie. */
export function logout(): Promise<void> {
  return apiPost<void>("/auth/logout/");
}

/** Pide el enlace de reseteo. Responde siempre lo mismo, exista o no la cuenta. */
export function requestPasswordReset(
  payload: PasswordResetRequest,
): Promise<DetailMessage> {
  return apiPost<DetailMessage>("/auth/password-reset/", payload);
}

/** Cambia la contraseña con el uid y el token del enlace. */
export function confirmPasswordReset(
  payload: PasswordResetConfirm,
): Promise<DetailMessage> {
  return apiPost<DetailMessage>("/auth/password-reset/confirm/", payload);
}

/** Confirma el email con el uid y el token del enlace. */
export function verifyEmail(
  payload: EmailVerification,
): Promise<EmailVerificationResponse> {
  return apiPost<EmailVerificationResponse>("/auth/email/verify/", payload);
}

/** Reenvía el correo de verificación al usuario autenticado. */
export function resendEmailVerification(): Promise<DetailMessage> {
  return apiPost<DetailMessage>("/auth/email/resend/");
}

// ---- meta (modo, bandera de revisión legal) ----

export function getMeta(): Promise<Meta> {
  return apiGet<Meta>("/meta/");
}

export async function getCompliance(): Promise<Compliance | null> {
  const meta = await getMeta();
  return meta?.compliance ?? null;
}

// ---- ledger ----

export async function listAccounts(): Promise<Account[]> {
  return asArray(await apiGet<Account | Account[]>("/ledger/accounts/"));
}

export function createAccount(payload: CreateAccount): Promise<Account> {
  return apiPost<Account>("/ledger/accounts/", payload);
}

export function getBalance(accountId: string): Promise<Balance> {
  return apiGet<Balance>(`/ledger/accounts/${accountId}/balance/`);
}

export async function listTransactions(): Promise<LedgerTransaction[]> {
  return asArray(
    await apiGet<LedgerTransaction | LedgerTransaction[]>(
      "/ledger/transactions/",
    ),
  );
}

/** Movimiento de dinero: el backend exige `Idempotency-Key`. */
export function createTransaction(
  payload: CreateTransaction,
  idempotencyKey: string,
): Promise<LedgerTransaction> {
  return apiPostWithIdempotency<LedgerTransaction>(
    "/ledger/transactions/",
    payload,
    idempotencyKey,
  );
}

// ---- offers (propias) ----

export async function listMyOffers(): Promise<Offer[]> {
  return asArray(await apiGet<Offer | Offer[]>("/offers/"));
}

export function createOffer(payload: CreateOffer): Promise<Offer> {
  return apiPost<Offer>("/offers/", payload);
}

export function getOffer(offerId: string): Promise<Offer> {
  return apiGet<Offer>(`/offers/${offerId}/`);
}

export function updateOffer(
  offerId: string,
  payload: PatchedUpdateOffer,
): Promise<Offer> {
  return apiPatch<Offer>(`/offers/${offerId}/`, payload);
}

// ---- matching (marketplace) ----

export interface OfferFilters {
  amount_min?: string;
  amount_max?: string;
  currency?: string;
  max_rate?: string;
  term_months?: number;
  ordering?: OrderingField;
}

export function buildOfferQuery(filters: OfferFilters): string {
  const params = new URLSearchParams();
  if (filters.amount_min) params.set("amount_min", filters.amount_min);
  if (filters.amount_max) params.set("amount_max", filters.amount_max);
  if (filters.currency) params.set("currency", filters.currency);
  if (filters.max_rate) params.set("max_rate", filters.max_rate);
  if (filters.term_months)
    params.set("term_months", String(filters.term_months));
  if (filters.ordering) params.set("ordering", filters.ordering);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function searchOffers(
  filters: OfferFilters,
): Promise<OfferMatch[]> {
  const data = await apiGet<OfferMatch | OfferMatch[]>(
    `/matching/offers/${buildOfferQuery(filters)}`,
  );
  return asArray(data);
}

export async function compareOffers(
  payload: CompareOffers,
): Promise<OfferComparison[]> {
  const data = await apiPost<OfferComparison | OfferComparison[]>(
    "/matching/comparisons/",
    payload,
  );
  return asArray(data);
}

// ---- loans ----

export async function listLoans(): Promise<Loan[]> {
  return asArray(await apiGet<Loan | Loan[]>("/loans/"));
}

/** Aceptar una oferta: mueve dinero, exige `Idempotency-Key`. */
export function acceptOffer(
  payload: AcceptOffer,
  idempotencyKey: string,
): Promise<Loan> {
  return apiPostWithIdempotency<Loan>("/loans/", payload, idempotencyKey);
}

export function getLoan(loanId: string): Promise<LoanDetail> {
  return apiGet<LoanDetail>(`/loans/${loanId}/`);
}

export function payInstallment(
  loanId: string,
  number: number,
): Promise<Installment> {
  return apiPost<Installment>(`/loans/${loanId}/installments/${number}/pay/`);
}

// ---- investments ----

export async function listProducts(): Promise<InvestmentProduct[]> {
  return asArray(
    await apiGet<InvestmentProduct | InvestmentProduct[]>(
      "/investments/products/",
    ),
  );
}

export async function listPositions(): Promise<Position[]> {
  return asArray(
    await apiGet<Position | Position[]>("/investments/positions/"),
  );
}

/** Invertir: mueve dinero, exige `Idempotency-Key`. */
export function openPosition(
  payload: OpenPosition,
  idempotencyKey: string,
): Promise<Position> {
  return apiPostWithIdempotency<Position>(
    "/investments/positions/",
    payload,
    idempotencyKey,
  );
}

export function getPosition(positionId: string): Promise<PositionDetail> {
  return apiGet<PositionDetail>(`/investments/positions/${positionId}/`);
}

// ---- kyc ----

export async function getKyc(): Promise<KYCVerification | null> {
  const data = await apiGet<KYCVerification | KYCVerification[] | null>(
    "/kyc/",
  );
  if (data == null) return null;
  return asArray(data)[0] ?? null;
}

export function requestKyc(payload: KYCRequest): Promise<KYCVerification> {
  return apiPost<KYCVerification>("/kyc/", payload);
}

export function getKycById(verificationId: string): Promise<KYCVerification> {
  return apiGet<KYCVerification>(`/kyc/${verificationId}/`);
}

// ---- pagos ----

export async function listPayments(): Promise<Payment[]> {
  return asArray(await apiGet<Payment | Payment[]>("/payments/"));
}

export function getPayment(paymentId: string): Promise<Payment> {
  return apiGet<Payment>(`/payments/${paymentId}/`);
}

/** Pagar: mueve dinero, exige `Idempotency-Key`. */
export function createPayment(
  payload: CreatePayment,
  idempotencyKey: string,
): Promise<Payment> {
  return apiPostWithIdempotency<Payment>("/payments/", payload, idempotencyKey);
}

// ---- presupuestos ----

export async function listCategories(): Promise<Category[]> {
  return asArray(await apiGet<Category | Category[]>("/budgets/categories/"));
}

export function createCategory(payload: CreateCategory): Promise<Category> {
  return apiPost<Category>("/budgets/categories/", payload);
}

export async function listBudgets(): Promise<Budget[]> {
  return asArray(await apiGet<Budget | Budget[]>("/budgets/"));
}

export function createBudget(payload: CreateBudget): Promise<Budget> {
  return apiPost<Budget>("/budgets/", payload);
}

export function getBudgetStatus(budgetId: string): Promise<BudgetStatus> {
  return apiGet<BudgetStatus>(`/budgets/${budgetId}/status/`);
}

export async function listExpenses(): Promise<Expense[]> {
  return asArray(await apiGet<Expense | Expense[]>("/budgets/expenses/"));
}

export function createExpense(payload: CreateExpense): Promise<Expense> {
  return apiPost<Expense>("/budgets/expenses/", payload);
}

// ---- reportes ----

export interface ReportParams {
  currency: string;
  from?: string;
  to?: string;
}

export function buildReportQuery(params: ReportParams): string {
  const search = new URLSearchParams();
  search.set("currency", params.currency);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  return `?${search.toString()}`;
}

export function getSpendingReport(params: ReportParams): Promise<unknown> {
  return apiGet(`/reports/spending/${buildReportQuery(params)}`);
}

export function getMovementsReport(params: ReportParams): Promise<unknown> {
  return apiGet(`/reports/movements/${buildReportQuery(params)}`);
}

export function getLoansReport(params: ReportParams): Promise<unknown> {
  return apiGet(`/reports/loans/${buildReportQuery(params)}`);
}

export function getInvestmentsReport(params: ReportParams): Promise<unknown> {
  return apiGet(`/reports/investments/${buildReportQuery(params)}`);
}

/** Descarga el CSV del reporte de movimientos (el backend responde texto plano). */
export async function downloadMovementsCsv(
  params: ReportParams,
): Promise<string> {
  const search = new URLSearchParams(buildReportQuery(params).slice(1));
  search.set("export", "csv");
  const res = await fetch(
    `${import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1"}/reports/movements/?${search.toString()}`,
    { credentials: "include" },
  );
  if (!res.ok)
    throw new Error(`No se pudo descargar el reporte (${res.status})`);
  return res.text();
}

// ---- notificaciones ----

export async function listNotifications(): Promise<Notification[]> {
  return asArray(
    await apiGet<Notification | Notification[]>("/notifications/"),
  );
}

// ---- asistente IA (solo contra el mock) ----

export function getMarket(): Promise<MarketSnapshot> {
  return apiGet<MarketSnapshot>("/assistant/market/");
}

export function getNews(): Promise<NewsFeed> {
  return apiGet<NewsFeed>("/assistant/news/");
}

export function sendChat(payload: ChatMessage): Promise<ChatReply> {
  return apiPost<ChatReply>("/assistant/chat/", payload);
}

export function getRegulations(params?: {
  category?: string;
  q?: string;
}): Promise<RegulationsResponse> {
  const search = new URLSearchParams();
  if (params?.category) search.set("category", params.category);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  return apiGet<RegulationsResponse>(
    `/assistant/regulations/${qs ? `?${qs}` : ""}`,
  );
}

export function getRegulation(id: string): Promise<{
  disclaimer: string;
  item: RegulationCard;
}> {
  return apiGet(`/assistant/regulations/${id}/`);
}
