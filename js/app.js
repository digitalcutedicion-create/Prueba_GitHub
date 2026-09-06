import { cargarDatos } from "./cargarDatos.js";
import { renderTarjetas } from "./renderTarjetas.js";

function normalizarCarrera(carrera) {
  if (!carrera) return "";

  const texto = carrera
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();

  switch (texto) {
    case "artes y medios audiovisuales":
    case "medios audiovisuales":
      return "Medios Audiovisuales";

    case "realizador":
    case "realizador integral":
    case "realizador integral en artes y medios audiovisuales":
      return "Realizador";

    case "escenografia":
      return "Escenografía";

    case "foba escenografia":
    case "foba8 esceno":
      return "FoBa Escenografía";

    case "diseno grafico":
      return "Diseño Gráfico";

    case "fotografia":
      return "Fotografía";

    case "ilustracion":
      return "Ilustración";

    case "profesorado en artes visuales":
      return "Profesorado En Artes Visuales";

    default:
      return carrera.trim();
  }
}

let mesas = [];

function normalizarTexto(t) {
  return (t || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[.,;:()\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}
function actualizarContador(c) {
  const e = document.getElementById("contadorResultados");
  if (e)
    e.textContent = c === 1 ? "1 mesa encontrada" : `${c} mesas encontradas`;
}
function completarSelect(
  id,
  valores,
  txt,
  formatearOpcion = (valor) => valor,
  ordenar = true,
) {
  const s = document.getElementById(id);
  if (!s) return;
  s.innerHTML = "";
  const o = document.createElement("option");
  o.value = "";
  o.textContent = txt;
  s.appendChild(o);
  const valoresUnicos = [...new Set(valores.filter(Boolean))];

  if (ordenar) {
    valoresUnicos.sort((a, b) => a.localeCompare(b, "es"));
  }

  valoresUnicos.forEach((v) => {
    const x = document.createElement("option");
    x.value = v;
    x.textContent = formatearOpcion(v);
    s.appendChild(x);
  });
}
function cargarFechas() {
  completarSelect(
    "filtroFecha",
    mesas
      .map((m) => m.fecha || m.dia || "")
      .filter((f) => /^\d{4}-\d{2}-\d{2}$/.test(f)),
    "Todas las fechas",
    (fecha) => {
      const [anio, mes, dia] = fecha.split("-");
      return `${dia}-${mes}-${anio}`;
    },
  );
}
const cargarMaterias = () => {
  const mapaMaterias = new Map();

  mesas.forEach((m) => {
    if (!m.materia) return;

    const clave = normalizarTexto(m.materia);

    if (clave === "asignatura") return;

    if (!mapaMaterias.has(clave)) {
      mapaMaterias.set(clave, m.materia.trim());
    }
  });

  completarSelect(
    "filtroMateria",
    [...mapaMaterias.values()],
    "Todas las unidades curriculares",
  );
};

const cargarCarreras = () =>
  completarSelect(
    "filtroCarrera",
    mesas.map((m) => m.carrera),
    "Todas las carreras",
  );
const cargarAnios = () =>
  completarSelect(
    "filtroAnio",
    mesas.map((m) => m.anio),
    "Todos los años",
    (valor) => {
      if (String(valor) === "0") return "FoBa";
      return `${valor}°`;
    },
  );
function cargarTurnos() {
  const orden = ["Mañana", "Tarde", "Noche", "No informado"];

  const turnos = [...new Set(mesas.map((m) => m.turno).filter(Boolean))].sort(
    (a, b) => {
      const posicionA = orden.indexOf(a);
      const posicionB = orden.indexOf(b);

      if (posicionA === -1 && posicionB === -1) {
        return a.localeCompare(b, "es");
      }

      if (posicionA === -1) return -1;
      if (posicionB === -1) return 1;

      return posicionA - posicionB;
    },
  );

  completarSelect("filtroTurno", turnos, "Todos los turnos", undefined, false);
}

function ejecutarBusqueda() {
  const texto = normalizarTexto(document.getElementById("txtBuscar").value);
  const materia = document.getElementById("filtroMateria").value;
  const carrera = document.getElementById("filtroCarrera").value;
  const anio = document.getElementById("filtroAnio").value;
  const turno = document.getElementById("filtroTurno").value;
  const fecha = document.getElementById("filtroFecha").value;
  const inscriptos = document.getElementById("filtroInscriptos").value;

  const r = mesas.filter((m) => {
    const coincideTexto = normalizarTexto(Object.values(m).join(" ")).includes(
      texto,
    );
    const coincideMateria =
      !materia || normalizarTexto(m.materia) === normalizarTexto(materia);
    const coincideCarrera = !carrera || m.carrera === carrera;
    const coincideAnio = !anio || String(m.anio) === anio;
    const coincideTurno = !turno || !m.turno || m.turno === turno;
    const coincideFecha = !fecha || (m.fecha || m.dia || "") === fecha;

    const coincideInscriptos =
      !inscriptos ||
      (inscriptos === "con" && m.conInscriptos === true) ||
      (inscriptos === "sin" && m.conInscriptos === false);
    return (
      coincideTexto &&
      coincideMateria &&
      coincideCarrera &&
      coincideAnio &&
      coincideTurno &&
      coincideFecha &&
      coincideInscriptos
    );
  });

  const criterio = document.getElementById("filtroOrden").value;

  r.sort((a, b) => {
    switch (criterio) {
      case "hora":
        return (a.hora || "").localeCompare(b.hora || "");

      case "materia":
        return (a.materia || "").localeCompare(b.materia || "", "es");

      case "carrera":
        return (a.carrera || "").localeCompare(b.carrera || "", "es");

      case "presidente":
        return (a.presidente || "").localeCompare(b.presidente || "", "es");

      case "fecha":
      default:
        return (a.dia || a.fecha || "").localeCompare(b.dia || b.fecha || "");
    }
  });

  renderTarjetas(r);
  actualizarContador(r.length);
}

function limpiarFiltros() {
  document.getElementById("txtBuscar").value = "";

  document.getElementById("filtroMateria").value = "";

  document.getElementById("filtroCarrera").value = "";

  document.getElementById("filtroAnio").value = "";

  document.getElementById("filtroTurno").value = "";

  document.getElementById("filtroFecha").value = "";

  document.getElementById("filtroOrden").value = "fecha";

  document.getElementById("filtroInscriptos").value = "";

  ejecutarBusqueda();

  document.getElementById("txtBuscar").focus();
}

function configurarBusqueda() {
  [
    "txtBuscar",
    "filtroMateria",
    "filtroCarrera",
    "filtroAnio",
    "filtroTurno",
    "filtroFecha",
    "filtroInscriptos",
    "filtroOrden",
  ].forEach((id) => {
    const e = document.getElementById(id);
    if (e)
      e.addEventListener(
        id === "txtBuscar" ? "input" : "change",
        ejecutarBusqueda,
      );
  });

  document
    .getElementById("btnLimpiarFiltros")
    ?.addEventListener("click", limpiarFiltros);
}

async function iniciarPortal() {
  mesas = await cargarDatos();

  mesas = mesas.map((m) => ({
    ...m,
    carrera: normalizarCarrera(m.carrera),
    turno: m.turno && String(m.turno).trim() ? m.turno : "No informado",
  }));

  cargarMaterias();
  cargarCarreras();
  cargarAnios();
  cargarTurnos();
  cargarFechas();
  renderTarjetas(mesas);
  actualizarContador(mesas.length);
  configurarBusqueda();
}
iniciarPortal();
