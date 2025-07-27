from flask import Flask, jsonify
import threading
import time

app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint для Railway"""
    return jsonify({
        "status": "healthy",
        "service": "Telegram Finance Bot",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    """Дополнительный health check endpoint"""
    return jsonify({"status": "ok"})

def run_web_server():
    """Запуск веб-сервера в отдельном потоке"""
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    import os
    run_web_server() 