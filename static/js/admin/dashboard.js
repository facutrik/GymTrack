document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (typeof cerrarModalCobroUnificado === 'function') {
            cerrarModalCobroUnificado();
        }
        const modalRutinas = document.getElementById('modalRutinasAdmin');
        if (modalRutinas) modalRutinas.classList.add('hidden');

        const modalEjercicio = document.getElementById('modalEditarEjercicioStaff');
        if (modalEjercicio) modalEjercicio.classList.add('hidden');
    }
});