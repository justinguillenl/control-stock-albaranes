# Control de stock desde albaranes

Herramienta en Python para tiendas y pequeños almacenes que reciben mercancía con albaranes en PDF. En lugar de teclear cada línea en el Excel de stock, la herramienta:

1. **Lee** los albaranes PDF de una carpeta.
2. **Descarta** los albaranes ya registrados (por ejemplo, el mismo PDF reenviado por email).
3. **Traduce** la referencia del proveedor a la referencia interna y convierte cajas en unidades.
4. **Deja las líneas en una hoja de revisión.** El stock no cambia hasta que una persona confirma.
5. **Actualiza** el stock, registra cada movimiento y genera una lista de productos bajo mínimo.

> Todos los datos del repositorio son ficticios.

## Cómo funciona

```
data/entrada/*.pdf ──► python main.py leer ──► hoja "Pendiente"
                                                  │  (revisión: escribir "sí")
                                                  ▼
                       python main.py aplicar ──► Productos + Movimientos + Alertas
```

El Excel `data/stock.xlsx` tiene cinco hojas:

| Hoja | Para qué sirve |
|---|---|
| Productos | Stock actual y stock mínimo de cada referencia interna |
| Movimientos | Historial de entradas, con albarán y fecha |
| Equivalencias | Referencia del proveedor → referencia interna, y unidades por caja |
| Pendiente | Líneas leídas a la espera de confirmación |
| Alertas | Productos bajo mínimo y cantidad sugerida para pedir |

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Prueba con los datos de ejemplo

```bash
python scripts/generar_ejemplos.py   # crea stock.xlsx y 3 albaranes ficticios
python main.py leer
```

Salida esperada:

```
LEÍDO     albaran_AN-2026-0153.pdf: 3 líneas
LEÍDO     albaran_AN-2026-0154.pdf: 3 líneas (1 referencias desconocidas)
DUPLICADO copia_reenviada_por_email.pdf: el albarán AN-2026-0153 ya estaba registrado
```

Abre `data/stock.xlsx`, hoja **Pendiente**:

- Las líneas con estado `OK` solo necesitan un `sí` en la columna `confirmar`.
- La línea `REF DESCONOCIDA` trae una sugerencia (`¿RN-BI-044 (BUJ-IRI-01)?`). Si es correcta, escribe la `ref_interna`, ajusta `unidades` si viene en cajas y añade la equivalencia a la hoja **Equivalencias** para la próxima vez.

Guarda, cierra Excel y aplica:

```bash
python main.py aplicar
```

## Tests

```bash
python -m pytest
```

Comprueban la extracción del PDF, la conversión de cajas a unidades, la detección de referencias desconocidas y de duplicados, y que el stock no cambia sin confirmación.

## Estructura

```
config/proveedores.json      Cómo leer el albarán de cada proveedor
src/stock_albaranes/
    extraer.py               PDF → número, fecha y líneas
    equivalencias.py         Referencia del proveedor → referencia interna
    excel.py                 Lectura y escritura del Excel sin perder el formato
    procesar.py              Órdenes "leer" y "aplicar"
scripts/generar_ejemplos.py  Datos ficticios de prueba
tests/                       Tests con pytest
main.py                      Punto de entrada
```

## Añadir un proveedor

Añade una entrada en `config/proveedores.json` con el texto que identifica al proveedor, las expresiones regulares para el número y la fecha, y cómo se llaman sus columnas. Después, añade sus referencias en la hoja **Equivalencias**.

## Próximas versiones

- [ ] **v2:** varios proveedores con formatos distintos; guardar en Equivalencias las referencias resueltas a mano.
- [ ] **v3:** albaranes escaneados o fotografiados (reconocimiento de texto).
- [ ] **v4:** ejecutable con doble clic (PyInstaller) para usarlo sin instalar Python.
- [ ] Salidas de mercancía (ventas) para tener el stock completo.

## Limitaciones actuales

- Solo PDFs digitales (con texto seleccionable).
- Un formato de albarán por proveedor.
- La regla de reposición es sencilla: pedir hasta el doble del stock mínimo.
