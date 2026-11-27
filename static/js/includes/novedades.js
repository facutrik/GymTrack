// Campana de novedades del nav (templates/includes/campana_novedades.html)
(function () {
    const boton = document.getElementById('btnCampanaNovedades');
    const panel = document.getElementById('panelNovedades');
    if (!boton || !panel) return;

    function csrf() {
        const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function abrir() {
        panel.classList.remove('hidden');
        boton.setAttribute('aria-expanded', 'true');
        const badge = document.getElementById('badgeNovedades');
        if (badge) {
            // Al abrir la campana, las novedades quedan como leídas
            fetch(boton.dataset.urlLeidas, { method: 'POST', headers: { 'X-CSRFToken': csrf() } })
                .then(r => { if (r.ok) badge.remove(); })
                .catch(() => {});
        }
    }

    function cerrar() {
        panel.classList.add('hidden');
        boton.setAttribute('aria-expanded', 'false');
    }

    boton.addEventListener('click', e => {
        e.stopPropagation();
        panel.classList.contains('hidden') ? abrir() : cerrar();
    });
    document.addEventListener('click', e => {
        if (!panel.classList.contains('hidden') && !panel.contains(e.target)) cerrar();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrar(); });
})();
