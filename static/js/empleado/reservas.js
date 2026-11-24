function filtrarDisciplinas() {
    const input = document.getElementById('filtroDisciplinaInput');
    const q = (input ? input.value : '').toLowerCase().trim();
    document.querySelectorAll('.tarjeta-disciplina').forEach(card => {
        const texto = (card.getAttribute('data-busqueda') || '') + ' ' + card.textContent.toLowerCase();
        card.style.display = texto.includes(q) ? 'block' : 'none';
    });
}