"""
Конфигурация дополнительных текстов (notices) для эндпоинтов.
Позволяет добавлять дополнительную документацию к конкретным эндпоинтам.
"""

from typing import Dict, Optional

from .constants import ConfigFilePaths
from . import handlers


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
        return handlers.find_config_file()
    
    def load_config(self):
        """Загрузка конфигурации из файла."""
        if self.config_path:
            self.notices = handlers.load_config_from_file(self.config_path)
    
    def get_notice(self, method: str, path: str) -> Optional[Dict[str, str]]:
        """
        Получить notice для эндпоинта.
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            path: Путь эндпоинта
            
        Returns:
            Словарь с notice текстами или None если не найдено
        """
        return handlers.get_notice_for_endpoint(self.notices, method, path)
    
    def add_notice(self, method: str, path: str, notice_type: str, text: str):
        """
        Добавить notice для эндпоинта.
        
        Args:
            method: HTTP метод
            path: Путь эндпоинта
            notice_type: Тип notice (warning, info, important, etc.)
            text: Текст notice
        """
        self.notices = handlers.add_notice_to_config(
            self.notices, method, path, notice_type, text
        )
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Сохранить конфигурацию в файл.
        
        Args:
            output_path: Путь для сохранения. Если не указан, использует текущий config_path.
        """
        save_path = output_path or self.config_path or ConfigFilePaths.PRIMARY
        handlers.save_config_to_file(self.notices, save_path)
    
    def create_example_config(self, output_path: str = ConfigFilePaths.PRIMARY):
        """Создать пример конфигурационного файла."""
        handlers.create_example_config_file(output_path)


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
    return handlers.format_notice_for_markdown(notice_type, text)