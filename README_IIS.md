# Despliegue en Windows con IIS y NSSM

Esta guía publica React como archivos estáticos en IIS y ejecuta Django REST Framework detrás de IIS con Waitress, administrado como servicio de Windows por NSSM. PostgreSQL permanece como base de datos. El navegador utiliza un solo origen para la aplicación, `/api/` y `/admin/`; IIS reenvía las solicitudes de Django a `127.0.0.1:8004`.

> Ejecuta los pasos de instalación y configuración de IIS/NSSM en una consola elevada como administrador. Sustituye las rutas de ejemplo por la ruta real del proyecto.

## 1. Requisitos de servidor

- Windows Server o Windows con IIS habilitado.
- IIS con **Static Content**, **Default Document** y **Request Filtering**.
- Extensiones **IIS URL Rewrite 2** y **Application Request Routing (ARR)**.
- Python, Node.js/npm y PostgreSQL instalados.
- NSSM disponible en el servidor.
- Certificado HTTPS para el nombre DNS del sitio.

En IIS Manager, abre **Application Request Routing Cache → Server Proxy Settings**, marca **Enable proxy** y aplica. La opción **Preserve host header** puede no aparecer en esa pantalla; configúrala desde PowerShell como administrador con `appcmd`:

```powershell
$appcmd = "$env:windir\System32\inetsrv\appcmd.exe"
& $appcmd set config -section:system.webServer/proxy /preserveHostHeader:"True" /commit:apphost
& $appcmd list config -section:system.webServer/proxy
```

En la salida, confirma que `preserveHostHeader="true"`. Es necesario conservar el hostname para que `ALLOWED_HOSTS` y la sesión funcionen correctamente. En **URL Rewrite**, verifica que esté instalada la extensión.

## 2. Preparar una instalación independiente

`C:\Apps\proveedores\` es la **carpeta raíz de instalación del proyecto**, no la carpeta donde IIS publica el sitio. Coloca allí el proyecto completo, con sus carpetas `backend\` y `frontend\`; no copies solo el build del frontend. Por ejemplo:

```text
C:\Apps\proveedores\
├── backend\
├── frontend\
├── .venv\
└── logs\
```

El build de React se generará más adelante en `C:\Apps\proveedores\frontend\dist\`, y **esa carpeta `dist\` será la raíz física del sitio IIS**. El backend, el entorno virtual y los logs permanecen fuera de la raíz publicada por IIS.

Copia o despliega primero el proyecto completo en `C:\Apps\proveedores\`. No ejecutes el servicio desde una carpeta temporal, una unidad de red o el perfil de un usuario que pueda cambiar. Luego abre PowerShell y sitúate en esa carpeta:

```powershell
Set-Location C:\Apps\proveedores
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
```

Configura `backend\.env`. No guardes las credenciales en el repositorio ni las incluyas en comandos o logs:

```dotenv
DJANGO_SECRET_KEY=<clave-aleatoria-larga-y-privada>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=proveedores.empresa.local
DB_NAME=proveedores
DB_USER=<usuario-de-servicio-postgresql>
DB_PASSWORD=<clave-de-postgresql>
DB_HOST=localhost
DB_PORT=5432
CSRF_TRUSTED_ORIGINS=https://proveedores.empresa.local
CORS_ALLOWED_ORIGINS=https://proveedores.empresa.local
```

Genera una clave nueva con:

```powershell
..\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el valor generado a `DJANGO_SECRET_KEY` en `backend\.env`. Usa un usuario de PostgreSQL con permisos solo sobre esta base de datos; evita `postgres` para el servicio de producción.

Aplica migraciones y recopila los archivos estáticos de Django:

```powershell
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

Las migraciones crean el modelo de proveedores y los grupos **Administradores** y **Consulta**. Crea la cuenta administrativa una vez:

```powershell
..\.venv\Scripts\python.exe manage.py createsuperuser
```

El PDF privado se almacena en `backend\private_uploads\`; respalda esa carpeta junto con PostgreSQL. No la publiques como directorio virtual de IIS.

## 3. Configurar Waitress como servicio con NSSM

Waitress ya está incluido en `backend\requirements.txt`. Abre una consola como administrador, ajusta la ruta y registra el servicio:

```powershell
$root = "C:\Apps\proveedores"
$nssm = "C:\nssm\win64\nssm.exe"

New-Item -ItemType Directory -Force "$root\logs" | Out-Null
& $nssm install ProveedoresAPI "$root\.venv\Scripts\waitress-serve.exe"
& $nssm set ProveedoresAPI AppDirectory "$root\backend"
& $nssm set ProveedoresAPI AppParameters "--listen=127.0.0.1:8004 --threads=8 config.wsgi:application"
& $nssm set ProveedoresAPI Start SERVICE_AUTO_START
& $nssm set ProveedoresAPI AppStdout "$root\logs\waitress-out.log"
& $nssm set ProveedoresAPI AppStderr "$root\logs\waitress-error.log"
& $nssm set ProveedoresAPI AppRotateFiles 1
& $nssm set ProveedoresAPI AppRotateOnline 1
& $nssm set ProveedoresAPI AppRotateBytes 10485760
& $nssm start ProveedoresAPI
```

Crea `C:\Apps\proveedores\logs` antes de iniciar el servicio. Si la instalación del proyecto no se llama `C:\Apps\proveedores`, actualiza `$root`.

Waitress escucha solo en loopback, no expongas el puerto 8004 al firewall. El servicio necesita permiso de lectura para el código, `.env` y el entorno virtual, permiso de escritura en `backend\private_uploads\` y en `logs\`, y acceso a PostgreSQL. Para producción, configura el servicio NSSM con una cuenta de Windows dedicada en **Services → ProveedoresAPI → Properties → Log On** y otorga únicamente esos permisos.

Administración del servicio:

```powershell
& $nssm status ProveedoresAPI
& $nssm restart ProveedoresAPI
& $nssm stop ProveedoresAPI
```

## 4. Compilar React para producción

La compilación debe usar `/api` como base de API, ya que IIS reenvía esa ruta al backend bajo el mismo origen. Desde PowerShell, en `frontend`:

```powershell
Set-Location C:\Apps\proveedores\frontend
$env:VITE_API_URL = "/api"
npm ci
npm run build
Remove-Item Env:VITE_API_URL
```

El sitio estático final queda en `frontend\dist\`. La variable `VITE_API_URL` se incorpora durante la compilación: si cambia el dominio o la ruta del backend, vuelve a compilar.

## 5. Configurar el sitio IIS

### Si por ahora solo se publica el backend

No cambies la ruta física de **Default Web Site** a `frontend\dist`; esa ruta corresponde a la publicación completa del frontend y se configura cuando React esté listo. Para publicar temporalmente solo API y admin mediante el sitio existente, conserva su raíz actual (`C:\inetpub\wwwroot`) y:

1. Confirma que **ARR** tenga el proxy habilitado y que **URL Rewrite** esté instalado.
2. Crea en `C:\inetpub\wwwroot\web.config` reglas de proxy solo para `/api/` y `/admin/` hacia `http://127.0.0.1:8004/`. Si ya existe ese archivo, integra las reglas sin reemplazar su configuración existente:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <configuration>
     <system.webServer>
       <rewrite>
         <rules>
           <rule name="Proxy API and Django admin to Waitress" stopProcessing="true">
             <match url="^(api/.*|admin/.*)$" />
             <action type="Rewrite" url="http://127.0.0.1:8004/{R:1}" appendQueryString="true" />
           </rule>
         </rules>
       </rewrite>
     </system.webServer>
   </configuration>
   ```

3. Bajo **Default Web Site**, agrega un directorio virtual con alias `static` y ruta física `C:\Apps\proveedores\backend\staticfiles`. La identidad del grupo de aplicaciones necesita permiso de lectura.
4. Accede a `http(s)://<nombre-del-sitio>/admin/` y comprueba que carguen los estilos. Configura HTTPS antes de permitir el acceso desde otras máquinas o introducir credenciales; la captura actual muestra un enlace HTTP.

Esta configuración no publica React. Cuando despliegues el frontend, sigue los pasos de publicación completa de abajo y usa `frontend\dist` como raíz del sitio.

1. Crea un sitio IIS llamado `Proveedores` con raíz física en `C:\Apps\proveedores\frontend\dist`.
2. Añade el binding HTTPS para `proveedores.empresa.local` y selecciona el certificado TLS.
3. Fuerza HTTPS desde IIS o el balanceador. No publiques el login por HTTP.
4. Comprueba que `frontend\dist\web.config` exista. Vite lo copia desde `frontend\public\web.config`. Las reglas envían `/api/...` y `/admin/...` a Waitress y sirven React para las rutas del frontend.
5. En **ARR → Server Proxy Settings**, confirma que el proxy esté habilitado. Comprueba también `preserveHostHeader="true"` con el comando `appcmd` del apartado 1.
6. Crea un directorio virtual IIS `/static` apuntando a `C:\Apps\proveedores\backend\staticfiles`. Así se sirven los estilos del admin de Django. Dale a la identidad del grupo de aplicaciones permiso de lectura sobre esa carpeta.
7. En el firewall, permite HTTPS al sitio desde las redes autorizadas. No abras el puerto 8004.

`frontend\public\web.config` contiene las reglas de proxy y fallback de React, además de un límite de solicitud ligeramente mayor que 10 MB para permitir el upload multipart de PDF. Verifica el límite también en cualquier proxy o balanceador delante de IIS.

El `.env` debe listar el dominio de producción, no la IP de desarrollo:

- `DJANGO_ALLOWED_HOSTS`: el nombre DNS sin esquema ni puerto, por ejemplo `proveedores.empresa.local`.
- `CSRF_TRUSTED_ORIGINS`: origen HTTPS completo, por ejemplo `https://proveedores.empresa.local`.
- `CORS_ALLOWED_ORIGINS`: el mismo origen HTTPS. El proxy mantiene frontend y API en el mismo origen, por lo que no es necesario habilitar CORS para otros dominios.

Reinicia el servicio después de cambiar backend, configuración, migraciones o dependencias:

```powershell
& $nssm restart ProveedoresAPI
```

## 6. Actualizaciones

Haz copia de seguridad de PostgreSQL y `backend\private_uploads\` antes de publicar una actualización. Después de actualizar el código:

```powershell
$root = "C:\Apps\proveedores"
$nssm = "C:\Tools\nssm\win64\nssm.exe"

Set-Location C:\Apps\proveedores\backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py collectstatic --noinput

Set-Location C:\Apps\proveedores\frontend
$env:VITE_API_URL = "/api"
npm ci
npm run build
Remove-Item Env:VITE_API_URL

& $nssm restart ProveedoresAPI
```

Comprueba el login, operaciones CRUD según el rol, el acceso al admin, la vista previa de PDF y los logs de IIS/NSSM. Mantén `DJANGO_DEBUG=false`; no uses `manage.py runserver` en producción.

## 7. Diagnóstico rápido

- **502.3 / conexión rechazada:** confirma que `ProveedoresAPI` está iniciado y que Waitress escucha en `127.0.0.1:8004`; revisa `logs\waitress-error.log`.
- **404 en `/api/` o `/admin/`:** confirma ARR, URL Rewrite, que `web.config` está en la raíz publicada y que el servicio responde en loopback.
- **403 CSRF:** entra por HTTPS usando el mismo hostname definido en `CSRF_TRUSTED_ORIGINS`; reinicia NSSM tras cambiar `.env` y borra las cookies antiguas del navegador.
- **Admin sin estilos:** revisa `collectstatic`, el directorio virtual `/static` y sus permisos de lectura.
- **PDF no se carga:** confirma el límite del proxy, los permisos de escritura del servicio en `backend\private_uploads\` y el espacio disponible.
- **No iniciar:** comprueba primero que exista `C:\Apps\proveedores\.venv\Scripts\waitress-serve.exe`; si no existe, crea el entorno virtual e instala `backend\requirements.txt` como se indica en el apartado 2. Luego revisa `logs\waitress-error.log` y el Visor de eventos, y confirma que la cuenta del servicio puede leer `.env` y conectarse a PostgreSQL.
