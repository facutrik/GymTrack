/*
 * Cartel de confirmación y avisos de GymTrack (uno solo para toda la página).
 *
 * Uso en un formulario (no hace falta escribir JS):
 *   <form method="POST"
 *         data-confirmar="¿Confirmás dar de baja a Juan Pérez?"
 *         data-confirmar-titulo="Dar de baja socio"      (opcional)
 *         data-confirmar-boton="Sí, dar de baja"         (opcional)
 *         data-confirmar-tipo="peligro">                 (peligro | exito | aviso, opcional)
 *
 * Uso desde JS:
 *   gymConfirmar({ mensaje: '...', titulo: '...', boton: '...', tipo: 'peligro' }).then(ok => { ... });
 *   gymAviso('Seleccioná un socio de la lista.');   // reemplaza a alert()
 */
(function () {
    const TIPOS = {
        peligro: {
            icono: 'fa-triangle-exclamation',
            caja: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
            boton: 'bg-rose-600 hover:bg-rose-500 shadow-rose-600/20',
            titulo: 'Confirmar acción',
        },
        exito: {
            icono: 'fa-circle-check',
            caja: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
            boton: 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20',
            titulo: 'Confirmar acción',
        },
        aviso: {
            icono: 'fa-circle-info',
            caja: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
            boton: 'bg-blue-600 hover:bg-blue-500 shadow-blue-600/20',
            titulo: 'Atención',
        },
    };

    let modal = null;
    let resolverPendiente = null;

    function crearModal() {
        modal = document.createElement('div');
        modal.id = 'gymModalConfirmar';
        modal.className = 'fixed inset-0 z-[100] hidden items-center justify-center bg-slate-950/75 backdrop-blur-sm p-4';
        modal.innerHTML = `
            <div class="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-6 text-white shadow-2xl" role="dialog" aria-modal="true">
                <div class="flex items-start justify-between gap-4">
                    <div class="flex items-center gap-3">
                        <div data-gym-caja class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border">
                            <i data-gym-icono class="fa-solid text-sm"></i>
                        </div>
                        <div>
                            <h3 data-gym-titulo class="text-base font-bold text-white"></h3>
                            <p data-gym-mensaje class="mt-1 text-sm text-slate-300"></p>
                        </div>
                    </div>
                    <button type="button" data-gym-cerrar class="text-slate-400 hover:text-white transition cursor-pointer" aria-label="Cerrar">
                        <i class="fa-solid fa-xmark text-lg"></i>
                    </button>
                </div>
                <div class="mt-6 flex items-center justify-end gap-3">
                    <button type="button" data-gym-cancelar data-gym-cerrar
                        class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition cursor-pointer">
                        Cancelar
                    </button>
                    <button type="button" data-gym-aceptar
                        class="px-4 py-2 rounded-xl text-white text-xs font-semibold shadow-md transition cursor-pointer"></button>
                </div>
            </div>`;
        document.body.appendChild(modal);

        modal.querySelectorAll('[data-gym-cerrar]').forEach(b => b.addEventListener('click', () => cerrar(false)));
        modal.querySelector('[data-gym-aceptar]').addEventListener('click', () => cerrar(true));
        modal.addEventListener('click', e => { if (e.target === modal) cerrar(false); });
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) cerrar(false);
        });
    }

    function cerrar(resultado) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        if (resolverPendiente) {
            const resolver = resolverPendiente;
            resolverPendiente = null;
            resolver(resultado);
        }
    }

    function gymConfirmar(opciones = {}) {
        if (!modal) crearModal();
        if (resolverPendiente) cerrar(false);
        const tipo = TIPOS[opciones.tipo] || TIPOS.peligro;

        const caja = modal.querySelector('[data-gym-caja]');
        caja.className = `flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${tipo.caja}`;
        modal.querySelector('[data-gym-icono]').className = `fa-solid ${tipo.icono} text-sm`;
        modal.querySelector('[data-gym-titulo]').textContent = opciones.titulo || tipo.titulo;
        modal.querySelector('[data-gym-mensaje]').textContent = opciones.mensaje || '¿Deseás continuar?';

        const aceptar = modal.querySelector('[data-gym-aceptar]');
        aceptar.className = `px-4 py-2 rounded-xl text-white text-xs font-semibold shadow-md transition cursor-pointer ${tipo.boton}`;
        aceptar.textContent = opciones.boton || (opciones.soloAceptar ? 'Entendido' : 'Confirmar');
        modal.querySelector('[data-gym-cancelar]').hidden = !!opciones.soloAceptar;

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        aceptar.focus();
        return new Promise(resolve => { resolverPendiente = resolve; });
    }

    function gymAviso(mensaje, titulo) {
        return gymConfirmar({ mensaje, titulo, tipo: 'aviso', soloAceptar: true });
    }

    // Intercepta los formularios con data-confirmar antes que cualquier otro manejador
    document.addEventListener('submit', e => {
        const form = e.target;
        if (!(form instanceof HTMLFormElement) || !form.dataset.confirmar) return;
        if (form.dataset.gymConfirmado === '1') {
            delete form.dataset.gymConfirmado;
            return;
        }
        e.preventDefault();
        e.stopPropagation();
        const boton = e.submitter;
        gymConfirmar({
            mensaje: form.dataset.confirmar,
            titulo: form.dataset.confirmarTitulo,
            boton: form.dataset.confirmarBoton,
            tipo: form.dataset.confirmarTipo,
        }).then(ok => {
            if (!ok) return;
            form.dataset.gymConfirmado = '1';
            form.requestSubmit(boton || undefined);
        });
    }, true);

    window.gymConfirmar = gymConfirmar;
    window.gymAviso = gymAviso;
})();
