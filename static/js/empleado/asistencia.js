function openAsistenciaModal() {
    document.getElementById('asistenciaModal').classList.remove('hidden');
    const input = document.getElementById('modalDniInput');
    if (input) input.focus();
}

function closeAsistenciaModal() {
    document.getElementById('asistenciaModal').classList.add('hidden');
}

let modoHistorialAsist = 'hoy';

function abrirModalHistorialAsistencias() {
    closeAsistenciaModal();
    document.getElementById('modalHistorialAsistencias').classList.remove('hidden');
    filtrarHistorialAsist('hoy');
}

function cerrarModalHistorialAsistencias() {
    document.getElementById('modalHistorialAsistencias').classList.add('hidden');
}

function filtrarHistorialAsist(modo) {
    modoHistorialAsist = modo;
    const btnHoy = document.getElementById('btnTabAsistHoy');
    const btnMes = document.getElementById('btnTabAsistMes');
    const selectMes = document.getElementById('selectMesAsist');

    if (modo === 'hoy') {
        if (btnHoy) btnHoy.className = "px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl transition cursor-pointer";
        if (btnMes) btnMes.className = "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-xl transition cursor-pointer";
        if (selectMes) selectMes.classList.add('hidden');
    } else {
        if (btnMes) btnMes.className = "px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl transition cursor-pointer";
        if (btnHoy) btnHoy.className = "px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-xl transition cursor-pointer";
        if (selectMes) selectMes.classList.remove('hidden');
    }
    aplicarFiltroAsist();
}

function aplicarFiltroAsist() {
    const selectMes = document.getElementById('selectMesAsist');
    const inputBuscar = document.getElementById('inputBuscarAsist');
    const mesSel = selectMes ? selectMes.value : 'todos';
    const texto = (inputBuscar ? inputBuscar.value : '').toLowerCase().trim();
    const filas = document.querySelectorAll('.fila-asist');
    let visibles = 0;

    filas.forEach(fila => {
        const esHoy = fila.getAttribute('data-es-hoy') === '1';
        const mesFila = fila.getAttribute('data-mes');
        const info = fila.getAttribute('data-busqueda') || '';

        let cumpleTiempo = (modoHistorialAsist === 'hoy') ? esHoy : (mesSel === 'todos' || mesFila === mesSel);
        let cumpleTexto = !texto || info.includes(texto);

        if (cumpleTiempo && cumpleTexto) {
            fila.classList.remove('hidden');
            visibles++;
        } else {
            fila.classList.add('hidden');
        }
    });

    const contador = document.getElementById('contadorFiltroAsist');
    if (contador) contador.innerText = `Mostrando ${visibles} ingreso(s)`;
}

function volverAMarcarAsistencia() {
    cerrarModalHistorialAsistencias();
    openAsistenciaModal();
}