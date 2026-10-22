import { useEffect, useState } from "react";
import * as api from "@/shared/api/endpoints";
import type { Budget, BudgetStatus, Category } from "@/shared/api/types";
import { formatMoney, formatPercent } from "@/shared/lib/format";
import { decimalPercent } from "@/shared/lib/decimal";

export default function Budgets() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [statuses, setStatuses] = useState<Record<string, BudgetStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryName, setCategoryName] = useState("");
  const [limit, setLimit] = useState("");
  const [threshold, setThreshold] = useState("50");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [budgetList, categoryList] = await Promise.all([
        api.listBudgets(),
        api.listCategories(),
      ]);
      setBudgets(budgetList);
      setCategories(categoryList);
      const entries = await Promise.all(
        budgetList.map(async (budget) => {
          try {
            const status = await api.getBudgetStatus(budget.id);
            return [budget.id, status] as const;
          } catch {
            return [budget.id, null] as const;
          }
        }),
      );
      const map: Record<string, BudgetStatus> = {};
      for (const [id, status] of entries) {
        if (status) map[id] = status;
      }
      setStatuses(map);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudieron cargar los presupuestos",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function createCategory(event: React.FormEvent) {
    event.preventDefault();
    if (categoryName.trim() === "") return;
    try {
      await api.createCategory({ name: categoryName.trim() });
      setCategoryName("");
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No se pudo crear la categoría",
      );
    }
  }

  async function createBudget(event: React.FormEvent) {
    event.preventDefault();
    const categoryId = categories[0]?.id;
    if (!categoryId || limit.trim() === "") return;
    try {
      await api.createBudget({
        category_id: categoryId,
        limit_amount: limit.trim(),
        currency: budgets[0]?.currency ?? "ARS",
        alert_threshold: Number(threshold),
      });
      setLimit("");
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No se pudo crear el presupuesto",
      );
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-title-sm font-semibold text-gray-800">
          Presupuestos
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Límites por categoría y aviso cuando se alcanza el umbral.
        </p>
      </header>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </p>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-gray-200 bg-white p-5">
          <h2 className="text-base font-semibold text-gray-800">
            Nueva categoría
          </h2>
          <form className="mt-4 flex gap-2" onSubmit={createCategory}>
            <input
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="Supermercado"
              value={categoryName}
              onChange={(e) => setCategoryName(e.target.value)}
              required
            />
            <button
              className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white"
              type="submit"
            >
              Crear
            </button>
          </form>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5">
          <h2 className="text-base font-semibold text-gray-800">
            Nuevo presupuesto
          </h2>
          <form
            className="mt-4 grid gap-3 sm:grid-cols-3"
            onSubmit={createBudget}
          >
            <input
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              inputMode="decimal"
              placeholder="Límite 80000.00"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              required
            />
            <input
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              inputMode="numeric"
              placeholder="Umbral %"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
            <button
              className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white"
              type="submit"
              disabled={categories.length === 0}
            >
              Crear
            </button>
          </form>
          {categories.length === 0 && (
            <p className="mt-2 text-xs text-gray-500">
              Creá primero una categoría de gasto.
            </p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white p-5">
        <h2 className="text-base font-semibold text-gray-800">
          Mis presupuestos
        </h2>
        {loading ? (
          <p className="mt-3 text-sm text-gray-500">Cargando…</p>
        ) : budgets.length === 0 ? (
          <p className="mt-3 text-sm text-gray-500">
            Todavía no tenés presupuestos cargados.
          </p>
        ) : (
          <ul className="mt-3 space-y-4">
            {budgets.map((budget) => {
              const status = statuses[budget.id];
              const spent = status?.spent_amount ?? "0";
              const limitAmount = status?.limit_amount ?? budget.limit_amount;
              const ratio = decimalPercent(spent, limitAmount);
              return (
                <li key={budget.id}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium text-gray-800">
                      {budget.category.name}
                    </p>
                    <p className="text-sm text-gray-600">
                      {formatMoney(spent, budget.currency)} de{" "}
                      {formatMoney(limitAmount, budget.currency)}
                    </p>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-100">
                    <div
                      className={
                        status?.alert_triggered
                          ? "h-full bg-red-500"
                          : "h-full bg-brand-500"
                      }
                      style={{ width: `${Math.min(ratio, 100)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    Umbral de aviso {formatPercent(budget.alert_threshold)}
                    {status?.alert_triggered && (
                      <span className="text-red-500"> · alerta activa</span>
                    )}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
