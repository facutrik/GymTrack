function cerrarMenuPerfil() {
    const modal = document.getElementById('modalMiniPerfil');
    if (modal) modal.classList.add('hidden');
}

function irACobrarDesdePerfil(dni) {
    cerrarMenuPerfil();
    if (typeof abrirModalCobroUnificado === 'function') {
        abrirModalCobroUnificado();
    }
    const buscador = document.getElementById('buscadorSocioCobro');
    if (buscador) {
        buscador.value = dni;
        if (typeof filtrarSociosCobroUnificado === 'function') {
            filtrarSociosCobroUnificado();
        }
    }
    const tarjeta = document.querySelector(`.tarjeta-socio-cobro[data-dni="${dni}"]`);
    if (tarjeta) tarjeta.click();
}

function abrirModalIniciarTurno(id, nombre, dni) {
    document.getElementById('modalProfeId').value = id;
    document.getElementById('modalProfeNombre').innerText = nombre;
    document.getElementById('modalProfeDni').value = dni;
    document.getElementById('modalIniciarTurno').classList.remove('hidden');
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        cerrarMenuPerfil();
        if (typeof cerrarModalPerfilSocio === 'function') cerrarModalPerfilSocio();
        if (typeof cerrarModalCobroUnificado === 'function') cerrarModalCobroUnificado();
        if (typeof closeAsistenciaModal === 'function') closeAsistenciaModal();
        if (typeof cerrarModalHistorialAsistencias === 'function') cerrarModalHistorialAsistencias();

        ['modalRutinaProfesor', 'modalEditarEjercicioEmp', 'modalIniciarTurno', 'modalDisciplinas'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('hidden');
        });
    }
});