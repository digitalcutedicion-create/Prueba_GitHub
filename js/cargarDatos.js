export async function cargarDatos() {

    try {

        const respuesta = await fetch("data/mesas.json");

        if (!respuesta.ok) {
            throw new Error("No se pudo leer mesas.json");
        }

        const datos = await respuesta.json();

        return datos;

    }
    catch (error) {

        console.error(error);

        return [];

    }

}