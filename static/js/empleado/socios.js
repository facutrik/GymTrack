const INFO_PASES_ALTA = {
    clases: {
        titulo: "Pase Clases",
        detalle: `
            <p class="mb-1 text-slate-300">Incluye acceso a todas las clases grupales:</p>
            <ul class="list-disc list-inside space-y-0.5 text-slate-400">
                <li><strong class="text-slate-200">Lun, Mié y Vie:</strong> 18hs Funcional • 19hs Spinning • 20hs Abdominales</li>
                <li><strong class="text-slate-200">Mar y Jue:</strong> 18hs Funcional + Cardio</li>
                <li><strong class="text-slate-200">Lun, Mar y Jue:</strong> 19hs Zumba</li>
            </ul>
        `,
        buscarPalabras: ["clase"]
    },
    musculacion: {
        titulo: "Pase Musculación",
        detalle: `<p>Acceso libre a sala de <strong class="text-white">Musculación + todas las Clases grupales</strong> incluidas durante 30 días.</p>`,
        buscarPalabras: ["musculacion", "musculación", "completo"]
    },
    familiar: {
        titulo: "Plan Familiar",
        detalle: `<p>Válido a partir de <strong class="text-white">3 personas del grupo familiar</strong> abonando el mismo día.</p>`,
        buscarPalabras: ["familiar"]
    },
    pilates_1: {
        titulo: "Pilates — 1 vez por semana",
        detalle: `<p>1 clase semanal de Pilates con reserva de turno (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs).</p>`,
        buscarPalabras: ["pilates", "1"]
    },
    pilates_2: {
        titulo: "Pilates — 2 veces por semana",
        detalle: `<p>2 clases semanales de Pilates con reserva de turno (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs).</p>`,
        buscarPalabras: ["pilates", "2"]
    },
    pilates_3: {
        titulo: "Pilates — 3 veces por semana",
        detalle: `<p>3 clases semanales de Pilates con reserva de turno (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs).</p>`,
        buscarPalabras: ["pilates", "3"]
    }
};

function mostrarModalAltaSocio() {
    const modalAlta = document.getElementById('modalAltaSocio');
    if (!modalAlta) return false;
    modalAlta.classList.remove('hidden');
    modalAlta.classList.add('flex');
    modalAlta.style.setProperty('display', 'flex', 'important');
    return true;
}

function ocultarModalAltaSocio() {
    const modalAlta = document.getElementById('modalAltaSocio');
    if (!modalAlta) return;
    modalAlta.classList.add('hidden');
    modalAlta.classList.remove('flex');
    modalAlta.style.setProperty('display', 'none', 'important');
}

function actualizarOpcionesPaseAlta() {
    const categoria = document.getElementById('selectCategoriaPaseAlta').value;
    const bloquePilates = document.getElementById('bloqueDiasPilatesAlta');
    const tarjetaInfo = document.getElementById('tarjetaInfoPaseAlta');

    if (!categoria) {
        bloquePilates.classList.add('hidden');
        tarjetaInfo.classList.add('hidden');
        document.getElementById('inputPlanIdAltaEmpleado').value = '';
        return;
    }

    if (categoria === 'pilates') {
        bloquePilates.classList.remove('hidden');
    } else {
        bloquePilates.classList.add('hidden');
    }

    sincronizarPlanRealAlta();
}

function sincronizarPlanRealAlta() {
    const categoria = document.getElementById('selectCategoriaPaseAlta').value;
    const clave = (categoria === 'pilates')
        ? document.getElementById('selectDiasPilatesAlta').value
        : categoria;

    const info = INFO_PASES_ALTA[clave];
    if (!info) return;

    document.getElementById('tarjetaInfoPaseAlta').classList.remove('hidden');
    document.getElementById('tituloInfoPaseAlta').innerText = info.titulo;
    document.getElementById('detalleInfoPaseAlta').innerHTML = info.detalle;

    const spansPlanes = document.querySelectorAll('#catalogoPlanesAltaBD span');
    let idEncontrado = '';

    spansPlanes.forEach(span => {
        const nombreBD = (span.getAttribute('data-nombre') || '').toLowerCase();
        const coincideTodo = info.buscarPalabras.every(palabra => nombreBD.includes(palabra));
        if (coincideTodo && !idEncontrado) {
            idEncontrado = span.getAttribute('data-id');
        }
    });

    document.getElementById('inputPlanIdAltaEmpleado').value = idEncontrado;
}

function abrirModalEditarDesdeBoton(btn) {
    document.getElementById('editSocioId').value = btn.getAttribute('data-id') || '';
    document.getElementById('editNombre').value = btn.getAttribute('data-nombre') || '';
    document.getElementById('editApellido').value = btn.getAttribute('data-apellido') || '';
    document.getElementById('editEmail').value = btn.getAttribute('data-email') || '';
    document.getElementById('editTelefono').value = btn.getAttribute('data-telefono') || '';
    const modalEdit = document.getElementById('modalEditarSocio');
    if (modalEdit) {
        modalEdit.classList.remove('hidden');
        modalEdit.classList.add('flex');
        modalEdit.style.setProperty('display', 'flex', 'important');
    }
}

function verificarParametroNuevoSocio() {
    if (new URLSearchParams(window.location.search).get('nuevo') !== '1') return;
    if (mostrarModalAltaSocio()) return;

    let intentos = 0;
    const reintento = setInterval(() => {
        intentos += 1;
        if (mostrarModalAltaSocio() || intentos >= 20) {
            clearInterval(reintento);
        }
    }, 50);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', verificarParametroNuevoSocio);
} else {
    verificarParametroNuevoSocio();
}
window.addEventListener('load', verificarParametroNuevoSocio);

(function abrirSiVieneNuevoEnUrl() {
    if (new URLSearchParams(window.location.search).get('nuevo') !== '1') return;

    function abrirModal() {
        const modal = document.getElementById('modalAltaSocio');
        if (!modal) return false;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        modal.style.setProperty('display', 'flex', 'important');
        return true;
    }

    if (!abrirModal()) {
        document.addEventListener('DOMContentLoaded', abrirModal);
        window.addEventListener('load', abrirModal);
    }
})();