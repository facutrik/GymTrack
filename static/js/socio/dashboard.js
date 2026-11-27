function switchTab(tabId) {
    const secRutina = document.getElementById('seccion-rutina');
    const secActividades = document.getElementById('seccion-actividades');
    const secPerfil = document.getElementById('seccion-perfil');

    if (secRutina) secRutina.style.display = 'none';
    if (secActividades) secActividades.style.display = 'none';
    if (secPerfil) secPerfil.style.display = 'none';

    const tabRutina = document.getElementById('tab-rutina');
    const tabActividades = document.getElementById('tab-actividades');
    const tabPerfil = document.getElementById('tab-perfil');

    const inactivo = "main-btn p-6 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition text-left w-full cursor-pointer";
    const activo = "main-btn active p-6 rounded-3xl bg-slate-900/90 border-2 border-blue-500 transition text-left w-full cursor-pointer shadow-lg shadow-blue-500/10";

    if (tabRutina) tabRutina.className = inactivo;
    if (tabActividades) tabActividades.className = inactivo;
    if (tabPerfil) tabPerfil.className = inactivo;

    if (tabId === 'rutina') {
        if (secRutina) secRutina.style.display = 'block';
        if (tabRutina) tabRutina.className = activo;
    } else if (tabId === 'actividades') {
        if (secActividades) secActividades.style.display = 'block';
        if (tabActividades) tabActividades.className = activo;
    } else if (tabId === 'perfil') {
        if (secPerfil) secPerfil.style.display = 'block';
        if (tabPerfil) tabPerfil.className = activo;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    const diaParam = urlParams.get('dia');

    if (tab === 'custom') {
        switchTab('rutina');
        if (typeof seleccionarModoRutina === 'function') seleccionarModoRutina('custom');
        if (diaParam && typeof seleccionarDiaRutina === 'function') seleccionarDiaRutina('custom', diaParam);
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (tab === 'actividades') {
        switchTab('actividades');
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (tab === 'perfil') {
        switchTab('perfil');
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (typeof cerrarModalEditarEjercicio === 'function') cerrarModalEditarEjercicio();
            if (typeof cerrarModalPagoSocio === 'function') cerrarModalPagoSocio();
        }
    });
});