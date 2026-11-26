// Busca sin distinguir mayúsculas ni tildes
function filtrarDisciplinas() {
    const normalizar = (t) => t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const q = normalizar(document.getElementById('filtroDisciplinaInput')?.value.trim() || '');
    let visibles = 0;
    document.querySelectorAll('.tarjeta-disciplina').forEach(card => {
        const coincide = normalizar(card.textContent).includes(q);
        card.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    document.getElementById('sinResultadosDisciplinas')?.classList.toggle('hidden', visibles > 0);
}
