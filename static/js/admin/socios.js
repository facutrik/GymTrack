function openModalAlta() {
    document.getElementById('modalAltaSocio').classList.remove('hidden');
}

function closeModalAlta() {
    document.getElementById('modalAltaSocio').classList.add('hidden');
}

    const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('nuevo') === '1') {
            openModalAlta();
        }