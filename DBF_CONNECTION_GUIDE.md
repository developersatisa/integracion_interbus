# Guía rápida: Conexión a DBF (servidor tierra)

Este documento explica **qué se necesita** y **cómo leer archivos DBF** en el servidor `tierra` (ej. `/mnt/tierra_laboral_atinomi/`).  
Está pensado para otro agente/compañero que quiera acceder a DBF desde Python.

## Requisitos

- **Python** en el servidor.
- Paquete **dbfread** instalado:
  ```bash
  pip install dbfread
  ```
- **Ruta accesible** al directorio DBF (ejemplo típico):
  ```
  /mnt/tierra_laboral_atinomi/
  ```
- Permisos de lectura sobre el archivo DBF.

## Archivos DBF frecuentes

- `contrcen.dbf` (centros / worker places)
- `convvaca.dbf` o `convvacas.dbf` (balances)

> Importante: el archivo puede venir con **diferentes mayúsculas** (`CONTRCEN.DBF`, `Contrcen.dbf`, etc.).

## Verificar existencia del archivo

```bash
ls -la /mnt/tierra_laboral_atinomi/
```

Si no aparece, verificar la **ruta real** o el **mount** del servidor.

## Lectura simple con Python

```python
from dbfread import DBF

dbf_path = "/mnt/tierra_laboral_atinomi/CONTRCEN.DBF"

table = DBF(dbf_path, load=True, char_decode_errors="ignore")

print("Total registros:", len(table))

# Ver campos disponibles
first = next(iter(table), None)
if first:
    print("Campos:", list(first.keys()))
    print("Primer registro:", dict(first))
```

## Campos en DBF (ejemplo `contrcen.dbf`)

Los nombres suelen venir en **mayúsculas**, por ejemplo:
- `CODIGOP`
- `CODIGODOM`
- `VIA`
- `CALLE`
- `CPOSTAL`
- `MUNICIPIO`
- `PROVINCIA`

## Problemas comunes

1) **Archivo no encontrado**  
   - Revisar ruta real
   - Probar variantes de nombre (`CONTRCEN.DBF`, `Contrcen.dbf`, etc.)

2) **Codificación rara**  
   - Usar `char_decode_errors="ignore"`
   - Si hace falta, usar `encoding` en DBF:
     ```python
     DBF(dbf_path, encoding="latin1")
     ```

3) **Permisos**  
   - Asegurar lectura del archivo: `chmod` o permisos de usuario.

## Recomendación de integración

Si se integra en este repo:
- Centralizar la ruta DBF en una variable (`DBF_BASE_PATH`) para no hardcodear.
- Intentar buscar el archivo con **variantes de mayúsculas**.

## Ejemplo de búsqueda con variantes

```python
from pathlib import Path

base = Path("/mnt/tierra_laboral_atinomi/")
for name in ["CONTRCEN.DBF", "Contrcen.dbf", "contrcen.dbf"]:
    p = base / name
    if p.exists():
        print("Encontrado:", p)
        break
```
