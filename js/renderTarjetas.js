export function renderTarjetas(datos) {
  const contenedor = document.getElementById("contenedorTarjetas");

  contenedor.innerHTML = "";

  if (datos.length === 0) {
    contenedor.innerHTML = `
            <div class="sinResultados">
                No se encontraron mesas.
            </div>
        `;

    return;
  }

  datos.forEach((mesa) => {
    // ============================
    // Fecha
    // ============================

    let fechaMostrar = "Sin asignar";
    let diaSemana = "";

    if (mesa.dia) {
      const fecha = new Date(mesa.dia + "T00:00:00");

      const dias = [
        "Domingo",
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
      ];

      const meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
      ];

      diaSemana = dias[fecha.getDay()];

      fechaMostrar = `${String(fecha.getDate()).padStart(2, "0")} de ${meses[fecha.getMonth()]} de ${fecha.getFullYear()}`;
    }

    // ============================
    // Hora
    // ============================

    let horaMostrar = "Sin asignar";

    if (mesa.hora) {
      horaMostrar = mesa.hora.replace(".", ":");
    }

    // ============================
    // Vocales
    // ============================

    const vocales = [mesa.vocal1, mesa.vocal2]
      .filter((v) => v && v.trim() !== "")
      .join("<br>");

    // ============================
    // Tarjeta
    // ============================

    const tarjeta = document.createElement("article");

    tarjeta.className = "tarjeta";

    // =====================================
    // Color por carrera
    // =====================================

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
          return "Realizador";

        case "escenografia":
          return "Escenografía";

        case "foba escenografia":
        case "foba8 esceno":
          return "FoBa Escenografía";

        default:
          return carrera;
      }
    }

    const coloresCarrera = {
      "Diseño Gráfico": "#2F5DA7",

      Escenografía: "#20AFC0",

      "FoBa Escenografía": "#FFD400",

      Fotografía: "#EF7F1A",

      Ilustración: "#3EAD32",

      "Medios Audiovisuales": "#8E44AD",

      "Profesorado En Artes Visuales": "#D62828",

      Realizador: "#E6007E",
    };

    const carreraNormalizada = normalizarCarrera(mesa.carrera);

    const colorCarrera = coloresCarrera[carreraNormalizada] || "#999999";

    tarjeta.style.setProperty("--colorCarrera", colorCarrera);

    let textoCurso = "";

    if (mesa.carrera === "Escenografía" && String(mesa.anio) === "0") {
      textoCurso = `FoBa · Turno ${mesa.turno || ""}`;
    } else {
      textoCurso = `${mesa.anio || ""}° ${mesa.division || ""} · Turno ${mesa.turno || ""}`;
    }

    tarjeta.innerHTML = `

<div class="cabeceraTarjeta"></div>

<div class="contenidoTarjeta">

<h2 class="materia">
    ${mesa.materia}
</h2>

${
  mesa.conInscriptos
    ? `
<div class="badgeInscriptos">
    🟢 Con inscriptos
</div>
`
    : `
<div class="badgeSinInscriptos">
    ⚪ Sin inscriptos
</div>
`
}

<div class="carrera">
        ${carreraNormalizada}
    </div>

    <div class="curso">
    ${textoCurso}
</div>

    <hr class="separador">

<div class="datosMesa">

    <div class="itemDato">

        <span class="etiqueta">
            FECHA
        </span>

        <span class="valor">
            ${fechaMostrar}
        </span>

    </div>

    <div class="itemDato">

        <span class="etiqueta">
            DÍA
        </span>

        <span class="valor">
            ${diaSemana || "Sin asignar"}
        </span>

    </div>

    <div class="itemDato">

        <span class="etiqueta">
            HORA
        </span>

        <span class="valor">
            ${horaMostrar}
        </span>

    </div>

</div>

    <hr class="separador">

    <div class="tribunal">

        <div class="bloqueTribunal">

            <div class="tituloSeccion">
                👤 PRESIDENTE
            </div>

            <div class="nombreIntegrante">
                ${mesa.presidente || "Sin asignar"}
            </div>

        </div>

        <div class="bloqueTribunal">

            <div class="tituloSeccion">
                👥 VOCALES
            </div>

            <div class="nombreIntegrante">
                ${vocales || "Sin asignar"}
            </div>

        </div>

    </div>

</div>

`;
    contenedor.appendChild(tarjeta);
  });
}
