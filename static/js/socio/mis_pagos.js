function abrirModalPagoSocio() {
    const modal = document.getElementById('modalPagoSocio');
    if (modal) modal.classList.remove('hidden');
}

function cerrarModalPagoSocio() {
    const modal = document.getElementById('modalPagoSocio');
    if (modal) modal.classList.add('hidden');
}

function recalcularTotalPago() {
    const checkboxes = document.querySelectorAll('.chk-pago:checked');
    let total = 0;
    checkboxes.forEach(chk => {
        total += parseInt(chk.getAttribute('data-precio') || 0, 10) || 0;
    });
    const label = document.getElementById('labelTotalPagoSocio');
    if (label) {
        label.innerText = '$' + total.toLocaleString('es-AR');
    }
}

// Pilates es una sola opción: la frecuencia elegida define qué se cobra y cuánto
function actualizarPilates() {
    const chk = document.getElementById('chkPilates');
    const select = document.getElementById('selectFrecuenciaPilates');
    if (!chk || !select) return;

    const opcion = select.options[select.selectedIndex];
    const precio = parseInt(opcion.dataset.precio, 10);
    chk.value = opcion.value;
    chk.dataset.precio = precio;

    document.getElementById('bloqueFrecuenciaPilates').classList.toggle('hidden', !chk.checked);
    document.getElementById('precioPilates').innerText =
        (chk.checked ? '$' : 'Desde $') + (chk.checked ? precio : parseInt(select.options[0].dataset.precio, 10)).toLocaleString('es-AR');
    recalcularTotalPago();
}

// El navegador puede recordar lo marcado al volver a la página
document.addEventListener('DOMContentLoaded', actualizarPilates);
