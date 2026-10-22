// Marco legal (Argentina) para el asistente Presti.
// Contenido curado: fichas informativas con referencias a leyes, decretos y
// organismos. NO es asesoramiento legal — cada ficha incluye esa advertencia.
// Fuente de cada norma: InfoLEG / Boletín Oficial / BCRA / CNV.

/** @typedef {"prestamos"|"entidades"|"inversion"|"consumidor"|"antilavado"|"general"} RegCategory */

export const DISCLAIMER =
  "Esta información es de carácter general y educativo, no constituye asesoramiento legal. " +
  "Antes de operar, consultá con un abogado y verificá el texto vigente en InfoLEG, el BCRA o la CNV.";

export const CATEGORIES = [
  { id: "prestamos", label: "Préstamos y mutuo" },
  { id: "entidades", label: "Entidades y BCRA" },
  { id: "inversion", label: "Inversión y CNV" },
  { id: "consumidor", label: "Defensa del consumidor" },
  { id: "antilavado", label: "Antilavado (UIF)" },
  { id: "general", label: "General" },
];

export const REGULATIONS = [
  {
    id: "mutuo-ccyc",
    category: "prestamos",
    title: "Mutuo entre particulares (Código Civil y Comercial)",
    summary:
      "El préstamo entre personas se rige por el contrato de mutuo: quien recibe dinero se obliga a devolver otro tanto de la misma especie y calidad. No requiere habilitación para prestar de forma aislada.",
    key_points: [
      "CCyC, arts. 1520 y siguientes: definen el contrato de mutuo y las obligaciones del deudor.",
      "Prestar de forma ocasional entre particulares es legal sin autorización.",
      "Puede instrumentarse por escrito (recomendado) con firma de las partes.",
      "El deudor responde con todo su patrimonio; la garantía (prenda, fianza) se pacta aparte.",
    ],
    norms: [
      { code: "CCyC art. 1520", note: "Contrato de mutuo" },
      { code: "CCyC art. 1525", note: "Obligación de restituir" },
    ],
    links: [
      {
        label: "InfoLEG – Código Civil y Comercial",
        url: "https://servicios.infoleg.gob.ar/infolegInternet/anexos/235000-239999/235975/norma.htm",
      },
    ],
    applies_to:
      "Prestamista independiente y plataformas de enlace entre particulares.",
  },
  {
    id: "intereses-768",
    category: "prestamos",
    title: "Intereses y tasa máxima (art. 768 CCyC)",
    summary:
      "La tasa de interés se determina por acuerdo de partes, por leyes especiales o, en subsidio, por las reglamentaciones del BCRA. Una tasa usuraria puede ser reducida judicialmente.",
    key_points: [
      "CCyC art. 768: orden de prelación para fijar la tasa de interés (moratorio).",
      "El BCRA publica la Tasa de Intereses Moratorios (TIM) 'para uso de la justicia' (Resolución 2026-1-E del BCRA).",
      "Para préstamos personales y tarjetas el BCRA fija tasas de referencia y límites (p. ej. Comunicación 'B' 13111/2026).",
      "El Código Penal y la Ley 24.240 sancionan el abuso en la fijación de intereses.",
    ],
    norms: [
      { code: "CCyC art. 768", note: "Intereses moratorios y tasa aplicable" },
      { code: "Res. BCRA 2026-1-E", note: "Serie TIM" },
      { code: "Com. BCRA 'B' 13111/2026", note: "Límites a tasas" },
    ],
    links: [
      {
        label: "BCRA – Tasas de interés",
        url: "https://www.bcra.gob.ar/tasas-de-interes/",
      },
    ],
    applies_to:
      "Todos los préstamos onerosos, entre particulares o profesionales.",
  },
  {
    id: "ley-21526",
    category: "entidades",
    title: "Ley de Entidades Financieras (Ley 21.526)",
    summary:
      "Solo las entidades autorizadas por el BCRA pueden captar dinero del público y prestarlo de forma habitual. Intermediar entre el ahorro público y el crédito sin autorización es una infracción.",
    key_points: [
      "Ley 21.526: régimen de las entidades financieras; la autorización la otorga el BCRA.",
      "La 'intermediación habitual entre la oferta y la demanda de recursos financieros' está reservada a entidades autorizadas.",
      "Constituir una entidad exige capital mínimo, gobierno corporativo, plan de negocios y aprobación del BCRA.",
      "Operar sin autorización puede encuadrarse en el art. 309 del Código Penal (captación no autorizada).",
    ],
    norms: [
      { code: "Ley 21.526", note: "Entidades financieras" },
      { code: "Carta Orgánica BCRA (Ley 24.144)", note: "Facultades del BCRA" },
    ],
    links: [
      { label: "BCRA – Régimen de entidades", url: "https://www.bcra.gob.ar/" },
    ],
    applies_to:
      "Sociedades que quieran captar fondos y prestar de forma masiva y profesional.",
  },
  {
    id: "pnfc",
    category: "entidades",
    title: "Proveedores No Financieros de Crédito (PNFC)",
    summary:
      "Las fintech y sociedades que otorgan crédito sin ser bancos deben inscribirse ante el BCRA como Proveedores No Financieros de Crédito, con deberes de transparencia e información.",
    key_points: [
      "Los PNFC se registran en el BCRA y quedan sujetos a régimen informativo de tasas y costos.",
      "Deben exponer tasas (TNA/CFT), cargos y condiciones conforme a las normas de transparencia.",
      "Se les aplican las normas de protección al usuario de servicios financieros del BCRA.",
      "Este es el encuadre típico de una app de préstamos operada por un prestamista profesional.",
    ],
    norms: [
      { code: "Normas BCRA – PNFC", note: "Registro y régimen informativo" },
      { code: "Ley 21.526", note: "Marco general" },
    ],
    links: [
      {
        label: "BCRA – Proveedores no financieros de crédito",
        url: "https://www.bcra.gob.ar/",
      },
    ],
    applies_to:
      "La sociedad prestamista que use la app para dar créditos a escala.",
  },
  {
    id: "cnv-26831",
    category: "inversion",
    title: "Oferta pública de inversiones (Ley 26.831 – CNV)",
    summary:
      "Salvo excepciones, ofrecer al público instrumentos para que el dinero se invierta y financie créditos constituye oferta pública y requiere autorización de la Comisión Nacional de Valores.",
    key_points: [
      "Ley 26.831: régimen del mercado de capitales; la CNV autoriza la oferta pública.",
      "El 'crowdfunding' o financiamiento colectivo tiene su propio régimen y requisitos de plataforma.",
      "Financiar préstamos con dinero de terceros puede instrumentarse vía obligaciones negociables o fideicomiso.",
      "No se puede prometer rendimiento al público sin un vehículo autorizado.",
    ],
    norms: [
      { code: "Ley 26.831", note: "Mercado de Capitales" },
      { code: "Régimen de financiamiento colectivo", note: "Crowdfunding CNV" },
    ],
    links: [
      {
        label: "CNV – Comisión Nacional de Valores",
        url: "https://www.argentina.gob.ar/cnv",
      },
    ],
    applies_to: "La pata de 'inversión del público para financiar créditos'.",
  },
  {
    id: "fideicomiso",
    category: "inversion",
    title: "Fideicomiso financiero de créditos",
    summary:
      "Vía habitual para que inversores financien préstamos sin que la app capte dinero: un fiduciario autorizado administra un patrimonio separado que otorga crédito y reparte los rendimientos.",
    key_points: [
      "El patrimonio fideicomitido queda separado del patrimonio de la app y del prestamista.",
      "El fiduciario debe estar inscripto en la CNV; los títulos se ofrecen conforme a la Ley 26.831.",
      "Es el camino más usado para estructurar inversión respaldada por créditos.",
      "La app puede ser la interfaz tecnológica, sin captar fondos en nombre propio.",
    ],
    norms: [
      { code: "CCyC arts. 1666 y ss.", note: "Fideicomiso" },
      { code: "Ley 24.441", note: "Fideicomiso (histórica)" },
      { code: "Ley 26.831", note: "Oferta pública de títulos" },
    ],
    links: [
      {
        label: "CNV – Fiduciarios registrados",
        url: "https://www.argentina.gob.ar/cnv",
      },
    ],
    applies_to:
      "Modelo recomendado para conectar inversores con créditos de forma legal.",
  },
  {
    id: "codigo-penal-309",
    category: "general",
    title: "Captación no autorizada de dinero (art. 309 CP)",
    summary:
      "Recibir dinero del público con promesa de rendimiento sin autorización puede constituir delito. Es la principal advertencia para modelos que 'captan' fondos propios.",
    key_points: [
      "Código Penal, art. 309: sanciona la captación no autorizada de fondos del público.",
      "Aplica cuando la app 'recibe' el dinero y promete devolverlo con ganancia sin estar habilitada.",
      "Refuerza la necesidad de usar una entidad autorizada o un fiduciario para la pata de inversión.",
      "La difusión de estas normas es parte del deber de información al usuario.",
    ],
    norms: [{ code: "Código Penal art. 309", note: "Captación no autorizada" }],
    links: [
      {
        label: "InfoLEG – Código Penal",
        url: "https://servicios.infoleg.gob.ar/",
      },
    ],
    applies_to:
      "Cualquier modelo en que la plataforma reciba y administre dinero del público.",
  },
  {
    id: "usuario-financiero-bcra",
    category: "consumidor",
    title: "Protección al usuario de servicios financieros (BCRA)",
    summary:
      "El BCRA protege al usuario con deberes de trato digno, información clara de tasas y costos, y canales de reclamo. Aplica a los proveedores de crédito alcanzados.",
    key_points: [
      "Derecho a información veraz, clara y suficiente sobre tasas (TNA y CFT) y costos.",
      "Debe informarse el costo total del crédito antes de contratar.",
      "Existen canales de reclamo ante el BCRA y la autoridad de consumo.",
      "El trato digno y no abusivo es exigible.",
    ],
    norms: [
      { code: "Normas BCRA – Protección al usuario", note: "" },
      { code: "Ley 24.240", note: "Defensa del Consumidor" },
    ],
    links: [
      {
        label: "BCRA – Protección al usuario",
        url: "https://www.bcra.gob.ar/BCRAyVos/",
      },
    ],
    applies_to: "Toda relación con usuarios de crédito o inversión.",
  },
  {
    id: "ley-24240",
    category: "consumidor",
    title: "Ley de Defensa del Consumidor (Ley 24.240)",
    summary:
      "Rige las relaciones con consumidores: información obligatoria, publicidad veraz, cláusulas abusivas y derecho de arrepentimiento según el caso.",
    key_points: [
      "Deber de informar condiciones, precio, tasa y riesgo de forma destacada.",
      "Son nulas las cláusulas abusivas que desnaturalizan las obligaciones.",
      "La publicidad integra el contrato: lo prometido obliga.",
      "Evitar prometer rendimientos o beneficios sin respaldo regulatorio.",
    ],
    norms: [
      { code: "Ley 24.240", note: "Defensa del Consumidor" },
      { code: "CCyC art. 1092 y ss.", note: "Contratos de consumo" },
    ],
    links: [
      {
        label: "InfoLEG – Ley 24.240",
        url: "https://servicios.infoleg.gob.ar/infolegInternet/anexos/0-4999/638/texact.htm",
      },
    ],
    applies_to: "Comunicación y contratación con usuarios finales.",
  },
  {
    id: "uif-antilavado",
    category: "antilavado",
    title: "Prevención de lavado de activos (UIF)",
    summary:
      "Los sujetos obligados deben identificar clientes, reportar operaciones sospechosas y llevar registros. Alcanza a los proveedores de crédito y a los vehículos de inversión.",
    key_points: [
      "Ley 27.739 y normas de la UIF: régimen de prevención de lavado y financiamiento del terrorismo.",
      "Deberes de 'conocé a tu cliente' (KYC), registro y reporte de operaciones sospechosas.",
      "Los prestamistas profesionales y vehículos de inversión son sujetos obligados.",
      "La función KYC de la app se alinea con estas obligaciones.",
    ],
    norms: [
      { code: "Ley 27.739", note: "Prevención LA/FT" },
      { code: "Resoluciones UIF", note: "" },
    ],
    links: [
      {
        label: "UIF – Unidad de Información Financiera",
        url: "https://www.argentina.gob.ar/uif",
      },
    ],
    applies_to: "Prestamistas profesionales, fiduciarios y plataformas.",
  },
];

// ---------- acceso ----------

export function listRegulations({ category, q } = {}) {
  let items = REGULATIONS;
  if (category) items = items.filter((r) => r.category === category);
  if (q) {
    const needle = String(q)
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
    items = items.filter((r) => {
      const hay = `${r.title} ${r.summary} ${r.key_points.join(" ")} ${r.norms
        .map((n) => n.code)
        .join(" ")}`
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
      return hay.includes(needle);
    });
  }
  return items;
}

export function getRegulation(id) {
  return REGULATIONS.find((r) => r.id === id) ?? null;
}
