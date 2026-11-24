function toggleDestinoRutinaEmp() {
    const dest = document.getElementById('selectDestinoRutinaEmp').value;
    document.getElementById('bloqueSelectBasicaEmp').classList.toggle('hidden', dest !== 'basica');
    document.getElementById('bloqueSelectSocioEmp').classList.toggle('hidden', dest !== 'socio');
    cambiarTabRutinasEmp(dest === 'basica' ? 'basicas' : 'socios');
}

function cambiarTabRutinasEmp(tab) {
    const basicas = document.getElementById('contenedorRutinasBasicasEmp');
    const socios = document.getElementById('contenedorRutinasSociosEmp');
    const btnB = document.getElementById('btnTabRutinasBasicasEmp');
    const btnS = document.getElementById('btnTabRutinasSociosEmp');

    if (!basicas || !socios || !btnB || !btnS) return;

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

function abrirModalEditarEjEmp(btn) {
    document.getElementById('empEditEjId').value = btn.getAttribute('data-id');
    document.getElementById('empEditEjNombre').value = btn.getAttribute('data-nombre');
    document.getElementById('empEditEjSeries').value = btn.getAttribute('data-series');
    document.getElementById('empEditEjReps').value = btn.getAttribute('data-reps');
    document.getElementById('empEditEjDescanso').value = btn.getAttribute('data-descanso');
    document.getElementById('modalEditarEjercicioEmp').classList.remove('hidden');
}