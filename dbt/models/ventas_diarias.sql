-- Resumen diario: una fila por fecha de negocio.
-- cantidad (INTEGER) * precio_unitario (DECIMAL(12,2)) da un DECIMAL con dos
-- decimales y su suma sigue siendo DECIMAL: no se pasa por FLOAT ni se redondea.
select
    fecha_venta,
    count(*) as numero_ventas,
    sum(cantidad) as unidades_vendidas,
    sum(cantidad * precio_unitario) as ingreso_total
from {{ ref('stg_ventas') }}
group by fecha_venta
