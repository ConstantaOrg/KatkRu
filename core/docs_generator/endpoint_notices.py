"""
Конфигурация дополнительных текстов (notices) для эндпоинтов.
Позволяет добавлять дополнительную документацию к конкретным эндпоинтам.
"""

from typing import Dict, Optional
import json
import os
from pathlib import Path


class EndpointNoticesConfig:
    """Управление дополнительными текстами для эндпоинтов."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация конфигурации notices.
        
        Args:
            config_path: Путь к файлу конфигурации. Если не указан, ищет в стандартных местах.
        """
        self.notices: Dict[str, Dict[str, str]] = {}
        self.config_path = config_path or self._find_config_file()
        self.load_config()
    
    def _find_config_file(self) -> Optional[str]:
        """Поиск файла конфигурации в стандартных местах."""
        possible_paths = [
            "docs_endpoint_notices.json",
            ".kiro/docs_endpoint_notices.json",
            "core/docs_generator/endpoint_notices.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def load_config(self):
        """Загрузка конфигурации из файла."""
        if not self.config_path or not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.notices = data.get('endpoint_notices', {})
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"Warning: Failed to load endpoint notices config: {e}")
    
    def get_notice(self, method: str, path: str) -> Optional[Dict[str, str]]:
        """
        Получить notice для эндпоинта.
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            path: Путь эндпоинта
            
        Returns:
            Словарь с notice текстами или None если не найдено
        """
        endpoint_key = f"{method.upper()} {path}"
        return self.notices.get(endpoint_key)
    
    def add_notice(self, method: str, path: str, notice_type: str, text: str):
        """
        Добавить notice для эндпоинта.
        
        Args:
            method: HTTP метод
            path: Путь эндпоинта
            notice_type: Тип notice (warning, info, important, etc.)
            text: Текст notice
        """
        endpoint_key = f"{method.upper()} {path}"
        if endpoint_key not in self.notices:
            self.notices[endpoint_key] = {}
        self.notices[endpoint_key][notice_type] = text
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Сохранить конфигурацию в файл.
        
        Args:
            output_path: Путь для сохранения. Если не указан, использует текущий config_path.
        """
        save_path = output_path or self.config_path or "docs_endpoint_notices.json"
        
        config_data = {
            "endpoint_notices": self.notices,
            "_description": "Конфигурация дополнительных текстов для эндпоинтов API документации",
            "_format": "Ключ: 'METHOD /path', значение: объект с типами notices"
        }
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def create_example_config(self, output_path: str = "docs_endpoint_notices.json"):
        """Создать пример конфигурационного файла."""
        example_config = {
            "endpoint_notices": {
                "POST /api/v1/private/n8n_ui/cards/save": {
                    "warning": "⚠️ Этот эндпоинт может возвращать конфликты при сохранении. Обязательно обрабатывайте ответы с success: false.",
                    "info": "💡 При конфликтах рекомендуется показать пользователю альтернативные варианты времени или преподавателей."
                },
                "POST /api/v1/private/n8n_ui/std_ttable/check_exists": {
                    "important": "🔍 Этот эндпоинт выполняет сложную проверку актуальности данных. Время выполнения может достигать 5-10 секунд.",
                    "info": "📊 Результат содержит детальную информацию о различиях в группах, преподавателях и дисциплинах."
                },
                "GET /api/v1/private/disciplines/get": {
                    "info": "📚 Поддерживает пагинацию через параметры limit и offset.",
                    "tip": "💡 Для лучшей производительности рекомендуется использовать limit не более 100."
                }
            },
            "_description": "Конфигурация дополнительных текстов для эндпоинтов API документации",
            "_format": "Ключ: 'METHOD /path', значение: объект с типами notices",
            "_available_types": [
                "info - общая информация",
                "warning - предупреждения", 
                "important - важные замечания",
                "tip - советы по использованию",
                "example - дополнительные примеры",
                "performance - замечания по производительности"
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        
        print(f"Создан пример конфигурации: {output_path}")


# Глобальный экземпляр для использования в генераторе
_notices_config = None

def get_notices_config() -> EndpointNoticesConfig:
    """Получить глобальный экземпляр конфигурации notices."""
    global _notices_config
    if _notices_config is None:
        _notices_config = EndpointNoticesConfig()
    return _notices_config

def format_notice_for_markdown(notice_type: str, text: str) -> str:
    """
    Форматировать notice для вставки в Markdown документацию.
    
    Args:
        notice_type: Тип notice
        text: Текст notice
        
    Returns:
        Отформатированный Markdown текст
    """
    type_icons = {
        'info': 'ℹ️',
        'warning': '⚠️', 
        'important': '❗',
        'tip': '💡',
        'example': '📝',
        'performance': '⚡'
    }
    
    icon = type_icons.get(notice_type, '📌')
    type_name = notice_type.upper()
    
    return f"\n> **{icon} {type_name}:** {text}\n"