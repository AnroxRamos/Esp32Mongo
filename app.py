import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuración mejorada de MongoDB
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000,
        retryWrites=True,
        retryReads=True
    )
    # Test connection
    client.admin.command('ping')
    db = client["BasePryEsp32"]
    collection = db["Datos"]
    logger.info("✅ Conexión exitosa a MongoDB Atlas")
except Exception as e:
    logger.error(f"❌ Error de conexión a MongoDB: {str(e)}")
    raise e

@app.route("/api/data", methods=["POST"])
def recibir_dato():
    try:
        data = request.get_json()
        required_keys = ["dispositivo", "temperatura", "humedad", "luz", "movimiento"]
        
        if not all(k in data for k in required_keys):
            return jsonify({"error": "Faltan campos requeridos en el JSON"}), 400

        documento = {
            "dispositivo": data["dispositivo"],
            "temperatura": data["temperatura"],
            "humedad": data["humedad"],
            "luz": data["luz"],
            "movimiento": data["movimiento"],
            "timestamp": datetime.utcnow() - timedelta(hours=6)
        }

        result = collection.insert_one(documento)
        logger.info(f"Datos insertados con ID: {result.inserted_id}")
        return jsonify({
            "message": "Datos guardados correctamente",
            "id": str(result.inserted_id)
        }), 200

    except Exception as e:
        logger.error(f"Error al guardar en MongoDB: {str(e)}")
        return jsonify({"error": "Error al procesar los datos"}), 500

@app.route("/api/datos", methods=["GET"])
def ver_datos():
    try:
        datos = list(collection.find().sort("timestamp", -1).limit(50))
        for d in datos:
            d["_id"] = str(d["_id"])
            d["timestamp"] = d["timestamp"].isoformat()

        return jsonify(datos), 200
    except Exception as e:
        logger.error(f"Error al recuperar datos: {str(e)}")
        return jsonify({"error": "Error al obtener datos"}), 500

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "active",
        "service": "API Flask con MongoDB",
        "documentation": "/api/data (POST) y /api/datos (GET)"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
