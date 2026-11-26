function abrirModalCobroUnificado() {
    const modal = document.getElementById('modalRegistrarPago');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        modal.style.setProperty('display', 'flex', 'important');
    }
    const buscador = document.getElementById('buscadorSocioCobro');
    if (buscador) buscador.focus();
}

function cerrarModalCobroUnificado() {
    const modal = document.getElementById('modalRegistrarPago');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        modal.style.setProperty('display', 'none', 'important');
    }
}

function filtrarSociosCobroUnificado() {
    const q = (document.getElementById('buscadorSocioCobro')?.value || '').toLowerCase().trim();
    document.querySelectorAll('.tarjeta-socio-cobro').forEach(card => {
        const texto = card.getAttribute('data-busqueda') || '';
        card.style.display = texto.includes(q) ? 'flex' : 'none';
    });
}

function seleccionarSocioCobroUnificado(el, socioId) {
    document.querySelectorAll('.tarjeta-socio-cobro').forEach(c => {
        c.classList.remove('border-emerald-500', 'bg-emerald-950/20');
        c.classList.add('border-slate-800');
    });
    el.classList.remove('border-slate-800');
    el.classList.add('border-emerald-500', 'bg-emerald-950/20');
    const inputSocio = document.getElementById('cobroUnificadoSocioId');
    if (inputSocio) inputSocio.value = socioId;
}

function validarSocioSeleccionadoUnificado() {
    const val = document.getElementById('cobroUnificadoSocioId')?.value;
    if (!val) {
        alert('Por favor seleccioná un socio de la lista antes de confirmar el cobro.');
        return false;
    }
    return true;
}

function actualizarSelectorPaseUnificado() {
    const cat = document.getElementById('selectCategoriaPaseUnificado')?.value;
    const bloquePilates = document.getElementById('bloqueFrecuenciaPilatesUnificado');
    if (bloquePilates) {
        bloquePilates.classList.toggle('hidden', cat !== 'grupo_pilates');
    }
    recalcularTotalCobroUnificado();
}

function recalcularTotalCobroUnificado() {
    const selCat = document.getElementById('selectCategoriaPaseUnificado');
    const selPilates = document.getElementById('selectSubPlanPilatesUnificado');
    const selAct = document.getElementById('selectActividadUnificado');
    const inputPlanReal = document.getElementById('cobroUnificadoPlanIdReal');

    const cajaInfo = document.getElementById('cajaInfoPaseUnificado');
    const tituloInfo = document.getElementById('tituloInfoPaseUnificado');
    const descInfo = document.getElementById('descInfoPaseUnificado');

    let precioPlan = 0;
    let nombrePlan = '';

    if (selCat && selCat.value === 'grupo_pilates' && selPilates && selPilates.options.length > 0) {
        const optP = selPilates.options[selPilates.selectedIndex];
        if (inputPlanReal) inputPlanReal.value = optP.value;
        precioPlan = parseInt(optP.getAttribute('data-precio') || 0);
        nombrePlan = optP.text.split('—')[0].trim();
    } else if (selCat && selCat.value) {
        const optC = selCat.options[selCat.selectedIndex];
        if (inputPlanReal) inputPlanReal.value = optC.value;
        precioPlan = parseInt(optC.getAttribute('data-precio') || 0);
        nombrePlan = optC.text.split('—')[0].trim();
    } else if (inputPlanReal) {
        inputPlanReal.value = '';
    }

    if (cajaInfo && tituloInfo && descInfo) {
        if (nombrePlan) {
            cajaInfo.classList.remove('hidden');
            tituloInfo.textContent = nombrePlan;
            const nomLow = nombrePlan.toLowerCase();
            if (nomLow.includes('pilates')) {
                descInfo.textContent = 'Clases de Pilates Reformer con reserva previa (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs).';
            } else if (nomLow.includes('clase')) {
                descInfo.textContent = 'Incluye Funcional (L/M/V 18hs), Spinning (L/M/V 19hs), Abdominales (L/M/V 20hs), Funcional+Cardio (M/J 18hs) y Zumba (L/M/J 19hs).';
            } else if (nomLow.includes('familiar')) {
                descInfo.textContent = 'Promoción válida a partir de 3 integrantes del grupo familiar abonando el mismo día ($50.000 c/u).';
            } else if (nomLow.includes('musculacion') || nomLow.includes('musculación')) {
                descInfo.textContent = 'Acceso libre a sala de Musculación + todas las Clases grupales incluidas durante 30 días.';
            } else {
                descInfo.textContent = 'Pase mensual habilitado por 30 días corridos desde la fecha de cobro.';
            }
        } else {
            cajaInfo.classList.add('hidden');
        }
    }

    const optA = selAct && selAct.selectedIndex >= 0 ? selAct.options[selAct.selectedIndex] : null;
    const precioAct = optA ? parseInt(optA.getAttribute('data-precio') || 0) : 0;
    const labelTotal = document.getElementById('labelTotalCobroUnificado');
    if (labelTotal) {
        labelTotal.textContent = '$' + (precioPlan + precioAct).toLocaleString('es-AR');
    }
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        cerrarModalCobroUnificado();
    }
});