// Modal único de cobro a socio (templates/includes/modal_cobro.html)

function abrirModalCobroUnificado() {
    const modal = document.getElementById('modalRegistrarPago');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.getElementById('buscadorSocioCobro')?.focus();
}

function cerrarModalCobroUnificado() {
    const modal = document.getElementById('modalRegistrarPago');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function filtrarSociosCobroUnificado() {
    const q = (document.getElementById('buscadorSocioCobro')?.value || '').toLowerCase().trim();
    document.querySelectorAll('.tarjeta-socio-cobro').forEach(card => {
        card.style.display = (card.dataset.busqueda || '').includes(q) ? 'flex' : 'none';
    });
}

function seleccionarSocioCobroUnificado(el, socioId) {
    document.querySelectorAll('.tarjeta-socio-cobro').forEach(c => {
        c.classList.remove('border-emerald-500', 'bg-emerald-500/10');
        c.classList.add('border-slate-800');
    });
    el.classList.remove('border-slate-800');
    el.classList.add('border-emerald-500', 'bg-emerald-500/10');
    document.getElementById('cobroUnificadoSocioId').value = socioId;
}

function validarSocioSeleccionadoUnificado() {
    if (!document.getElementById('cobroUnificadoSocioId')?.value) {
        gymAviso('Seleccioná un socio de la lista antes de confirmar el cobro.', 'Falta elegir el socio');
        return false;
    }
    return true;
}

function actualizarSelectorPaseUnificado() {
    const cat = document.getElementById('selectCategoriaPaseUnificado')?.value;
    document.getElementById('bloqueFrecuenciaPilatesUnificado')?.classList.toggle('hidden', cat !== 'grupo_pilates');
    recalcularTotalCobroUnificado();
}

function descripcionDelPlan(nombre) {
    const n = nombre.toLowerCase();
    if (n.includes('pilates')) return 'Clases de Pilates Reformer con reserva previa (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs).';
    if (n.includes('clase')) return 'Incluye Funcional (L/M/V 18hs), Spinning (L/M/V 19hs), Abdominales (L/M/V 20hs), Funcional+Cardio (M/J 18hs) y Zumba (L/M/J 19hs).';
    if (n.includes('familiar')) return 'Promoción válida a partir de 3 integrantes del grupo familiar abonando el mismo día ($50.000 c/u).';
    if (n.includes('musculaci')) return 'Acceso libre a sala de Musculación + todas las Clases grupales incluidas durante 30 días.';
    return 'Pase mensual habilitado por 30 días corridos desde la fecha de cobro.';
}

function recalcularTotalCobroUnificado() {
    const selCat = document.getElementById('selectCategoriaPaseUnificado');
    const selPilates = document.getElementById('selectSubPlanPilatesUnificado');
    const selAct = document.getElementById('selectActividadUnificado');
    const inputPlanReal = document.getElementById('cobroUnificadoPlanIdReal');

    let opcionPlan = null;
    if (selCat?.value === 'grupo_pilates' && selPilates?.options.length) {
        opcionPlan = selPilates.options[selPilates.selectedIndex];
    } else if (selCat?.value) {
        opcionPlan = selCat.options[selCat.selectedIndex];
    }
    inputPlanReal.value = opcionPlan ? opcionPlan.value : '';

    const precioPlan = opcionPlan ? parseInt(opcionPlan.dataset.precio || 0) : 0;
    const nombrePlan = opcionPlan ? opcionPlan.text.split('—')[0].trim() : '';

    const cajaInfo = document.getElementById('cajaInfoPaseUnificado');
    cajaInfo.classList.toggle('hidden', !nombrePlan);
    if (nombrePlan) {
        document.getElementById('tituloInfoPaseUnificado').textContent = nombrePlan;
        document.getElementById('descInfoPaseUnificado').textContent = descripcionDelPlan(nombrePlan);
    }

    const opcionAct = selAct && selAct.selectedIndex >= 0 ? selAct.options[selAct.selectedIndex] : null;
    const precioAct = opcionAct ? parseInt(opcionAct.dataset.precio || 0) : 0;
    document.getElementById('labelTotalCobroUnificado').textContent = '$' + (precioPlan + precioAct).toLocaleString('es-AR');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarModalCobroUnificado();
});

document.getElementById('modalRegistrarPago')?.addEventListener('click', e => {
    if (e.target.id === 'modalRegistrarPago') cerrarModalCobroUnificado();
});
