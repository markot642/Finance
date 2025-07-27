#!/usr/bin/env python3
"""
Тест health check для Railway
"""

import requests
import time
import os

def test_health_check():
    """Тестирование health check"""
    port = int(os.environ.get('PORT', 5000))
    url = f"http://localhost:{port}/"
    
    print(f"Тестирование health check на {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Статус код: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check работает!")
            return True
        else:
            print("❌ Health check не работает!")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

if __name__ == '__main__':
    test_health_check() 