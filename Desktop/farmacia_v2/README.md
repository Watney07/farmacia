# 💊 Sistema de Farmacia — Grupo 6

**SENA · Análisis y Desarrollo de Software 228185**

Sistema web para control de inventario de medicamentos, ventas y alertas de vencimiento.

**Integrantes:**
- Escobar Esquivel Harold Andres
- Romero Marin Johan Steven
- Guzman Nuñez Brian Sneider

---

## 🛠 Tecnologías

- Python 3.11+ · Django 4.2 · Django REST Framework 3.15
- PostgreSQL en Supabase
- Bootstrap 5.3
- Token Authentication · python-decouple · dj-database-url

---

## 📁 Estructura del proyecto

```
farmacia_grupo6/
├── config/                  ← Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── farmacia/                ← App principal
│   ├── models.py            ← Medicamento, Lote, Venta
│   ├── serializers.py       ← Validaciones + lógica FIFO
│   ├── views.py             ← ViewSets + vistas de auth
│   ├── auth_urls.py         ← URLs de autenticación
│   ├── frontend_urls.py     ← URLs de templates HTML
│   ├── frontend_views.py    ← Vistas que renderizan HTML
│   ├── admin.py
│   └── migrations/
├── templates/               ← HTML + Bootstrap
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── medicamentos.html
│   ├── ventas.html
│   └── alertas.html
├── cargar_datos.py          ← Script de datos de prueba
├── .env.example             ← Plantilla de variables de entorno
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/farmacia-grupo6.git
cd farmacia-grupo6
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus datos:

```env
SECRET_KEY=una-clave-secreta-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Copia la URI desde: Supabase → Project Settings → Database → URI
DATABASE_URL=postgresql://postgres:tu_password@db.xxxx.supabase.co:5432/postgres

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

> ⚠️ **NUNCA subas el `.env` a GitHub.** Ya está en el `.gitignore`.

---

## 🗄️ Cómo obtener el DATABASE_URL de Supabase

1. Entra a [supabase.com](https://supabase.com) y abre tu proyecto.
2. Ve a **Project Settings → Database**.
3. Busca la sección **Connection string** y selecciona **URI**.
4. Copia la cadena — tiene el formato:
   ```
   postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres
   ```
5. Reemplaza `[PASSWORD]` con tu contraseña y pégala en `.env` como `DATABASE_URL`.

---

### 4. Aplicar migraciones (crea las tablas en Supabase)

```bash
python manage.py migrate
```

### 5. Crear superusuario para el admin

```bash
python manage.py createsuperuser
```

### 6. Cargar datos de prueba

```bash
python manage.py shell < cargar_datos.py
```

### 7. Correr el servidor

```bash
python manage.py runserver
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔗 Endpoints de la API

### Autenticación (pública)

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/auth/registro/` | Crear cuenta |
| POST | `/api/auth/login/` | Iniciar sesión → devuelve token |
| POST | `/api/auth/logout/` | Cerrar sesión (requiere token) |
| GET  | `/api/auth/perfil/` | Datos del usuario (requiere token) |

### Medicamentos

| Método | URL | Auth |
|--------|-----|------|
| GET    | `/api/medicamentos/` | No |
| POST   | `/api/medicamentos/` | Token |
| GET    | `/api/medicamentos/{id}/` | No |
| PUT    | `/api/medicamentos/{id}/` | Token |
| PATCH  | `/api/medicamentos/{id}/` | Token |
| DELETE | `/api/medicamentos/{id}/` | Token |
| GET    | `/api/medicamentos/alertas/` | No — **Regla de negocio** |

### Lotes y Ventas

| Método | URL |
|--------|-----|
| GET/POST | `/api/lotes/` |
| GET/PUT/PATCH/DELETE | `/api/lotes/{id}/` |
| GET/POST | `/api/ventas/` — POST ejecuta FIFO automáticamente |
| GET/PUT/PATCH | `/api/ventas/{id}/` |
| DELETE | `/api/ventas/{id}/` — cancela y restaura stock |

---

## 🔒 Usar el token en Thunder Client

1. `POST /api/auth/login/` → body: `{"username":"...", "password":"..."}`
2. Copia el valor de `token` en la respuesta.
3. En cada petición protegida agrega el header:
   ```
   Authorization: Token aqui-va-tu-token
   ```

---

## ⚙️ Regla de negocio especial — FIFO + Alertas

### FIFO (First In, First Out)
Al `POST /api/ventas/`, el sistema automáticamente:
1. Busca lotes no vencidos del medicamento, ordenados por `fecha_vencimiento` (más antiguo primero).
2. Descuenta las unidades del lote más antiguo.
3. Si no hay stock suficiente retorna `HTTP 400` con mensaje claro.

### Alertas de vencimiento
`GET /api/medicamentos/alertas/` retorna:
- Medicamentos con menos de **10 unidades** en stock.
- Lotes que vencen en menos de **30 días**.

---

## 🌐 Vistas Frontend

| URL | Vista |
|-----|-------|
| `/` | Dashboard con contadores |
| `/login/` | Login y registro |
| `/medicamentos/` | CRUD visual de medicamentos |
| `/ventas/` | Registrar y consultar ventas |
| `/alertas/` | Panel de alertas |
