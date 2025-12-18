import os
import uuid
from flask import Flask, request, jsonify
from PIL import Image

from app.db_utils import VectorDB, S3Storage
from app.ml_utils import embed_image

app = Flask(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/cats")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "images")


@app.route("/similar", methods=["POST"])
def similar():
    """
    POST /similar — пpинимaeт изoбpaжeниe, вoзвpaщaeт списoк пoхoжих зaписeй
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    try:
        img = Image.open(file.stream)
        embedding = embed_image(img)

        results = db.find_similar(embedding, limit=5)

        response_data = []
        for img_id, distance in results:
            response_data.append({
                "id": img_id,
                "distance": float(distance)
            })

        return jsonify({"similar": response_data})
    except Exception as e:
        # Печатаем ошибку в консоль докера для отладки
        print(f"API Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload():
    """
    POST /upload — зaгpужaeт oднo изoбpaжeниe, сoxpaняeт в S3 и в БД
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Генерируем уникальное имя файла, чтобы не перезатереть старые
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"

        temp_path = f"/tmp/{filename}"
        file.save(temp_path)

        # 1. Загрузка в S3
        url = s3.upload_image(temp_path, filename)

        # 2. Генерация эмбеддинга
        embedding = embed_image(temp_path)

        # 3. Сохранение в БД
        db.insert_image(embedding)

        # Удаляем временный файл
        os.remove(temp_path)

        return jsonify({"status": "ok", "url": url, "filename": filename})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """
    GET  /stats - возвращает статистику по БД
    """
    try:
        if db.conn is None:
            db.connect()
        cur = db.conn.cursor()
        cur.execute("SELECT count(*) FROM embeddings;")
        count = cur.fetchone()[0]
        cur.close()
        return jsonify({"total_images": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    db = VectorDB(DB_URL)
    db.init_table()

    s3 = S3Storage(S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET)
    s3.ensure_bucket_exists()

    app.run(host='0.0.0.0', port=5000)