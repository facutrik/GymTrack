function abrirModalCrearPlan() {
    document.getElementById('modalPlanTitulo').textContent = 'Crear Plan de Membresía';
    document.getElementById('modalPlanAccion').value = 'crear';
    document.getElementById('modalPlanId').value = '';
    document.getElementById('modalPlanNombre').value = '';
    document.getElementById('modalPlanPrecio').value = '';
    document.getElementById('modalPlanDuracion').value = '30';
    document.getElementById('modalPlanDesc').value = '';
    document.getElementById('modalPlan').classList.remove('hidden');
}

function abrirModalEditarPlan(id, nombre, precio, duracion, desc) {
    document.getElementById('modalPlanTitulo').textContent = 'Editar Plan de Membresía';
    document.getElementById('modalPlanAccion').value = 'editar';
    document.getElementById('modalPlanId').value = id;
    document.getElementById('modalPlanNombre').value = nombre;
    document.getElementById('modalPlanPrecio').value = precio;
    document.getElementById('modalPlanDuracion').value = duracion;
    document.getElementById('modalPlanDesc').value = desc;
    document.getElementById('modalPlan').classList.remove('hidden');
}

function cerrarModalPlan() {
    document.getElementById('modalPlan').classList.add('hidden');
}