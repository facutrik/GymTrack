function abrirModalLegalGlobal(id) {
    const m = document.getElementById(id);
        if (m) m.classList.remove('hidden');
    }

function cerrarModalLegalGlobal(id) {
    const m = document.getElementById(id);
        if (m) m.classList.add('hidden');
    }

window.addEventListener('click', function(e) {
    if (['modal-terminos-global', 'modal-privacidad-global', 'modal-arrepentimiento-global'].includes(e.target.id)) {
        e.target.classList.add('hidden');
    }
});