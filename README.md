# Gestión de proveedores

Proyecto inicial con Django REST Framework, React y PostgreSQL. Permite listar, buscar, crear, editar y eliminar proveedores.

Los campos almacenados son proveedor, contrato, tarifa mensual, servicios y estado. **Acciones** es la columna de controles (editar/eliminar) del frontend, no un campo de la base de datos.

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

La API queda en `http://localhost:8000/api/proveedores/`. El acceso a la API requiere iniciar sesión. La tarifa se almacena como número decimal, sin fijar moneda.

### Usuarios y roles

Django crea las tablas de usuarios, grupos/roles y permisos (`auth_user`, `auth_group`, `auth_permission` y sus tablas relacionadas). La migración inicial crea los roles **Administradores** y **Consulta**. Los usuarios autenticados con el rol Consulta pueden ver proveedores; solo un superusuario o un usuario del grupo Administradores puede crearlos, editarlos o eliminarlos. Esta regla se aplica también en la API, no solo en la interfaz.

Crea la cuenta inicial de administración después de aplicar las migraciones:

```powershell
python manage.py createsuperuser
```

Al actualizar el proyecto, vuelve a ejecutar las migraciones para crear la columna y habilitar el campo para adjuntar PDF:

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

Abre `http://127.0.0.1:5176`. El servidor está configurado para usar IPv4 y un puerto no reservado por Windows en esta máquina. Para cambiar la dirección base de la API, define `VITE_API_URL` (por defecto `http://localhost:8000/api`).

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
