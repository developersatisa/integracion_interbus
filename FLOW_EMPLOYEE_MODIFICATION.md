# Flow Employee Modifications

## Identificacion del trabajador
- Buscar por `codiemp + nombre + apellidos`.
- Si no hay resultado y llega `NASS`, buscar por `codiemp + NASS` (numeross).
- Si no hay resultado y llega `VATNum`, buscar por `codiemp + NIF/DNI`.

## Baja
- Si `EndDate` es valida (no placeholder) y existe trabajador, se trata como baja.
- Si no existe trabajador, se continua el flujo y se trata como alta.

## Alta y modificacion
- Se mantiene la logica actual de fechas y orden cronologico.
- `CCC` se trata como dato del perfil y no define alta/modificacion.

## Campos compartidos (pendiente)
- Direccion, DNI, cuenta bancaria, email, telefono, nacionalidad, fecha de nacimiento.
- En el futuro, si cambian estos datos se generarian registros por cada perfil activo del trabajador.
