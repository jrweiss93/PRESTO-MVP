import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { ApiError } from "@/shared/api/client";
import type {
  Account,
  BackupAccount,
  KYCVerification,
  Loan,
  Position,
} from "@/shared/api/types";
import { useAuth } from "@/features/auth/AuthContext";
import {
  KYC_STATUS_LABELS,
  LOAN_STATUS_LABELS,
  formatMoney,
} from "@/shared/lib/format";
import { PROFILE_LABELS } from "@/shared/lib/profiles";
import { sumDecimals, compareDecimals } from "@/shared/lib/decimal";
import {
  CheckCircleIcon,
  DollarLineIcon,
  PieChartIcon,
  UserMoneyIcon,
} from "@/shared/ui/icons";
import Mascot from "@/shared/ui/Mascot";

export default function Dashboard() {
  const { user, activeProfile } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [backupAccounts, setBackupAccounts] = useState<BackupAccount[]>([]);
  const [kyc, setKyc] = useState<KYCVerification | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [acc, ln, pos, kv, backup] = await Promise.all([
          api.listAccounts().catch(() => [] as Account[]),
          api.listLoans().catch(() => [] as Loan[]),
          api.listPositions().catch(() => [] as Position[]),
          api.getKyc().catch(() => null),
          api.listBackupAccounts().catch(() => [] as BackupAccount[]),
        ]);
        if (cancelled) return;
        setAccounts(acc);
        setLoans(ln);
        setPositions(pos);
        setKyc(kv);
        setBackupAccounts(backup);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "No se pudo cargar el resumen.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <div className="loading">Cargando resumen…</div>;

  const activeLoans = loans.filter((l) => l.status === "active");
  const activePositions = positions.filter((p) => p.status === "active");
  const totalInvested = sumDecimals(activePositions.map((p) => p.amount));
  const hasVerifiedBackup = backupAccounts.some(
    (account) => account.status === "verified",
  );

  return (
    <>
      <div className="dashboard-hero">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <span className="hero-kicker">
              Tu panel
              {activeProfile && ` · Perfil ${PROFILE_LABELS[activeProfile]}`}
            </span>
            <h1 className="mt-3">Hola, {user?.first_name || user?.email}</h1>
            <p className="mt-2 max-w-xl text-theme-sm text-white/75">
              Tu resumen financiero en Presto. Todo lo importante, en un solo
              lugar.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="hero-chip">Billetera ARS y USD</span>
              <span className="hero-chip">Dinero simulado</span>
              <span className="hero-chip">Presti te acompaña</span>
            </div>
          </div>
          <Mascot
            mood="happy"
            className="presti-float h-28 w-28 shrink-0 self-start sm:self-center"
          />
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      {kyc && kyc.status !== "approved" && (
        <div className="alert error">
          Tu verificación KYC está{" "}
          <strong>{KYC_STATUS_LABELS[kyc.status]}</strong>.{" "}
          <Link to="/perfil">Ir a Perfil y KYC</Link>
        </div>
      )}
      {!kyc && (
        <div className="alert error">
          Todavía no solicitaste la verificación KYC.{" "}
          <Link to="/perfil">Solicitála desde tu perfil</Link> para poder
          operar.
        </div>
      )}
      {activeProfile === "borrower" &&
        !backupAccounts.some((account) => account.status === "verified") && (
          <div className="alert warning">
            Para aceptar un préstamo necesitás una{" "}
            <Link to="/perfil#respaldo">cuenta de respaldo verificada</Link>.
          </div>
        )}

      <div className="card-grid">
        {accounts.length === 0 ? (
          <div className="stat-card flex items-start gap-4">
            <span className="flex items-center justify-center rounded-xl bg-brand-50 p-4 text-brand-500">
              <DollarLineIcon />
            </span>
            <div>
              <div className="label">Billeteras</div>
              <div className="value">—</div>
              <Link className="small text-brand-500" to="/billetera">
                Crear billetera
              </Link>
            </div>
          </div>
        ) : (
          accounts.map((acc) => (
            <div className="stat-card flex items-start gap-4" key={acc.id}>
              <span className="flex items-center justify-center rounded-xl bg-brand-50 p-4 text-brand-500">
                <DollarLineIcon />
              </span>
              <div>
                <div className="label">
                  Saldo {acc.currency} ·{" "}
                  {acc.kind === "user_wallet" ? "Billetera" : acc.kind}
                </div>
                <div className="value">
                  {formatMoney(acc.balance, acc.currency)}
                </div>
              </div>
            </div>
          ))
        )}
        {activeProfile !== "investor" && (
          <div className="stat-card flex items-start gap-4">
            <span className="flex items-center justify-center rounded-xl bg-warning-50 p-4 text-warning-500">
              <UserMoneyIcon />
            </span>
            <div>
              <div className="label">Préstamos activos</div>
              <div className="value">{activeLoans.length}</div>
              <Link className="small text-brand-500" to="/prestamos">
                Ver préstamos
              </Link>
            </div>
          </div>
        )}
        {activeProfile === "borrower" && (
          <div className="stat-card flex items-start gap-4">
            <span className="flex items-center justify-center rounded-xl bg-brand-50 p-4 text-brand-500">
              <CheckCircleIcon />
            </span>
            <div>
              <div className="label">Cuenta de respaldo</div>
              <div className="value" style={{ fontSize: "1.35rem" }}>
                {hasVerifiedBackup ? "Verificada" : "Pendiente"}
              </div>
              <Link className="small text-brand-500" to="/perfil#respaldo">
                Gestionar respaldo
              </Link>
            </div>
          </div>
        )}
        {activeProfile === "investor" && (
          <div className="stat-card flex items-start gap-4">
            <span className="flex items-center justify-center rounded-xl bg-success-50 p-4 text-success-500">
              <PieChartIcon />
            </span>
            <div>
              <div className="label">Inversiones activas</div>
              <div className="value">{activePositions.length}</div>
              {compareDecimals(totalInvested, "0") > 0 && (
                <div className="small text-muted">
                  Capital: {formatMoney(totalInvested)}
                </div>
              )}
              <Link className="small text-brand-500" to="/inversiones">
                Ver inversiones
              </Link>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="section-header">
          <h2 className="mt-0 mb-0">Accesos rápidos</h2>
        </div>
        <div className="btn-row">
          {activeProfile === "borrower" && (
            <Link className="btn" to="/marketplace">
              Buscar ofertas
            </Link>
          )}
          {activeProfile === "lender" && (
            <Link className="btn" to="/ofertas">
              Publicar oferta
            </Link>
          )}
          {activeProfile === "investor" && (
            <Link className="btn" to="/inversiones">
              Invertir
            </Link>
          )}
          <Link className="btn secondary" to="/billetera">
            Depositar fondos
          </Link>
        </div>
      </div>

      {activeProfile !== "investor" && activeLoans.length > 0 && (
        <div className="card">
          <h2>Tus préstamos activos</h2>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Capital</th>
                  <th>Tasa</th>
                  <th>Plazo</th>
                  <th>Estado</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {activeLoans.map((loan) => (
                  <tr key={loan.id}>
                    <td>{formatMoney(loan.principal, loan.currency)}</td>
                    <td>{loan.interest_rate}% TNA</td>
                    <td>{loan.term_months} meses</td>
                    <td>
                      <span className="badge info">
                        {LOAN_STATUS_LABELS[loan.status]}
                      </span>
                    </td>
                    <td>
                      <Link to={`/prestamos/${loan.id}`}>Ver detalle</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
