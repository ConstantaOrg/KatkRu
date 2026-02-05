"""
Мониторинг ресурсов контейнера (CPU, RAM)
"""
import asyncio
import psutil
from core.utils.logger import log_event


class ResourceMonitor:
    """Мониторинг использования ресурсов"""

    @staticmethod
    def get_cpu_usage() -> float:
        """Получить текущую загрузку CPU в процентах"""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def get_memory_usage() -> dict:
        """Получить информацию об использовании памяти"""
        one_mb = 1_048_576
        mem = psutil.virtual_memory()
        return {
            'total_mb': round(mem.total / one_mb, 2),
            'used_mb': round(mem.used / one_mb, 2),
            'available_mb': round(mem.available / one_mb, 2),
            'percent': mem.percent
        }
    
    @staticmethod
    def log_resource_usage():
        """Логировать текущее использование ресурсов"""
        cpu = ResourceMonitor.get_cpu_usage()
        mem = ResourceMonitor.get_memory_usage()
        
        log_event(
            f"Загруженность сервера: CPU {cpu}%, RAM {mem['percent']}%",
            **{
                'cpu_percent': cpu,
                'memory_percent': mem['percent'],
                'memory_used_mb': mem['used_mb'],
                'memory_total_mb': mem['total_mb'],
                'metric_type': 'resource_usage'
            }
        )


async def resource_monitoring_task(interval: int = 60):
    """
    Фоновая задача для периодического мониторинга ресурсов
    
    Args:
        interval: Интервал в секундах между замерами (по умолчанию 60)
    """
    while True:
        try:
            ResourceMonitor.log_resource_usage()
        except Exception as e:
            log_event(f"Error in resource monitoring: {e}", level='ERROR')
        
        await asyncio.sleep(interval)
