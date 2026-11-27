// Padrón de socios (compartido por los módulos admin y empleado)

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
        buscarPalabras: ["musculaci"]
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

function mostrarModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function ocultarModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function mostrarModalAltaSocio() {
    mostrarModal('modalAltaSocio');
}

function actualizarOpcionesPaseAlta() {
    const categoria = document.getElementById('selectCategoriaPaseAlta').value;
    document.getElementById('bloqueDiasPilatesAlta').classList.toggle('hidden', categoria !== 'pilates');

    if (!categoria) {
        document.getElementById('tarjetaInfoPaseAlta').classList.add('hidden');
        document.getElementById('inputPlanIdAlta').value = '';
        return;
    }
    sincronizarPlanRealAlta();
}

// Busca en el catálogo de la BD el plan que corresponde a lo elegido y guarda su id
function sincronizarPlanRealAlta() {
    const categoria = document.getElementById('selectCategoriaPaseAlta').value;
    const clave = categoria === 'pilates'
        ? document.getElementById('selectDiasPilatesAlta').value
        : categoria;
    const info = INFO_PASES_ALTA[clave];
    if (!info) return;

    document.getElementById('tarjetaInfoPaseAlta').classList.remove('hidden');
    document.getElementById('tituloInfoPaseAlta').innerText = info.titulo;
    document.getElementById('detalleInfoPaseAlta').innerHTML = info.detalle;

    const plan = [...document.querySelectorAll('#catalogoPlanesAltaBD span')].find(span => {
        const nombreBD = (span.dataset.nombre || '').toLowerCase();
        return info.buscarPalabras.every(palabra => nombreBD.includes(palabra));
    });
    document.getElementById('inputPlanIdAlta').value = plan ? plan.dataset.id : '';
}

function abrirModalEditarSocio(btn) {
    document.getElementById('editSocioId').value = btn.dataset.id || '';
    document.getElementById('editNombre').value = btn.dataset.nombre || '';
    document.getElementById('editApellido').value = btn.dataset.apellido || '';
    document.getElementById('editEmail').value = btn.dataset.email || '';
    document.getElementById('editTelefono').value = btn.dataset.telefono || '';
    mostrarModal('modalEditarSocio');
}

// El perfil se abre con ?perfil=<id>; al cerrarlo se saca ese parámetro de la URL
function cerrarPerfilSocio() {
    const modal = document.getElementById('modalPerfilSocio');
    if (!modal) return;
    ocultarModal('modalPerfilSocio');
    history.replaceState(null, '', modal.dataset.urlCerrar);
}

// Cerrar los modales con un clic afuera de la tarjeta
['modalAltaSocio', 'modalEditarSocio'].forEach(id => {
    document.getElementById(id)?.addEventListener('click', e => {
        if (e.target.id === id) ocultarModal(id);
    });
});
document.getElementById('modalPerfilSocio')?.addEventListener('click', e => {
    if (e.target.id === 'modalPerfilSocio') cerrarPerfilSocio();
});
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarPerfilSocio();
});

// Los paneles enlazan a ?nuevo=1 para abrir directamente el alta
if (new URLSearchParams(window.location.search).get('nuevo') === '1') {
    mostrarModalAltaSocio();
}
