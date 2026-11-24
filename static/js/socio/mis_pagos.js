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