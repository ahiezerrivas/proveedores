# Respaldo y restauración de PostgreSQL

Esta guía explica cómo guardar y restaurar la base de datos PostgreSQL del proyecto en Windows PowerShell. Los archivos de respaldo contienen información sensible: guárdalos en una ubicación protegida y no los subas al repositorio ni los envíes por canales públicos.

## Antes de comenzar

Los comandos usan `proveedores` como nombre de base de datos, `localhost` como servidor, `5432` como puerto y `postgres` como usuario. Si `backend\.env` define `DB_NAME`, `DB_HOST`, `DB_PORT` o `DB_USER`, reemplaza los valores correspondientes en los comandos.

Abre PowerShell en la raíz del proyecto y define una carpeta de respaldo fuera del repositorio. Ajusta la ruta de PostgreSQL si instalaste otra versión:

```powershell
$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$respaldoDir = "C:\RespaldosProveedores"
New-Item -ItemType Directory -Force -Path $respaldoDir
```

Si `pg_dump.exe`, `pg_restore.exe` y `psql.exe` ya están en `PATH`, puedes ejecutar sus nombres directamente y omitir `$pgBin`.

Los programas de PostgreSQL solicitarán la contraseña de `DB_USER`. No la escribas directamente en el comando ni la guardes en este documento.

## Crear un respaldo recomendado

El formato custom de PostgreSQL es compacto y permite restaurar con `pg_restore`:

```powershell
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
& "$pgBin\pg_dump.exe" -h localhost -p 5432 -U postgres -F c --no-owner --no-acl -f "$respaldoDir\proveedores-$fecha.backup" proveedores
```

Comprueba que el comando terminó con código cero y que el archivo existe:

```powershell
if ($LASTEXITCODE -ne 0) { throw "Falló el respaldo de PostgreSQL." }
Get-Item "$respaldoDir\proveedores-$fecha.backup"
```

## Crear un respaldo en formato SQL legible

Este formato genera un archivo `.sql` de texto que puedes inspeccionar:

```powershell
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
& "$pgBin\pg_dump.exe" -h localhost -p 5432 -U postgres --no-owner --no-acl --format=plain --encoding=UTF8 -f "$respaldoDir\proveedores-$fecha.sql" proveedores
if ($LASTEXITCODE -ne 0) { throw "Falló el respaldo SQL de PostgreSQL." }
```

No abras ni edites el archivo para compartirlo: puede contener nombres, datos de cuentas y otros datos privados.

## Restaurar un respaldo custom

La restauración debe hacerse sobre una base de datos vacía. El siguiente ejemplo crea una base nueva llamada `proveedores_restauracion` y carga el respaldo. No sobrescribe ni elimina la base original:

```powershell
& "$pgBin\createdb.exe" -h localhost -p 5432 -U postgres proveedores_restauracion
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear la base de datos de restauración." }

& "$pgBin\pg_restore.exe" -h localhost -p 5432 -U postgres --no-owner --no-acl -d proveedores_restauracion "$respaldoDir\proveedores-AAAAMMDD-HHMMSS.backup"
if ($LASTEXITCODE -ne 0) { throw "Falló la restauración del respaldo." }
```

Reemplaza el nombre del archivo por el respaldo que quieras probar. Valida los datos y la aplicación en esa base antes de decidir cualquier cambio en producción.

## Restaurar un archivo SQL

Crea también una base vacía antes de cargar el archivo:

```powershell
& "$pgBin\createdb.exe" -h localhost -p 5432 -U postgres proveedores_restauracion
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear la base de datos de restauración." }

& "$pgBin\psql.exe" -h localhost -p 5432 -U postgres -d proveedores_restauracion -X -v ON_ERROR_STOP=1 -f "$respaldoDir\proveedores-AAAAMMDD-HHMMSS.sql"
if ($LASTEXITCODE -ne 0) { throw "Falló la restauración SQL." }
```

`ON_ERROR_STOP=1` hace que `psql` detenga la restauración al primer error.

## Archivos PDF adjuntos

La base de datos guarda la referencia al PDF, pero el contenido de los archivos se almacena aparte en `backend\private_uploads\`. Para poder recuperar también los contratos adjuntos, copia esa carpeta de forma segura junto con el respaldo:

```powershell
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
Compress-Archive -Path .\backend\private_uploads\* -DestinationPath "$respaldoDir\proveedores-archivos-$fecha.zip"
```

Mantén juntos el respaldo de la base de datos y el ZIP de archivos de la misma fecha. Al restaurar, coloca los PDFs de nuevo bajo `backend\private_uploads\`, conservando su estructura de carpetas.

## Recomendaciones

- Haz un respaldo antes de migraciones, actualizaciones o cambios de estructura.
- Conserva varias copias en un disco o ubicación protegida distinta del equipo que ejecuta PostgreSQL.
- Prueba periódicamente una restauración en una base separada; un archivo existente no garantiza por sí solo que sea restaurable.
- Los respaldos no sustituyen la copia de los PDFs ni la custodia segura de `backend\.env`.
