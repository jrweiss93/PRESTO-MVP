import { Link } from "react-router-dom";

const SECTIONS = [
  {
    title: "1. Qué es esta demo",
    body: "Presto es una aplicación de finanzas personales, inversiones y préstamos entre personas. Esta instancia es una demostración pública con datos de ejemplo y dinero simulado. No es un servicio financiero habilitado para operar con fondos reales.",
  },
  {
    title: "2. Dinero simulado",
    body: "Los depósitos, retiros, transferencias, préstamos e inversiones se registran en un libro mayor interno, pero no mueven dinero real ni están conectados a una cuenta bancaria o billetera virtual. Los saldos que se muestran no son exigibles.",
  },
  {
    title: "3. No es oferta ni asesoramiento",
    body: "Nada de lo que muestra la aplicación constituye una oferta pública de valores, una recomendación de inversión ni asesoramiento financiero, legal o contable. Las tasas y los productos son ejemplos. Antes de operar con dinero real hay que contar con el encuadre regulatorio correspondiente (BCRA, CNV y UIF, según el caso).",
  },
  {
    title: "4. Datos personales",
    body: "La demo usa cuentas de prueba y no debe usarse con datos personales reales. El KYC de la demo es una simulación administrativa: no valida documentos ni reemplaza un proceso de identificación. La política de privacidad definitiva se publicará antes de habilitar usuarios reales.",
  },
  {
    title: "5. Alcance técnico",
    body: "El asistente Presti responde con reglas y contenido curado. La información de mercado y las noticias provienen de fuentes externas y pueden estar demoradas o no disponibles. Las fichas regulatorias son información general y pueden quedar desactualizadas.",
  },
  {
    title: "6. Contacto",
    body: "Para consultas sobre la demo o el proyecto, escribí al equipo responsable de Presto. Esta página es un borrador de alcance para la demostración y no reemplaza la revisión legal previa a un lanzamiento.",
  },
];

export default function Legal() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-5 py-4">
          <Link to="/" className="text-title-sm font-semibold text-gray-800">
            Presto<span className="text-brand-500">.</span>
          </Link>
          <Link
            to="/"
            className="text-theme-sm text-gray-600 hover:text-gray-900"
          >
            Volver al inicio
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-5 py-12">
        <span className="inline-flex rounded-full bg-amber-50 px-3 py-1 text-theme-xs font-medium text-amber-800">
          Documento de la demo
        </span>
        <h1 className="mt-4 text-3xl font-semibold text-gray-900">
          Legal y alcance de la demostración
        </h1>
        <p className="mt-3 text-theme-sm text-gray-600">
          Este texto explica qué se puede esperar de esta instancia de Presto.
          No es un contrato de términos y condiciones definitivo.
        </p>

        <div className="mt-10 space-y-8">
          {SECTIONS.map((section) => (
            <section key={section.title}>
              <h2 className="text-lg font-semibold text-gray-800">
                {section.title}
              </h2>
              <p className="mt-2 text-theme-sm leading-6 text-gray-600">
                {section.body}
              </p>
            </section>
          ))}
        </div>

        <div className="mt-10 rounded-lg border border-gray-200 bg-gray-50 p-5 text-theme-sm text-gray-600">
          <p className="font-medium text-gray-800">
            Antes de un lanzamiento real
          </p>
          <p className="mt-1">
            Hay que reemplazar este borrador por términos y condiciones,
            política de privacidad y el encuadre regulatorio revisados por un
            profesional. Los pendientes están listados en{" "}
            <code className="rounded bg-white px-1 py-0.5 text-theme-xs">
              docs/regulatorio-bcra.md
            </code>{" "}
            del repositorio.
          </p>
        </div>

        <Link to="/" className="btn mt-8 inline-block">
          Volver al inicio
        </Link>
      </main>
    </div>
  );
}
