// Mis pagos (socio): modal para pagar la cuota

function abrirModalPagoSocio() {
    document.getElementById('modalPagoSocio')?.classList.remove('hidden');
    recalcularTotalPago();
}

function cerrarModalPagoSocio() {
    document.getElementById('modalPagoSocio')?.classList.add('hidden');
}

function recalcularTotalPago() {
    const elegidos = [...document.querySelectorAll('.opcion-pago:checked')].filter(o => o.value);
    const total = elegidos.reduce((suma, o) => suma + (parseInt(o.dataset.precio, 10) || 0), 0);
    document.getElementById('labelTotalPagoSocio').textContent = '$' + total.toLocaleString('es-AR');
    const nombres = elegidos.map(o => o.closest('label').querySelector('.font-bold')?.textContent.trim())
        .map((n, i) => elegidos[i].name === 'pilates' ? `Pilates ${n}` : n);
    document.getElementById('detalleTotalPagoSocio').textContent = nombres.length ? nombres.join(' + ') : 'Elegí qué vas a pagar';
}

function actualizarMetodoPago() {
    const transferencia = document.querySelector('.opcion-metodo:checked')?.value === 'transferencia';
    document.getElementById('bloqueTransferencia').classList.toggle('hidden', !transferencia);
    document.getElementById('bloqueRecepcion').classList.toggle('hidden', transferencia);
    document.getElementById('btnEnviarPagoSocio').textContent = transferencia ? 'Enviar pago' : 'Reservar pago en recepción';
}

function copiarDato(boton, texto) {
    navigator.clipboard?.writeText(texto).then(() => {
        const icono = boton.querySelector('i');
        icono.className = 'fa-solid fa-check text-emerald-400 ml-1';
        setTimeout(() => { icono.className = 'fa-regular fa-copy text-slate-500 ml-1'; }, 1500);
    });
}

const MAX_MB = 5;
document.getElementById('inputComprobante')?.addEventListener('change', function () {
    const archivo = this.files[0];
    const texto = document.getElementById('textoComprobante');
    const icono = document.getElementById('iconoComprobante');
    const zona = document.getElementById('zonaComprobante');
    if (!archivo) {
        texto.textContent = 'Subí la captura o el PDF';
        icono.className = 'fa-solid fa-cloud-arrow-up';
        zona.classList.remove('border-emerald-500/60');
        return;
    }
    if (archivo.size > MAX_MB * 1024 * 1024) {
        this.value = '';
        gymAviso(`El comprobante no puede pesar más de ${MAX_MB} MB.`, 'Archivo muy grande');
        return;
    }
    texto.textContent = archivo.name;
    icono.className = archivo.type === 'application/pdf' ? 'fa-solid fa-file-pdf' : 'fa-solid fa-file-image';
    zona.classList.add('border-emerald-500/60');
});

document.getElementById('formPagoSocio')?.addEventListener('submit', e => {
    const hayPlan = [...document.querySelectorAll('.opcion-pago:checked')].some(o => o.value);
    const transferencia = document.querySelector('.opcion-metodo:checked')?.value === 'transferencia';
    if (!hayPlan) {
        e.preventDefault();
        gymAviso('Elegí un pase mensual o una frecuencia de Pilates.', 'Falta elegir el plan');
    } else if (transferencia && !document.getElementById('inputComprobante').files.length) {
        e.preventDefault();
        gymAviso('Adjuntá el comprobante de la transferencia para que recepción pueda verificar el pago.', 'Falta el comprobante');
    }
});

document.querySelectorAll('.opcion-pago').forEach(o => o.addEventListener('change', recalcularTotalPago));
document.querySelectorAll('.opcion-metodo').forEach(o => o.addEventListener('change', actualizarMetodoPago));
document.getElementById('modalPagoSocio')?.addEventListener('click', e => {
    if (e.target.id === 'modalPagoSocio') cerrarModalPagoSocio();
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModalPagoSocio(); });
actualizarMetodoPago();
recalcularTotalPago();

// Barra de avance del período de cada membresía (el porcentaje viene en data-porcentaje)
document.querySelectorAll('.barra-periodo').forEach(barra => {
    barra.style.width = (parseFloat(barra.dataset.porcentaje) || 0) + '%';
});
