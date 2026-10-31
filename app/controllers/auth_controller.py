from flask import current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import (
    cerrar_sesion,
    datos_publicos_usuario,
    iniciar_sesion,
    respuesta_error,
)
from app.repositories.db_connection import execute_query


def registro():
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("nombre", "")).strip()
    email = str(datos.get("email", "")).strip().lower()
    password = str(datos.get("password", ""))

    # 1. Validaciones básicas de entrada
    if not nombre or not email or not password:
        return respuesta_error("DATOS_INVALIDOS", "Nombre, email y contraseña son obligatorios", 400)
    if "@" not in email:
        return respuesta_error("EMAIL_INVALIDO", "El formato del email es inválido", 400)
    if len(password) < 6:
        return respuesta_error("PASSWORD_INVALIDA", "La contraseña debe tener al menos 6 caracteres", 400)

    try:
        # 2. Comprobar si el email ya está registrado
        existente = execute_query(
            "SELECT id_usuario FROM usuarios WHERE email = %s",
            (email,),
            fetchone=True,
        )
        if existente:
            return respuesta_error("EMAIL_DUPLICADO", "El email ya está registrado", 409)

        # 3. Guardar en la base de datos
        id_nuevo = execute_query(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (%s, %s, %s, 'CLIENTE')",
            (nombre, email, generate_password_hash(password)),
            commit=True,
        )

        # 4. Devolver datos del usuario creado sin hacer otro SELECT
        usuario = {"id_usuario": id_nuevo, "nombre": nombre, "email": email, "rol": "CLIENTE"}
        return jsonify({"status": "success", "data": datos_publicos_usuario(usuario)}), 201

    except Exception:
        current_app.logger.exception("Error al registrar usuario")
        return respuesta_error("ERROR_INTERNO", "Error interno del servidor", 500)


def login():
    datos = request.get_json(silent=True) or {}
    email = str(datos.get("email", "")).strip().lower()
    password = str(datos.get("password", ""))

    if not email or not password:
        return respuesta_error("DATOS_INVALIDOS", "Email y contraseña son obligatorios", 400)

    try:
        usuario = execute_query(
            "SELECT id_usuario, nombre, email, password_hash, rol FROM usuarios WHERE email = %s",
            (email,),
            fetchone=True,
        )
        if not usuario or not check_password_hash(usuario["password_hash"], password):
            return respuesta_error("CREDENCIALES_INVALIDAS", "Credenciales inválidas", 401)

        iniciar_sesion(usuario)
        return jsonify({"status": "success", "data": datos_publicos_usuario(usuario)}), 200

    except Exception:
        current_app.logger.exception("Error al iniciar sesión")
        return respuesta_error("ERROR_INTERNO", "Error interno del servidor", 500)


def logout():
    if not session.get("id_usuario"):
        return respuesta_error("NO_AUTENTICADO", "No hay una sesión activa", 401)

    cerrar_sesion()
    return jsonify({"status": "success", "data": {"message": "Sesión cerrada"}}), 200


def me():
    id_usuario = session.get("id_usuario")
    if not id_usuario:
        return respuesta_error("NO_AUTENTICADO", "No hay una sesión activa", 401)

    try:
        usuario = execute_query(
            "SELECT id_usuario, nombre, email, rol FROM usuarios WHERE id_usuario = %s",
            (id_usuario,),
            fetchone=True,
        )
        if not usuario:
            cerrar_sesion()
            return respuesta_error("NO_AUTENTICADO", "La sesión ya no es válida", 401)

        return jsonify({"status": "success", "data": datos_publicos_usuario(usuario)}), 200

    except Exception:
        current_app.logger.exception("Error al consultar usuario autenticado")
        return respuesta_error("ERROR_INTERNO", "Error interno del servidor", 500)
