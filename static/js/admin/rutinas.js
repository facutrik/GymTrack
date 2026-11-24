function toggleDestinoRutinaAdmin() {
    const dest = document.getElementById('selectDestinoRutinaAdmin').value;
        document.getElementById('bloqueSelectBasicaAdmin').classList.toggle('hidden', dest !== 'basica');
        document.getElementById('bloqueSelectSocioAdmin').classList.toggle('hidden', dest !== 'socio');
}

function cambiarTabRutinasModal(tab) {
    const basicas = document.getElementById('contenedorRutinasBasicasModal');
    const socios = document.getElementById('contenedorRutinasSociosModal');
    const btnB = document.getElementById('btnTabRutinasBasicas');
    const btnS = document.getElementById('btnTabRutinasSocios');

    if (tab === 'basicas') {
        basicas.classList.remove('hidden');
        socios.classList.add('hidden');
        btnB.className = "px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl cursor-pointer";
        btnS.className = "px-4 py-2 bg-slate-800 text-slate-300 hover:text-white font-bold text-xs rounded-xl cursor-pointer";
    } else {
        socios.classList.remove('hidden');
        basicas.classList.add('hidden');
        btnS.className = "px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl cursor-pointer";
        btnB.className = "px-4 py-2 bg-slate-800 text-slate-300 hover:text-white font-bold text-xs rounded-xl cursor-pointer";
    }
}

function abrirModalEditarEjStaff(btn) {
    document.getElementById('staffEditEjId').value = btn.getAttribute('data-id');
    document.getElementById('staffEditEjNombre').value = btn.getAttribute('data-nombre');
    document.getElementById('staffEditEjSeries').value = btn.getAttribute('data-series');
    document.getElementById('staffEditEjReps').value = btn.getAttribute('data-reps');
    document.getElementById('staffEditEjDescanso').value = btn.getAttribute('data-descanso');
    document.getElementById('modalEditarEjercicioStaff').classList.remove('hidden');
}