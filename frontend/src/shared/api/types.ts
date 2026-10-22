// Tipos de la API: alias de los tipos **generados** desde `contract/openapi.yaml`
// con `pnpm gen:api`. No se escriben tipos de respuesta a mano
// (PROYECTO_FRONT.md §4.3 y §6.3).
import type { components } from "./schema";

type Schema<T extends keyof components["schemas"]> = components["schemas"][T];

export type Currency = Schema<"CurrencyEnum">;
/** Ordenamientos admitidos por `GET /matching/offers/` (query param). */
export type OrderingField = "rate" | "term" | "amount";
export type AccountKind = Schema<"KindEnum">;
export type LedgerTransactionType = Schema<"LedgerTransactionTypeEnum">;
export type CreateTransactionType = Schema<"CreateTransactionTypeEnum">;
export type OfferStatus = Schema<"OfferStatusEnum">;
export type LoanStatus = Schema<"LoanStatusEnum">;
export type InstallmentStatus = Schema<"InstallmentStatusEnum">;
export type PositionStatus = Schema<"PositionStatusEnum">;
export type KYCStatus = Schema<"KYCVerificationStatusEnum">;
export type InvestmentProductType = Schema<"InvestmentProductTypeEnum">;
export type InvestmentProductStatus = Schema<"InvestmentProductStatusEnum">;
export type PaymentDirection = Schema<"DirectionEnum">;
export type PaymentStatus = Schema<"PaymentStatusEnum">;
export type PaymentProvider = Schema<"ProviderEnum">;
export type BudgetPeriod = Schema<"PeriodEnum">;

export type User = Schema<"User">;
export type Login = Schema<"Login">;
export type Register = Schema<"Register">;
export type LoginResponse = Schema<"LoginResponse">;
export type TokenRefreshResponse = Schema<"TokenRefreshResponse">;
export type PatchedMeUpdate = Schema<"PatchedMeUpdate">;

export type Account = Schema<"Account">;
export type CreateAccount = Schema<"CreateAccount">;
export type Balance = Schema<"Balance">;
export type LedgerTransaction = Schema<"LedgerTransaction">;
export type CreateTransaction = Schema<"CreateTransaction">;

export type Offer = Schema<"Offer">;
export type CreateOffer = Schema<"CreateOffer">;
export type PatchedUpdateOffer = Schema<"PatchedUpdateOffer">;
export type OfferMatch = Schema<"OfferMatch">;
export type OfferComparison = Schema<"OfferComparison">;
export type CompareOffers = Schema<"CompareOffers">;
export type AcceptOffer = Schema<"AcceptOffer">;

export type Installment = Schema<"Installment">;
export type OfferTermsSnapshot = Schema<"OfferTermsSnapshot">;
export type Loan = Schema<"Loan">;
export type LoanDetail = Schema<"LoanDetail">;

export type InvestmentProduct = Schema<"InvestmentProduct">;
export type Position = Schema<"Position">;
export type PositionDetail = Schema<"PositionDetail">;
export type OpenPosition = Schema<"OpenPosition">;

export type KYCVerification = Schema<"KYCVerification">;
export type KYCRequest = Schema<"KYCRequest">;

export type Payment = Schema<"Payment">;
export type CreatePayment = Schema<"CreatePayment">;

export type Category = Schema<"Category">;
export type CreateCategory = Schema<"CreateCategory">;
export type Budget = Schema<"Budget">;
export type CreateBudget = Schema<"CreateBudget">;
export type BudgetStatus = Schema<"BudgetStatus">;
export type Expense = Schema<"Expense">;
export type CreateExpense = Schema<"CreateExpense">;

export type Meta = Schema<"Meta">;
export type Compliance = Schema<"Compliance">;
export type ComplianceItem = Schema<"ComplianceItem">;

export type Notification = Schema<"Notification">;

// ---- tipos del asistente (solo disponibles contra el mock) ----

export interface MarketCoin {
  symbol: string;
  name: string;
  price_usd: number | null;
  change_24h_pct: number | null;
}

export interface MarketIndex {
  symbol: string;
  name: string;
  price_usd?: number | null;
  price_local?: number | null;
  currency: string;
  change_24h_pct: number | null;
}

export interface MarketDollar {
  oficial: number | null;
  oficial_avg: number | null;
  blue: number | null;
  blue_avg: number | null;
}

export interface MarketSnapshot {
  updated_at: string;
  coins: MarketCoin[];
  indices: MarketIndex[];
  dollar: MarketDollar | null;
}

export interface NewsItem {
  title: string;
  link: string | null;
  published_at: string | null;
  source: string;
}

export interface NewsFeed {
  updated_at: string;
  items: NewsItem[];
}

export interface ChatMessage {
  message: string;
}

export interface ChatReply {
  reply: string;
  intent: "rules" | "llm" | "fallback" | "empty";
}

export type RegulationCategory =
  | "prestamos"
  | "entidades"
  | "inversion"
  | "consumidor"
  | "antilavado"
  | "general";

export interface RegulationNorm {
  code: string;
  note: string;
}

export interface RegulationLink {
  label: string;
  url: string;
}

export interface RegulationCard {
  id: string;
  category: RegulationCategory;
  title: string;
  summary: string;
  key_points: string[];
  norms: RegulationNorm[];
  links: RegulationLink[];
  applies_to: string;
}

export interface RegulationCategoryOption {
  id: RegulationCategory;
  label: string;
}

export interface RegulationsResponse {
  disclaimer: string;
  categories: RegulationCategoryOption[];
  items: RegulationCard[];
}
