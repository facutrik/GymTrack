function abrirModalEditarEmpleado(id, nombre, apellido, username, email, rol) {
    document.getElementById('editEmpId').value = id;
    document.getElementById('editEmpNombre').value = nombre;
    document.getElementById('editEmpApellido').value = apellido;
    document.getElementById('editEmpUsername').value = username;
    document.getElementById('editEmpEmail').value = email;
    document.getElementById('editEmpRol').value = rol;
    document.getElementById('modalEditarEmpleado').classList.remove('hidden');
}

function cerrarModalEditarEmpleado() {
    document.getElementById('modalEditarEmpleado').classList.add('hidden');
}
// El panel del admin enlaza a ?nuevo=1 para abrir directamente el alta de empleado
if (new URLSearchParams(window.location.search).get('nuevo') === '1') {
    document.getElementById('modalAltaEmpleado')?.classList.remove('hidden');
}
