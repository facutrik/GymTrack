function abrirModalEditarDesdeBoton(btn) {
    const id = btn.getAttribute('data-id');
    const nombre = btn.getAttribute('data-nombre');
    const descripcion = btn.getAttribute('data-descripcion');
    const requiereReserva = btn.getAttribute('data-reserva') === 'true';

    document.getElementById('editActividadId').value = id;
    document.getElementById('editNombre').value = nombre;
    document.getElementById('editDescripcion').value = descripcion;
    document.getElementById('editChkReserva').checked = requiereReserva;
    document.getElementById('editCupo').value = btn.getAttribute('data-cupo');
    document.getElementById('modalEditarActividad').classList.remove('hidden');
}