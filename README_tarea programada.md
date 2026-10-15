# Proveedores: servidores de desarrollo

## Configuracion automatica

La tarea programada `Proveedores Dev Servers` inicia Django y Vite al encender Windows. Se ejecuta como `SYSTEM` y lanza los servidores en segundo plano, sin ventanas de consola.

- Frontend: `http://10.0.111.61:5177` (la IP puede cambiar si cambia la red).
- Backend: `http://10.0.111.61:8004/api/`.
- Backend local: puerto `8004`.
- Frontend local: puerto `5177`.
- Lanzador: `start-dev-servers.ps1` en esta carpeta.

## Pausar el inicio automatico

Abre PowerShell como administrador y desactiva la tarea. Esto evita que los servidores vuelvan a iniciarse en el siguiente arranque, pero no detiene los que ya estan corriendo:

```powershell
Disable-ScheduledTask -TaskName 'Proveedores Dev Servers'
```

Para detener los servidores actuales, primero revisa que procesos ocupan los puertos:

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -in 8004, 5177 } |
  ForEach-Object {
    Get-CimInstance Win32_Process -Filter "ProcessId = $($_.OwningProcess)" |
      Select-Object ProcessId, Name, CommandLine
  } |
  Sort-Object ProcessId -Unique
```

Si confirmas que son los procesos de Django y Vite de este proyecto, detenlos por PID en PowerShell como administrador. Reemplaza los numeros por los que mostro el comando anterior:

```powershell
Stop-Process -Id 1234, 5678 -Force
```

> Detener por PID finaliza cualquier proceso que este usando esos puertos. Comprueba los nombres y comandos antes de hacerlo.

## Volver a iniciar

Reactiva la tarea para futuros arranques de Windows:

```powershell
Enable-ScheduledTask -TaskName 'Proveedores Dev Servers'
```

Inicia los servidores ahora, sin esperar a reiniciar Windows:

```powershell
& 'C:\Users\B219444\Documents\proveedores\start-dev-servers.ps1'
```

El lanzador omite cada servidor si su puerto ya esta ocupado.

## Ejecutar en consolas visibles para depurar

Si necesitas ver los logs en una consola, desactiva primero la tarea para que no vuelva a lanzar los servidores al proximo arranque. Luego ejecuta cada comando en una terminal separada.

Backend, desde la carpeta `backend`:

```powershell
..\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8004
```

Frontend, desde la carpeta `frontend`:

```powershell
npm run dev:network
```

Deten cada servidor visible con `Ctrl+C`. Cuando termines, puedes habilitar de nuevo la tarea programada.

## Consultar el estado de la tarea

```powershell
Get-ScheduledTask -TaskName 'Proveedores Dev Servers' |
  Select-Object TaskName, State,
    @{Name='Usuario'; Expression={$_.Principal.UserId}},
    @{Name='Activador'; Expression={$_.Triggers.CimClass.CimClassName}}

Get-ScheduledTaskInfo -TaskName 'Proveedores Dev Servers' |
  Select-Object LastRunTime, LastTaskResult
```

`LastTaskResult` igual a `0` indica que la ultima ejecucion de la tarea termino correctamente. La tarea solo lanza los servidores; despues de iniciarlos puede aparecer como `Ready` aunque Django y Vite sigan ejecutandose.
