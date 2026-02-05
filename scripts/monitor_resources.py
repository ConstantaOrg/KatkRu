#!/usr/bin/env python3
"""
Скрипт для мониторинга ресурсов (CPU, RAM)
Запускается через crontab каждую минуту
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import psutil


def get_resource_metrics() -> dict:
    """Получить метрики ресурсов"""
    one_mb = 1_048_576
    mem = psutil.virtual_memory()
    
    return {
        'cpu_percent': round(psutil.cpu_percent(interval=1), 2),
        'memory_percent': round(mem.percent, 2),
        'memory_used_mb': round(mem.used / one_mb, 2),
        'memory_total_mb': round(mem.total / one_mb, 2),
    }


def log_metrics(metrics: dict, log_file: Path):
    """Записать метрики в лог файл в формате JSON"""
    log_entry = {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "message": f"Загруженность сервера: CPU {metrics['cpu_percent']}%, RAM {metrics['memory_percent']}%",
        "service": "fastapi-app",
        "environment": "production",
        "method": "",
        "url": "",
        "func": "monitor_resources",
        "location": "scripts/monitor_resources.py",
        "line": 0,
        "ip": "",
        "cpu_percent": metrics['cpu_percent'],
        "memory_percent": metrics['memory_percent'],
        "memory_used_mb": metrics['memory_used_mb'],
        "memory_total_mb": metrics['memory_total_mb'],
        "metric_type": "resource_usage"
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def main():
    """Основная функция"""
    # Путь к лог файлу
    log_file = Path(__file__).parent.parent / 'logs' / 'app.log'
    
    # Создаём директорию если не существует
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Получаем метрики
        metrics = get_resource_metrics()
        
        # Логируем
        log_metrics(metrics, log_file)
        
        # Опционально: вывод в stdout для отладки
        # print(f"✓ Logged: CPU {metrics['cpu_percent']}%, RAM {metrics['memory_percent']}%")
        
    except Exception as e:
        # Логируем ошибку
        error_entry = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "message": f"Resource monitoring error: {str(e)}",
            "service": "fastapi-app",
            "environment": "production",
            "method": "",
            "url": "",
            "func": "monitor_resources",
            "location": "scripts/monitor_resources.py",
            "line": 0,
            "ip": ""
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
        
        sys.exit(1)


if __name__ == '__main__':
    main()
