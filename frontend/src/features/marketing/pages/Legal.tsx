import { Link } from "react-router-dom";
import ThemeToggle from "@/shared/ui/ThemeToggle";

const TERMS_SECTIONS = [
  {
    title: "1. Aceptación de los términos",
    body: "Al registrarte y usar Presto aceptás estos Términos y Condiciones y la Política de Privacidad. Si no estás de acuerdo, no crees una cuenta ni uses la aplicación.",
  },
  {
    title: "2. Descripción del servicio",
    body: "Presto es una aplicación de finanzas personales que reúne una billetera en pesos y dólares, préstamos entre personas, plazos fijos, presupuestos y un asistente. Conecta a personas que quieren prestar con personas que necesitan financiarse.",
  },
  {
    title: "3. Carácter de demostración y dinero simulado",
    body: "Esta instancia es una demostración pública. Los depósitos, retiros, transferencias, préstamos e inversiones se registran en un libro mayor interno, pero no mueven dinero real ni están conectados a una cuenta bancaria o billetera virtual. Los saldos que se muestran no son exigibles ni canjeables por dinero real.",
  },
  {
    title: "4. Registro y responsabilidad de la cuenta",
    body: "Creás tu cuenta con un email y una contraseña. Sos responsable de mantener la confidencialidad de tus credenciales y de toda la actividad que ocurra en tu cuenta. Notificanos de inmediato ante cualquier uso no autorizado.",
  },
  {
    title: "5. Verificación de identidad (KYC)",
    body: "Para operar con dinero, aunque sea simulado, la aplicación exige una verificación de identidad (KYC). En esta demo el KYC y la validación biométrica son simulaciones administrativas: no validan documentos reales ni reemplazan un proceso de identificación regulado.",
  },
  {
    title: "6. Operaciones de la plataforma",
    body: "Las ofertas, los préstamos, las cuotas y los plazos fijos se calculan con reglas internas y tasas de ejemplo. La comparación muestra cuota, interés y costo total antes de aceptar, pero esos valores son ilustrativos y no representan condiciones de un producto real.",
  },
  {
    title: "7. Perfiles de usuario",
    body: "Al registrarte elegís un perfil: prestatario, prestamista o inversor. Cada perfil habilita operaciones distintas y el perfil es fijo para la cuenta. Un prestatario no puede publicar ofertas, un prestamista no puede invertir y así sucesivamente.",
  },
  {
    title: "8. Uso aceptable y prohibido",
    body: "No uses la aplicación para actividades ilícitas, fraudulentas o que infrinjan derechos de terceros. No intentes manipular el sistema, acceder a cuentas ajenas ni automatizar el uso de forma abusiva.",
  },
  {
    title: "9. No constituye oferta ni asesoramiento",
    body: "Nada de lo que muestra la aplicación constituye una oferta pública de valores, una recomendación de inversión ni asesoramiento financiero, legal, contable o impositivo. Antes de operar con dinero real hay que contar con el encuadre regulatorio correspondiente (BCRA, CNV y UIF, según el caso).",
  },
  {
    title: "10. Propiedad intelectual",
    body: "La marca Presto, el diseño, el código y los contenidos de la aplicación pertenecen a sus respectivos titulares. No se otorga ninguna licencia más allá del uso de la aplicación conforme a estos términos.",
  },
  {
    title: "11. Disponibilidad y modificaciones",
    body: "La aplicación puede quedar temporalmente fuera de servicio por mantenimiento o por limitaciones del entorno de demostración. Podemos modificar estos términos en cualquier momento; la versión vigente es la que se publica en esta página.",
  },
  {
    title: "12. Limitación de responsabilidad",
    body: "La aplicación se ofrece \"tal cual\" y sin garantías. En la máxima medida permitida por la ley, Presto no será responsable por daños directos o indirectos derivados del uso o de la imposibilidad de uso de la aplicación, especialmente en una instancia de demostración con dinero simulado.",
  },
  {
    title: "13. Suspensión y terminación",
    body: "Podemos suspender o cancelar una cuenta que incumpla estos términos, que intente vulnerar la seguridad o que use la aplicación de forma abusiva. Podés dejar de usar la aplicación en cualquier momento.",
  },
  {
    title: "14. Legislación aplicable",
    body: "Estos términos se rigen por la legislación de la República Argentina. Cualquier controversia se someterá a los tribunales competentes de la Ciudad Autónoma de Buenos Aires, salvo disposición legal en contrario.",
  },
  {
    title: "15. Contacto",
    body: "Para consultas sobre estos términos, la demo o el proyecto, escribí al equipo responsable de Presto.",
  },
];

const PRIVACY_SECTIONS = [
  {
    title: "Datos que recopilamos",
    body: "Recopilamos los datos que cargás al registrarte y operar: email, teléfono, fecha de nacimiento, país y el detalle de tus movimientos (depósitos, transferencias, préstamos e inversiones).",
  },
  {
    title: "Uso de los datos",
    body: "Usamos tus datos para darte acceso, llevar el registro de tus operaciones, mostrar tu saldo y tus cuotas, y enviarte los avisos que activaste. No vendemos ni compartimos tus datos con terceros para fines publicitarios.",
  },
  {
    title: "Datos biométricos",
    body: "La validación biométrica de esta demo es una simulación: no se procesan ni se almacenan datos biométricos reales. Solo se guarda una referencia (hash) de la muestra simulada y el resultado de la verificación.",
  },
  {
    title: "Datos en la demo",
    body: "Esta instancia usa cuentas de prueba y no debe utilizarse con datos personales reales ni sensibles. Si cargaste información real, solicitá su eliminación al equipo responsable.",
  },
  {
    title: "Tus derechos",
    body: "Podés solicitar el acceso, la rectificación o la eliminación de tus datos escribiendo al equipo responsable. En una instancia de demostración, la eliminación puede implicar el reinicio del escenario de ejemplo.",
  },
];

function SectionList({ sections }: { sections: { title: string; body: string }[] }) {
  return (
    <div className="space-y-8">
      {sections.map((section) => (
        <section key={section.title}>
          <h2 className="text-lg font-semibold text-gray-800">{section.title}</h2>
          <p className="mt-2 text-theme-sm leading-6 text-gray-600">{section.body}</p>
        </section>
      ))}
    </div>
  );
}

export default function Legal() {
  return (
    <div className="landing-page min-h-screen bg-white dark:bg-gray-950">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-5 py-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-title-sm font-semibold text-gray-800"
          >
            <span className="brand-mark flex size-8 items-center justify-center rounded-lg text-lg font-semibold text-white">
              P
            </span>
            Presto<span className="text-brand-500">.</span>
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              to="/"
              className="text-theme-sm text-gray-600 hover:text-gray-900"
            >
              Volver al inicio
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-5 py-12">
        <span className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-theme-xs font-medium text-brand-600">
          Términos y Condiciones · Demo
        </span>
        <h1 className="mt-4 text-3xl font-semibold text-gray-900">
          Términos y Condiciones
        </h1>
        <p className="mt-3 text-theme-sm text-gray-600">
          Última actualización: 8 de noviembre de 2026. Estos términos rigen el
          uso de Presto, una demostración pública con dinero simulado.
        </p>

        <div className="mt-10">
          <SectionList sections={TERMS_SECTIONS} />
        </div>

        <div className="mt-14 border-t border-gray-200 pt-10">
          <h2 className="text-2xl font-semibold text-gray-900">
            Política de Privacidad
          </h2>
          <div className="mt-6">
            <SectionList sections={PRIVACY_SECTIONS} />
          </div>
        </div>

        <div className="mt-10 rounded-lg border border-amber-200 bg-amber-50 p-5 text-theme-sm text-gray-700 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p className="font-medium text-amber-900 dark:text-amber-200">
            Antes de un lanzamiento real
          </p>
          <p className="mt-1 text-amber-900/80 dark:text-amber-200/80">
            Este texto aplica a la demo. Para operar con dinero real hay que
            reemplazarlo por términos, política de privacidad y encuadre
            regulatorio revisados por un profesional. Los pendientes están
            listados en{" "}
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
