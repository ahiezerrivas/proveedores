# Gestión de proveedores

Proyecto inicial con Django REST Framework, React y PostgreSQL. Permite listar, buscar, crear, editar y eliminar proveedores.

Para crear y restaurar respaldos de PostgreSQL y de los PDF adjuntos, consulta la [guía de respaldos](./README_RESPALDO_BD.md).

La base de datos separa proveedores y contratos: cada proveedor tiene un código opcional (único cuando se proporciona) y nombre; cada contrato pertenece a un proveedor y contiene sus tarifas mensual, trimestral, semestral y anual, servicios, estado y PDF. La migración agrupa automáticamente los registros existentes por nombre exacto, conservando sus contratos, tarifas y documentos. Revisa luego los códigos y consolida manualmente nombres que representen al mismo proveedor pero estén escritos de forma distinta. Los campos son opcionales; las tarifas vacías se guardan como `0.00`. **Acciones** es la columna de controles (editar/eliminar) del frontend, no un campo de la base de datos.

El panel muestra los montos con el símbolo `$`. El directorio y sus controles usan tipografía ampliada para facilitar la lectura. Cada proveedor puede tener un PDF adjunto opcional (hasta 10 MB); solo usuarios con sesión iniciada pueden descargarlo y el backend valida que el contenido sea PDF. Los archivos se guardan en `backend/private_uploads/`, fuera de las rutas públicas de archivos estáticos.

## Requisitos

- Python 3.10 o superior
- Node.js y npm
- PostgreSQL instalado y en ejecución

## Backend

Desde la raíz del proyecto, en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edita `backend\.env` con las credenciales correctas de PostgreSQL. Django carga automáticamente ese archivo.

Crea la base de datos `proveedores` desde pgAdmin o con `createdb proveedores`. Si el servicio de PostgreSQL está detenido, inicia `postgresql-x64-18` desde Servicios de Windows o con PowerShell como administrador (`Start-Service postgresql-x64-18`), y luego aplica las migraciones:

```powershell
cd backend
python manage.py migrate
python manage.py runserver
```

La API de proveedores queda en `http://localhost:8000/api/proveedores/` y la de contratos en `http://localhost:8000/api/contratos/`. El acceso a ambas requiere iniciar sesión. Las tarifas se almacenan como números decimales, sin fijar moneda.

La API registra las solicitudes realizadas por usuarios autenticados en `/api/` (incluidos inicio y cierre de sesión), junto con usuario, fecha, método, ruta, resultado e IP. Cada registro incluye además una acción (`accion`: inicio/cierre de sesión, consulta, creación, actualización o eliminación) y una descripción legible (`descripcion`), por ejemplo «Creó el proveedor «Servicios del Norte» (PR-001) con el contrato «CT-2026-01»» o «Actualizó el contrato «CT-1» del proveedor «Servicios del Norte». Cambios: estado: Activo → Inactivo». Los registros anteriores a esta función reciben una descripción genérica (por ejemplo «Consultó la lista de proveedores») al migrar. No guarda el contenido de las solicitudes. La consulta paginada está disponible en `/api/auditoria/` (filtrable con `?usuario=<nombre>` y `?accion=<accion>`; `/api/auditoria/usuarios/` lista los usuarios con actividad) exclusivamente para el grupo **Administradores** y superusuarios; en el frontend aparece la sección **Auditoría** solo para ellos.

### Usuarios y roles

Django crea las tablas de usuarios, grupos/roles y permisos (`auth_user`, `auth_group`, `auth_permission` y sus tablas relacionadas). Lo que cada usuario puede hacer depende de los **permisos de Django** que tenga (directamente o por sus grupos), no del nombre del grupo. La API revisa estos permisos y `GET /api/auth/session/` devuelve la lista en `permisos`; el frontend muestra u oculta las opciones según esa lista.

| Permiso | Permite |
| --- | --- |
| `view_proveedor` / `view_contrato` | Ver proveedores y contratos (incluye descargar el PDF) |
| `add_contrato` | Crear contratos |
| `change_contrato` | Editar contratos y quitar su PDF |
| `delete_contrato` | Eliminar contratos |
| `add_proveedor` | Registrar un proveedor nuevo al crear un contrato |
| `change_proveedor` | Cambiar el código de un proveedor |
| `delete_proveedor` | Eliminar proveedores sin contratos |
| `view_registroauditoria` | Ver la sección y la API de Auditoría |

Las migraciones crean los grupos **Administradores** (todos los permisos anteriores) y **Consulta** (solo `view_proveedor` y `view_contrato`). Un superusuario tiene todos los permisos.

Para crear un rol nuevo, entra al admin de Django (`/admin/`) → **Grupos** → **Agregar grupo**, elige sus permisos y asígnalo a los usuarios. Por ejemplo, un grupo **Supervisor** que administra todo menos la auditoría lleva todos los permisos de *proveedor* y *contrato*, pero no «Can view registro auditoria». Los cambios aplican la próxima vez que el usuario cargue la página; no hace falta tocar código.

Crea la cuenta inicial de administración después de aplicar las migraciones:

```powershell
python manage.py createsuperuser
```

Al actualizar el proyecto, haz un respaldo de la base de datos y vuelve a ejecutar las migraciones. La migración de normalización separa los proveedores y sus contratos, agrupando los registros anteriores por el nombre exacto del proveedor y conservando los datos y documentos asociados:

```powershell
python manage.py migrate
```

Inicia sesión en `http://localhost:8000/admin/` con esa cuenta para crear usuarios y asignarles el grupo **Administradores** o **Consulta**. En la interfaz de React, inicia sesión con el nombre de usuario y la contraseña creados. No se crean contraseñas predeterminadas.

## Frontend

En otra terminal, desde la raíz:

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://127.0.0.1:5176`. La sección de auditoría tiene su propia ruta (`http://127.0.0.1:5176/auditoria`, con React Router), así que se puede recargar o abrir directamente; si un usuario sin rol de administrador entra a esa ruta, se le redirige a la página principal. Después de actualizar el proyecto, vuelve a ejecutar `npm install` para instalar `react-router`. El servidor está configurado para usar IPv4 y un puerto no reservado por Windows en esta máquina. Para cambiar la dirección base de la API, define `VITE_API_URL` (por defecto `http://localhost:8000/api`).

### Ver el frontend desde otro dispositivo en la red local

Desde `frontend`, inicia Vite escuchando en las interfaces de red:

```powershell
npm run dev:network
```

En Windows, ejecuta `ipconfig` y busca la dirección **IPv4** de la conexión Wi-Fi o Ethernet. Desde el otro dispositivo, conectado a la misma red, abre `http://<IP-IPv4-de-esta-PC>:5176` (por ejemplo, `http://192.168.1.25:5176`). Si no carga, permite Node.js o el puerto TCP `5176` en el Firewall de Windows para redes privadas.

Para usar también la API desde otro dispositivo, configura `VITE_API_URL` con `http://<IP-IPv4-de-esta-PC>:8004/api` en `frontend\.env`, inicia Django con `python manage.py runserver 0.0.0.0:8004` y agrega `http://<IP-IPv4-de-esta-PC>:5176` tanto a `CORS_ALLOWED_ORIGINS` como a `CSRF_TRUSTED_ORIGINS` en `backend\.env`. Agrega también la IP de esta PC a `DJANGO_ALLOWED_HOSTS`. Reinicia Django y Vite después de cambiar la configuración. **Usa la IP de la PC también en `VITE_API_URL`, no `localhost`: si abres el frontend por IP pero llamas a `localhost`, el navegador trata la cookie de sesión/CSRF como perteneciente a otro sitio y puede rechazar el inicio de sesión.**

## Nota del entorno

El entorno virtual `.venv` se crea en la raíz. En algunas instalaciones de PowerShell puede ser necesario permitir la activación del entorno o invocar directamente `.\.venv\Scripts\python.exe`.

Para desplegar en producción con IIS, ARR, URL Rewrite y NSSM, consulta la [guía de despliegue para IIS](./README_IIS.md).
