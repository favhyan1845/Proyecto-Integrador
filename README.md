# BiciParking - Sistema de Gestión Integral

Este proyecto es una prueba de concepto para la gestión de un BiciParking que incluye el manejo de bicicletas tradicionales y eléctricas (e-bikes), con integración de pagos y escaneo QR.

## Tecnologías Utilizadas

- **Backend:** FastAPI, SQLAlchemy (ORM), SQLite (por defecto, escalable a MySQL)
- **Frontend:** Vue.js 3, TailwindCSS, Vite

## Estructura del Proyecto

- `/backend`: Contiene la API, los modelos de base de datos y la lógica de negocio.
- `/frontend`: Contiene la interfaz de usuario en Vue.

## Instrucciones de Ejecución

### 1. Levantar el Backend (FastAPI)

1. Ve a la carpeta `backend/`.
2. Crea un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate # En Windows: venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura la Base de Datos:
   - Por defecto, el archivo `.env` usa SQLite (`biciparking.db`).
   - Para usar **MySQL**, edita `backend/.env` y descomenta/modifica la línea `DATABASE_URL` con tus credenciales de MySQL (ej. `mysql+pymysql://root:password@localhost:3306/biciparking_db`).
5. Ejecuta el servidor:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
6. La API estará disponible en `http://localhost:8000`. Puedes ver la documentación interactiva en `http://localhost:8000/docs`.

### 2. Levantar el Frontend (Vue.js)

1. Ve a la carpeta `frontend/`.
2. Instala las dependencias:
   ```bash
   npm install
   ```
3. Ejecuta el servidor de desarrollo:
   ```bash
   npm run dev
   ```
4. La aplicación estará disponible en `http://localhost:3000`.

## Flujo de Prueba
1. Puedes crear usuarios y registrar bicicletas desde los endpoints Swagger (`/docs`) del backend.
2. Cada bicicleta registrada generará un `qr_code`.
3. En la interfaz web (Frontend), ve a la pestaña "Simulador QR".
4. Ingresa el `qr_code` de la bicicleta y presiona "Entrar".
5. Verás el registro activo en el Dashboard.
6. Ingresa el mismo `qr_code` y presiona "Salir". El sistema calculará el costo de parqueo y te permitirá simular el pago en línea.
