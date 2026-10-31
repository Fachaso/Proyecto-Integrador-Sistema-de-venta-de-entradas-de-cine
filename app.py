import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Configuración directa
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Habilitar CORS para permitir solicitudes del Frontend
CORS(app)

# Registro de Blueprints
from app.routes.auth_routes import auth_bp
from app.routes.candybar_routes import candybar_bp
from app.routes.peliculas_routes import pelicula_bp
from app.routes.sucursales_routes import sucursales_bp

app.register_blueprint(auth_bp)
app.register_blueprint(pelicula_bp)
app.register_blueprint(candybar_bp)
app.register_blueprint(sucursales_bp)

# Ruta de chequeo de salud
@app.get("/api/health")
def health_check():
    return jsonify({
        "status": "success",
        "message": "Backend Cine Paradiso activo y funcionando correctamente"
    }), 200

# Manejo global de errores en formato JSON
def manejar_error(error):
    estado = getattr(error, "code", 500)

    mensajes = {
        400: ("SOLICITUD_INVALIDA", "Petición no válida (Bad Request)"),
        401: ("NO_AUTENTICADO", "No autorizado (Requiere autenticación)"),
        403: ("ACCESO_DENEGADO", "Acceso prohibido (Permisos insuficientes)"),
        404: ("RECURSO_NO_ENCONTRADO", "Recurso no encontrado"),
        405: ("METODO_NO_PERMITIDO", "Método HTTP no permitido para esta ruta"),
        500: ("ERROR_INTERNO", "Error interno del servidor"),
    }

    codigo, mensaje = mensajes.get(estado, mensajes[500])

    return jsonify({
        "status": "error",
        "code": codigo,
        "message": mensaje
    }), estado

for estado in (400, 401, 403, 404, 405, 500):
    app.register_error_handler(estado, manejar_error)


if __name__ == "__main__":
    puerto = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "t"]
    
    app.run(host="0.0.0.0", port=puerto, debug=debug_mode)
