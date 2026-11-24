const CATALOGO_HEVY = [
    // PECHO
    { nombre: "Press de banca plano con barra", grupo: "pecho", equipo: "Barra", s: 4, r: "8-10", kg: 60 },
    { nombre: "Press de banca inclinado con barra", grupo: "pecho", equipo: "Barra", s: 4, r: "8-10", kg: 50 },
    { nombre: "Press de banca declinado con barra", grupo: "pecho", equipo: "Barra", s: 3, r: "10", kg: 50 },
    { nombre: "Press plano con mancuernas", grupo: "pecho", equipo: "Mancuernas", s: 4, r: "10", kg: 22 },
    { nombre: "Press inclinado con mancuernas", grupo: "pecho", equipo: "Mancuernas", s: 4, r: "10-12", kg: 20 },
    { nombre: "Press declinado con mancuernas", grupo: "pecho", equipo: "Mancuernas", s: 3, r: "10-12", kg: 18 },
    { nombre: "Press de pecho en máquina convergente", grupo: "pecho", equipo: "Máquina", s: 3, r: "12", kg: 40 },
    { nombre: "Press inclinado en máquina Smith", grupo: "pecho", equipo: "Smith", s: 3, r: "10", kg: 40 },
    { nombre: "Aperturas planas con mancuernas", grupo: "pecho", equipo: "Mancuernas", s: 3, r: "12-15", kg: 12 },
    { nombre: "Aperturas inclinadas con mancuernas", grupo: "pecho", equipo: "Mancuernas", s: 3, r: "12-15", kg: 12 },
    { nombre: "Peck Deck / Contractora de pecho", grupo: "pecho", equipo: "Máquina", s: 3, r: "12-15", kg: 35 },
    { nombre: "Cruces en polea alta", grupo: "pecho", equipo: "Polea", s: 3, r: "12-15", kg: 15 },
    { nombre: "Cruces en polea baja", grupo: "pecho", equipo: "Polea", s: 3, r: "12-15", kg: 10 },
    { nombre: "Fondos en paralelas para pecho", grupo: "pecho", equipo: "Peso corporal", s: 3, r: "10", kg: 0 },
    { nombre: "Flexiones de brazos (Push-ups)", grupo: "pecho", equipo: "Peso corporal", s: 3, r: "15", kg: 0 },
    { nombre: "Pullover con mancuerna en banco", grupo: "pecho", equipo: "Mancuernas", s: 3, r: "12", kg: 18 },

    // ESPALDA
    { nombre: "Dominadas pronas (Pull-ups)", grupo: "espalda", equipo: "Peso corporal", s: 4, r: "8-10", kg: 0 },
    { nombre: "Dominadas supinas (Chin-ups)", grupo: "espalda", equipo: "Peso corporal", s: 4, r: "8-10", kg: 0 },
    { nombre: "Dominadas asistidas en máquina", grupo: "espalda", equipo: "Máquina", s: 3, r: "10-12", kg: 25 },
    { nombre: "Dorsalera / Jalón al pecho agarre amplio", grupo: "espalda", equipo: "Polea", s: 4, r: "10-12", kg: 45 },
    { nombre: "Dorsalera agarre neutro (triángulo)", grupo: "espalda", equipo: "Polea", s: 3, r: "10-12", kg: 45 },
    { nombre: "Jalón al pecho supino", grupo: "espalda", equipo: "Polea", s: 3, r: "10-12", kg: 40 },
    { nombre: "Remo con barra (Bent-over row)", grupo: "espalda", equipo: "Barra", s: 4, r: "8-10", kg: 50 },
    { nombre: "Remo Pendlay con barra", grupo: "espalda", equipo: "Barra", s: 4, r: "6-8", kg: 55 },
    { nombre: "Remo T con apoyo al pecho", grupo: "espalda", equipo: "Máquina", s: 4, r: "8-12", kg: 40 },
    { nombre: "Remo unilateral con mancuerna", grupo: "espalda", equipo: "Mancuernas", s: 3, r: "10-12", kg: 22 },
    { nombre: "Remo sentado en polea baja (gironda)", grupo: "espalda", equipo: "Polea", s: 3, r: "10-12", kg: 45 },
    { nombre: "Remo en máquina Hammer", grupo: "espalda", equipo: "Máquina", s: 3, r: "10-12", kg: 40 },
    { nombre: "Pullover en polea alta con soga", grupo: "espalda", equipo: "Polea", s: 3, r: "12-15", kg: 20 },
    { nombre: "Hiperextensiones lumbares en banco", grupo: "espalda", equipo: "Peso corporal", s: 3, r: "15", kg: 10 },
    { nombre: "Encogimientos de trapecio con barra", grupo: "espalda", equipo: "Barra", s: 3, r: "12", kg: 60 },
    { nombre: "Encogimientos de trapecio con mancuernas", grupo: "espalda", equipo: "Mancuernas", s: 3, r: "12-15", kg: 24 },

    // PIERNAS
    { nombre: "Sentadilla libre trasera con barra", grupo: "piernas", equipo: "Barra", s: 4, r: "8-10", kg: 80 },
    { nombre: "Sentadilla frontal con barra", grupo: "piernas", equipo: "Barra", s: 4, r: "8", kg: 60 },
    { nombre: "Sentadilla en máquina Smith", grupo: "piernas", equipo: "Smith", s: 3, r: "10", kg: 60 },
    { nombre: "Sentadilla Goblet con mancuerna", grupo: "piernas", equipo: "Mancuernas", s: 3, r: "12", kg: 20 },
    { nombre: "Sentadilla Hack en máquina", grupo: "piernas", equipo: "Máquina", s: 4, r: "10", kg: 70 },
    { nombre: "Sentadilla búlgara con mancuernas", grupo: "piernas", equipo: "Mancuernas", s: 3, r: "10", kg: 14 },
    { nombre: "Prensa inclinada 45°", grupo: "piernas", equipo: "Máquina", s: 4, r: "10-12", kg: 120 },
    { nombre: "Prensa horizontal", grupo: "piernas", equipo: "Máquina", s: 3, r: "12", kg: 80 },
    { nombre: "Peso muerto convencional con barra", grupo: "piernas", equipo: "Barra", s: 4, r: "5-8", kg: 90 },
    { nombre: "Peso muerto rumano con barra", grupo: "piernas", equipo: "Barra", s: 4, r: "8-10", kg: 70 },
    { nombre: "Peso muerto rumano con mancuernas", grupo: "piernas", equipo: "Mancuernas", s: 3, r: "10-12", kg: 22 },
    { nombre: "Peso muerto sumo con barra", grupo: "piernas", equipo: "Barra", s: 4, r: "6-8", kg: 85 },
    { nombre: "Hip Thrust con barra", grupo: "piernas", equipo: "Barra", s: 4, r: "10-12", kg: 80 },
    { nombre: "Hip Thrust en máquina", grupo: "piernas", equipo: "Máquina", s: 3, r: "12", kg: 60 },
    { nombre: "Sillón de cuádriceps (Extensión)", grupo: "piernas", equipo: "Máquina", s: 3, r: "12-15", kg: 40 },
    { nombre: "Camilla femoral acostado", grupo: "piernas", equipo: "Máquina", s: 3, r: "10-12", kg: 35 },
    { nombre: "Curl femoral sentado en máquina", grupo: "piernas", equipo: "Máquina", s: 3, r: "12", kg: 35 },
    { nombre: "Aductores en máquina", grupo: "piernas", equipo: "Máquina", s: 3, r: "12-15", kg: 40 },
    { nombre: "Abductores en máquina", grupo: "piernas", equipo: "Máquina", s: 3, r: "15", kg: 40 },
    { nombre: "Zancadas / Estocadas caminando", grupo: "piernas", equipo: "Mancuernas", s: 3, r: "12", kg: 14 },
    { nombre: "Subidas al cajón (Step-ups)", grupo: "piernas", equipo: "Mancuernas", s: 3, r: "12", kg: 12 },
    { nombre: "Patada de glúteo en polea baja", grupo: "piernas", equipo: "Polea", s: 3, r: "15", kg: 15 },
    { nombre: "Gemelos parado en máquina", grupo: "piernas", equipo: "Máquina", s: 4, r: "12-15", kg: 50 },
    { nombre: "Gemelos sentado (Sóleo)", grupo: "piernas", equipo: "Máquina", s: 3, r: "15", kg: 35 },

    // HOMBROS
    { nombre: "Press militar de pie con barra", grupo: "hombros", equipo: "Barra", s: 4, r: "8-10", kg: 35 },
    { nombre: "Press militar sentado con mancuernas", grupo: "hombros", equipo: "Mancuernas", s: 4, r: "10", kg: 16 },
    { nombre: "Press Arnold con mancuernas", grupo: "hombros", equipo: "Mancuernas", s: 3, r: "10-12", kg: 14 },
    { nombre: "Press de hombros en máquina", grupo: "hombros", equipo: "Máquina", s: 3, r: "10-12", kg: 30 },
    { nombre: "Vuelos laterales con mancuernas", grupo: "hombros", equipo: "Mancuernas", s: 4, r: "12-15", kg: 10 },
    { nombre: "Vuelos laterales en polea baja", grupo: "hombros", equipo: "Polea", s: 3, r: "12-15", kg: 8 },
    { nombre: "Vuelos laterales en máquina", grupo: "hombros", equipo: "Máquina", s: 3, r: "12-15", kg: 20 },
    { nombre: "Vuelos frontales con mancuernas o disco", grupo: "hombros", equipo: "Mancuernas", s: 3, r: "12", kg: 10 },
    { nombre: "Pájaros / Vuelos posteriores con mancuernas", grupo: "hombros", equipo: "Mancuernas", s: 3, r: "12-15", kg: 8 },
    { nombre: "Peck Deck inverso (Deltoides posterior)", grupo: "hombros", equipo: "Máquina", s: 3, r: "12-15", kg: 25 },
    { nombre: "Face Pull en polea con soga", grupo: "hombros", equipo: "Polea", s: 3, r: "15", kg: 18 },
    { nombre: "Remo al mentón con barra Z", grupo: "hombros", equipo: "Barra", s: 3, r: "10-12", kg: 25 },

    // BÍCEPS
    { nombre: "Curl de bíceps con barra recta", grupo: "biceps", equipo: "Barra", s: 3, r: "10-12", kg: 25 },
    { nombre: "Curl de bíceps con barra W", grupo: "biceps", equipo: "Barra", s: 3, r: "10-12", kg: 25 },
    { nombre: "Curl alternado con mancuernas", grupo: "biceps", equipo: "Mancuernas", s: 3, r: "10-12", kg: 12 },
    { nombre: "Curl de bíceps sentado en banco inclinado", grupo: "biceps", equipo: "Mancuernas", s: 3, r: "10-12", kg: 10 },
    { nombre: "Curl martillo con mancuernas", grupo: "biceps", equipo: "Mancuernas", s: 3, r: "10-12", kg: 14 },
    { nombre: "Curl martillo en polea baja con soga", grupo: "biceps", equipo: "Polea", s: 3, r: "12", kg: 20 },
    { nombre: "Curl en banco Scott (Predicador)", grupo: "biceps", equipo: "Barra / Máq.", s: 3, r: "10-12", kg: 20 },
    { nombre: "Curl concentrado con mancuerna", grupo: "biceps", equipo: "Mancuernas", s: 3, r: "12", kg: 10 },
    { nombre: "Curl de bíceps en polea baja con barra", grupo: "biceps", equipo: "Polea", s: 3, r: "12", kg: 20 },
    { nombre: "Curl araña (Spider curl)", grupo: "biceps", equipo: "Mancuernas", s: 3, r: "12", kg: 10 },

    // TRÍCEPS
    { nombre: "Extensión de tríceps en polea alta con soga", grupo: "triceps", equipo: "Polea", s: 3, r: "12", kg: 20 },
    { nombre: "Extensión de tríceps en polea con barra recta", grupo: "triceps", equipo: "Polea", s: 3, r: "10-12", kg: 25 },
    { nombre: "Press francés con barra W", grupo: "triceps", equipo: "Barra", s: 3, r: "10-12", kg: 20 },
    { nombre: "Extensión trasnuca con soga en polea", grupo: "triceps", equipo: "Polea", s: 3, r: "12-15", kg: 18 },
    { nombre: "Copa de tríceps a dos manos con mancuerna", grupo: "triceps", equipo: "Mancuernas", s: 3, r: "12", kg: 18 },
    { nombre: "Press de banca con agarre cerrado", grupo: "triceps", equipo: "Barra", s: 3, r: "8-10", kg: 45 },
    { nombre: "Fondos entre bancos", grupo: "triceps", equipo: "Peso corporal", s: 3, r: "12-15", kg: 0 },
    { nombre: "Patada de tríceps en polea o mancuerna", grupo: "triceps", equipo: "Polea / Manc.", s: 3, r: "12-15", kg: 8 },

    // ABDOMEN / CORE
    { nombre: "Plancha abdominal frontal (Isométrica)", grupo: "core", equipo: "Peso corporal", s: 3, r: "45s", kg: 0 },
    { nombre: "Plancha lateral (Oblicuos)", grupo: "core", equipo: "Peso corporal", s: 3, r: "30s", kg: 0 },
    { nombre: "Crunch abdominal en colchoneta", grupo: "core", equipo: "Peso corporal", s: 3, r: "15-20", kg: 0 },
    { nombre: "Crunch abdominal en polea alta", grupo: "core", equipo: "Polea", s: 3, r: "15", kg: 25 },
    { nombre: "Elevación de piernas colgado", grupo: "core", equipo: "Barra", s: 3, r: "12", kg: 0 },
    { nombre: "Elevación de piernas acostado", grupo: "core", equipo: "Peso corporal", s: 3, r: "15", kg: 0 },
    { nombre: "Rueda abdominal (Ab Wheel)", grupo: "core", equipo: "Accesorio", s: 3, r: "10-12", kg: 0 },
    { nombre: "Giros rusos (Russian Twist) con disco", grupo: "core", equipo: "Disco", s: 3, r: "20", kg: 10 },
    { nombre: "Press Pallof anti-rotación en polea", grupo: "core", equipo: "Polea", s: 3, r: "12", kg: 15 },

    // CARDIO / FUNCIONAL
    { nombre: "Cinta de correr (Trote / Intervalos HIIT)", grupo: "cardio", equipo: "Cardio", s: 1, r: "20 min", kg: 0 },
    { nombre: "Bicicleta estática / Spinning", grupo: "cardio", equipo: "Cardio", s: 1, r: "25 min", kg: 0 },
    { nombre: "Elíptico / Escalador", grupo: "cardio", equipo: "Cardio", s: 1, r: "15 min", kg: 0 },
    { nombre: "Remo ergómetro (Concept2)", grupo: "cardio", equipo: "Cardio", s: 3, r: "500 m", kg: 0 },
    { nombre: "Saltos a la soga", grupo: "cardio", equipo: "Accesorio", s: 4, r: "60s", kg: 0 },
    { nombre: "Kettlebell Swing (Balanceo con pesa rusa)", grupo: "cardio", equipo: "Kettlebell", s: 4, r: "15", kg: 16 },
    { nombre: "Burpees", grupo: "cardio", equipo: "Peso corporal", s: 3, r: "12", kg: 0 },
    { nombre: "Battle Rope (Sogas de batalla)", grupo: "cardio", equipo: "Accesorio", s: 4, r: "30s", kg: 0 },
    { nombre: "Paseo del granjero (Farmer Walk)", grupo: "cardio", equipo: "Mancuernas", s: 3, r: "30 m", kg: 24 }
];

let grupoHevyActual = 'todos';
let hevySegundos = 90;
let hevyIntervalo = null;

function seleccionarGrupoHevy(grupo, btn) {
    grupoHevyActual = grupo;
    document.querySelectorAll('.btn-grupo-hevy').forEach(b => {
        b.className = "btn-grupo-hevy px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:text-white border border-slate-800 text-[11px] cursor-pointer";
    });
    if (btn) {
        btn.className = "btn-grupo-hevy px-3 py-1 rounded-lg bg-blue-600 text-white font-bold text-[11px] cursor-pointer";
    }
    filtrarCatalogoHevy();
}

function filtrarCatalogoHevy() {
    const grid = document.getElementById('gridCatalogoHevy');
    if (!grid) return;
    const query = (document.getElementById('buscadorCatalogoHevy')?.value || '').toLowerCase().trim();
    const filtrados = CATALOGO_HEVY.filter(item => {
        const okGrupo = (grupoHevyActual === 'todos') || (item.grupo === grupoHevyActual);
        const okTexto = !query || item.nombre.toLowerCase().includes(query) || item.equipo.toLowerCase().includes(query);
        return okGrupo && okTexto;
    });
    const contador = document.getElementById('contadorCatalogoHevy');
    if (contador) contador.textContent = `${filtrados.length} ejercicios`;
    grid.innerHTML = filtrados.map(ej => `
        <button type="button"
                onclick="autocompletarEjercicioHevy('${ej.nombre.replace(/'/g, "\\'")}', ${ej.s}, '${ej.r}', ${ej.kg})"
                class="p-2.5 rounded-xl bg-slate-900/90 hover:bg-blue-600/20 border border-slate-800 hover:border-blue-500/40 text-left transition flex items-center justify-between gap-2 cursor-pointer group">
            <div class="min-w-0">
                <span class="font-bold text-white group-hover:text-blue-300 text-[11px] block truncate">${ej.nombre}</span>
                <span class="text-[10px] text-slate-500 uppercase font-mono">${ej.grupo} • ${ej.equipo}</span>
            </div>
            <span class="text-blue-400 text-xs font-bold shrink-0">+</span>
        </button>
    `).join('');
}

function seleccionarModoRutina(modo) {
    document.querySelectorAll('.panel-modo-rutina').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.btn-modo-rutina').forEach(b => {
        b.className = "btn-modo-rutina px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition cursor-pointer";
    });
    const panel = document.getElementById('panel-rutina-' + modo);
    const btn = document.getElementById('btn-rutina-' + modo);
    if (panel) panel.classList.remove('hidden');
    if (btn) btn.className = "btn-modo-rutina px-4 py-2.5 rounded-xl text-xs font-bold bg-blue-600 text-white shadow-md shadow-blue-600/20 transition cursor-pointer";
}

function seleccionarDiaRutina(plan, idDia) {
    document.querySelectorAll('.contenido-dia-' + plan).forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.btn-dia-' + plan).forEach(btn => {
        btn.className = `btn-dia-${plan} ${plan === 'custom' ? 'p-3.5' : 'p-4'} rounded-2xl border text-left transition cursor-pointer bg-slate-900/60 border-slate-800 hover:border-slate-700`;
    });
    const contenidoActivo = document.getElementById(`contenido-dia-${plan}-${idDia}`);
    const btnActivo = document.getElementById(`btn-dia-${plan}-${idDia}`);

    if (contenidoActivo) contenidoActivo.classList.remove('hidden');
    if (btnActivo) {
        btnActivo.className = `btn-dia-${plan} ${plan === 'custom' ? 'p-3.5' : 'p-4'} rounded-2xl border text-left transition cursor-pointer bg-slate-900 border-2 border-blue-500 shadow-lg shadow-blue-500/10`;
    }
}

function toggleSerieHevy(btn, segundosDescanso) {
    const row = btn.closest('.set-row');
    if (!row) return;
    const completada = row.classList.toggle('completed');
    if (completada) {
        btn.className = "ml-auto w-7 h-7 rounded-lg bg-emerald-500 text-slate-950 font-black flex items-center justify-center transition cursor-pointer shadow-md shadow-emerald-500/30";
        iniciarTimerHevy(segundosDescanso || 90);
    } else {
        btn.className = "ml-auto w-7 h-7 rounded-lg bg-slate-800 hover:bg-emerald-600/30 text-slate-400 flex items-center justify-center transition cursor-pointer";
    }
    recalcularHevy();
}

function recalcularHevy() {
    let volumen = 0;
    let seriesOk = 0;
    document.querySelectorAll('.set-row.completed').forEach(row => {
        seriesOk++;
        const kg = parseFloat(row.querySelector('.hevy-kg')?.value || 0);
        const reps = parseFloat(row.querySelector('.hevy-reps')?.value || 0);
        volumen += (kg * reps);
    });
    const volEl = document.getElementById('hevyVolumenTotal');
    const serEl = document.getElementById('hevySeriesCompletadas');
    if (volEl) volEl.textContent = volumen.toLocaleString('es-AR') + ' kg';
    if (serEl) serEl.textContent = seriesOk;
}

function reiniciarChecksHevy() {
    document.querySelectorAll('.set-row.completed').forEach(row => {
        row.classList.remove('completed');
        const btn = row.querySelector('button');
        if (btn) btn.className = "ml-auto w-7 h-7 rounded-lg bg-slate-800 hover:bg-emerald-600/30 text-slate-400 flex items-center justify-center transition cursor-pointer";
    });
    recalcularHevy();
}

function actualizarDisplayTimerHevy() {
    const display = document.getElementById('hevyTimerDisplay');
    if (!display) return;
    const min = String(Math.floor(hevySegundos / 60)).padStart(2, '0');
    const seg = String(hevySegundos % 60).padStart(2, '0');
    display.textContent = `${min}:${seg}`;
}

function iniciarTimerHevy(segundos) {
    if (hevyIntervalo) clearInterval(hevyIntervalo);
    hevySegundos = segundos;
    actualizarDisplayTimerHevy();
    const display = document.getElementById('hevyTimerDisplay');
    if (display) {
        display.classList.remove('text-emerald-400');
        display.classList.add('text-blue-400');
    }
    hevyIntervalo = setInterval(() => {
        if (hevySegundos > 0) {
            hevySegundos--;
            actualizarDisplayTimerHevy();
        } else {
            clearInterval(hevyIntervalo);
            if (display) {
                display.classList.remove('text-blue-400');
                display.classList.add('text-emerald-400');
            }
        }
    }, 1000);
}

function ajustarTimerHevy(delta) {
    hevySegundos = Math.max(0, hevySegundos + delta);
    actualizarDisplayTimerHevy();
}

function autocompletarEjercicioHevy(nombre, series, reps, kg) {
    const elNombre = document.getElementById('inputCustomNombreEj');
    const elSeries = document.getElementById('inputCustomSeries');
    const elReps = document.getElementById('inputCustomReps');
    const elPeso = document.getElementById('inputCustomPeso');
    if (elNombre) elNombre.value = nombre;
    if (elSeries) elSeries.value = series;
    if (elReps) elReps.value = reps;
    if (elPeso) elPeso.value = kg;
}

function abrirModalEditarEjercicio(id, nombre, reps) {
    const elId = document.getElementById('editEjId');
    const elNombre = document.getElementById('editEjNombre');
    const elReps = document.getElementById('editEjReps');
    const modal = document.getElementById('modalEditarEjercicio');
    if (elId) elId.value = id;
    if (elNombre) elNombre.value = nombre;
    if (elReps) elReps.value = reps;
    if (modal) modal.classList.remove('hidden');
}

function cerrarModalEditarEjercicio() {
    const modal = document.getElementById('modalEditarEjercicio');
    if (modal) modal.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', function () {
    filtrarCatalogoHevy();
});