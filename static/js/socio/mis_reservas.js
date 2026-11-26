document.addEventListener('DOMContentLoaded', () => {
    const modalBaja = document.getElementById('modalCancelarInscripcion');
    const textoBaja = document.getElementById('textoConfirmarBaja');
    const btnConfirmarBaja = document.getElementById('btnConfirmarBaja');
    let formularioPendiente = null;

if (!modalBaja) return;

const cerrarModalBaja = () => {
    modalBaja.classList.add('hidden');
    modalBaja.classList.remove('flex');
    formularioPendiente = null;
};

  // Abrir modal al hacer clic en "Cancelar Inscripción"
document.querySelectorAll('.btn-cancelar-inscripcion').forEach((boton) => {
    boton.addEventListener('click', () => {
    formularioPendiente = boton.closest('form');
    const disciplina = boton.dataset.disciplina || 'esta actividad';
    textoBaja.textContent = `¿Deseás darte de baja de ${disciplina}?`;
    modalBaja.classList.remove('hidden');
    modalBaja.classList.add('flex');
    });
});

  // Confirmar y enviar el formulario
btnConfirmarBaja?.addEventListener('click', () => {
    if (formularioPendiente) {
        formularioPendiente.submit();
    }
});

  // Cerrar con los botones "Cancelar" o la "X"
modalBaja.querySelectorAll('[data-cerrar-modal-baja]').forEach((btn) => {
    btn.addEventListener('click', cerrarModalBaja);
});

  // Cerrar al hacer clic fuera de la tarjeta
modalBaja.addEventListener('click', (e) => {
    if (e.target === modalBaja) {
        cerrarModalBaja();
    }
});
});