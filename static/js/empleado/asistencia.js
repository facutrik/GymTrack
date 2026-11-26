let timerAutoCierrePerfilSocio = null;
let intervaloCuentaRegresivaSocio = null;
let tiempoFinAutoCierreSocio = null;

function limpiarTimerAutoCierre() {
    if (timerAutoCierrePerfilSocio) {
        clearTimeout(timerAutoCierrePerfilSocio);
        timerAutoCierrePerfilSocio = null;
    }
    if (intervaloCuentaRegresivaSocio) {
        clearInterval(intervaloCuentaRegresivaSocio);
        intervaloCuentaRegresivaSocio = null;
    }
    tiempoFinAutoCierreSocio = null;
}

function cerrarModalPerfilSocio() {
    limpiarTimerAutoCierre();
    const modal = document.getElementById('modalPerfilSocioAsistencia');
    if (modal) {
        modal.style.setProperty('display', 'none', 'important');
        modal.classList.add('hidden');
        modal.remove();
    }
}

function iniciarAutoCierrePerfilSocio(segundos = 5) {
    limpiarTimerAutoCierre();

    const modal = document.getElementById('modalPerfilSocioAsistencia');
    const barra = document.getElementById('barraAutoCierreSocio');
    const contador = document.getElementById('contadorSegundosSocio');

    if (!modal) return;

    const duracionMs = (Number(segundos) || 5) * 1000;
    tiempoFinAutoCierreSocio = Date.now() + duracionMs;

    modal.style.setProperty('display', 'flex', 'important');
    modal.classList.remove('hidden');

    if (contador) {
        contador.textContent = Math.ceil(duracionMs / 1000);
    }

    if (barra) {
        barra.style.transition = 'none';
        barra.style.width = '100%';
        void barra.offsetWidth;
        barra.style.transition = `width ${duracionMs}ms linear`;
        barra.style.width = '0%';
    }

    intervaloCuentaRegresivaSocio = setInterval(function () {
        if (!tiempoFinAutoCierreSocio) return;
        const restantesSeg = Math.max(0, Math.ceil((tiempoFinAutoCierreSocio - Date.now()) / 1000));
        if (contador) {
            contador.textContent = restantesSeg;
        }
        if (restantesSeg <= 0 && intervaloCuentaRegresivaSocio) {
            clearInterval(intervaloCuentaRegresivaSocio);
            intervaloCuentaRegresivaSocio = null;
        }
    }, 250);

    timerAutoCierrePerfilSocio = setTimeout(function () {
        cerrarModalPerfilSocio();
    }, duracionMs);
}

function openAsistenciaModal() {
    const modal = document.getElementById('asistenciaModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('hidden');
    }
    const input = document.getElementById('modalDniInput');
    if (input) input.focus();
}

function closeAsistenciaModal() {
    const modal = document.getElementById('asistenciaModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('hidden');
    }
}

let modoHistorialAsist = 'mes';

function abrirModalHistorialAsistencias() {
    closeAsistenciaModal();
    cerrarModalPerfilSocio();
    const modalHist = document.getElementById('modalHistorialAsistencias');
    if (modalHist) {
        modalHist.style.display = 'flex';
        modalHist.classList.remove('hidden');
    }
    filtrarHistorialAsist('mes');
}

function cerrarModalHistorialAsistencias() {
    const modalHist = document.getElementById('modalHistorialAsistencias');
    if (modalHist) {
        modalHist.style.display = 'none';
        modalHist.classList.add('hidden');
    }
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
    if (contador) contador.textContent = `Mostrando ${visibles} ingreso(s)`;
}

function volverAMarcarAsistencia() {
    cerrarModalHistorialAsistencias();
    openAsistenciaModal();
}

document.addEventListener('click', function (e) {
    const btnCerrar = e.target.closest('[data-cerrar-perfil-socio]');
    if (btnCerrar) {
        e.preventDefault();
        e.stopPropagation();
        cerrarModalPerfilSocio();
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const modalPerfil = document.getElementById('modalPerfilSocioAsistencia');
    if (modalPerfil && !modalPerfil.classList.contains('hidden')) {
        iniciarAutoCierrePerfilSocio(5);
    }
});