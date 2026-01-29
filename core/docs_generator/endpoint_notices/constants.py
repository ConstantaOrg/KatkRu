"""
Constants for endpoint notices.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ConfigFilePaths:
    """Default configuration file paths to search for."""
    PRIMARY = "docs_endpoint_notices.json"
    KIRO_DIR = ".kiro/docs_endpoint_notices.json"
    GENERATOR_DIR = "core/docs_generator/endpoint_notices.json"
    
    @classmethod
    def all_paths(cls) -> List[str]:
        """Get all possible configuration file paths."""
        return [
            cls.PRIMARY,
            cls.KIRO_DIR,
            cls.GENERATOR_DIR
        ]


@dataclass
class NoticeTypes:
    """Available notice types."""
    INFO = "info"
    WARNING = "warning"
    IMPORTANT = "important"
    TIP = "tip"
    EXAMPLE = "example"
    PERFORMANCE = "performance"
    
    @classmethod
    def all_types(cls) -> List[str]:
        """Get all available notice types."""
        return [
            cls.INFO,
            cls.WARNING,
            cls.IMPORTANT,
            cls.TIP,
            cls.EXAMPLE,
            cls.PERFORMANCE
        ]


@dataclass
class NoticeIcons:
    """Icons for different notice types."""
    INFO = 'ℹ️'
    WARNING = '⚠️'
    IMPORTANT = '❗'
    TIP = '💡'
    EXAMPLE = '📝'
    PERFORMANCE = '⚡'
    DEFAULT = '📌'
    
    @classmethod
    def get_icon_map(cls) -> Dict[str, str]:
        """Get mapping of notice types to icons."""
        return {
            NoticeTypes.INFO: cls.INFO,
            NoticeTypes.WARNING: cls.WARNING,
            NoticeTypes.IMPORTANT: cls.IMPORTANT,
            NoticeTypes.TIP: cls.TIP,
            NoticeTypes.EXAMPLE: cls.EXAMPLE,
            NoticeTypes.PERFORMANCE: cls.PERFORMANCE
        }


@dataclass
class ErrorMessages:
    """Error messages for notice operations."""
    CONFIG_LOAD_FAILED = "Warning: Failed to load endpoint notices config: {error}"
    CONFIG_SAVE_FAILED = "Failed to save endpoint notices config: {error}"
    FILE_NOT_FOUND = "Configuration file not found: {path}"
    INVALID_JSON = "Invalid JSON in configuration file: {error}"


@dataclass
class InfoMessages:
    """Informational messages."""
    CONFIG_CREATED = "Создан пример конфигурации: {path}"
    CONFIG_LOADED = "Loaded endpoint notices from: {path}"


@dataclass
class ConfigKeys:
    """Keys used in configuration files."""
    ENDPOINT_NOTICES = "endpoint_notices"
    DESCRIPTION = "_description"
    FORMAT = "_format"
    AVAILABLE_TYPES = "_available_types"


@dataclass
class ExampleConfigTemplate:
    """Template for example configuration."""
    
    @classmethod
    def get_template(cls) -> Dict[str, Any]:
        """Get example configuration template."""
        return {
            ConfigKeys.ENDPOINT_NOTICES: {
                "POST /api/v1/private/n8n_ui/cards/save": {
                    NoticeTypes.WARNING: "⚠️ Этот эндпоинт может возвращать конфликты при сохранении. Обязательно обрабатывайте ответы с success: false.",
                    NoticeTypes.INFO: "💡 При конфликтах рекомендуется показать пользователю альтернативные варианты времени или преподавателей."
                },
                "POST /api/v1/private/n8n_ui/std_ttable/check_exists": {
                    NoticeTypes.IMPORTANT: "🔍 Этот эндпоинт выполняет сложную проверку актуальности данных. Время выполнения может достигать 5-10 секунд.",
                    NoticeTypes.INFO: "📊 Результат содержит детальную информацию о различиях в группах, преподавателях и дисциплинах."
                },
                "GET /api/v1/private/disciplines/get": {
                    NoticeTypes.INFO: "📚 Поддерживает пагинацию через параметры limit и offset.",
                    NoticeTypes.TIP: "💡 Для лучшей производительности рекомендуется использовать limit не более 100."
                }
            },
            ConfigKeys.DESCRIPTION: "Конфигурация дополнительных текстов для эндпоинтов API документации",
            ConfigKeys.FORMAT: "Ключ: 'METHOD /path', значение: объект с типами notices",
            ConfigKeys.AVAILABLE_TYPES: [
                "info - общая информация",
                "warning - предупреждения", 
                "important - важные замечания",
                "tip - советы по использованию",
                "example - дополнительные примеры",
                "performance - замечания по производительности"
            ]
        }


@dataclass
class MarkdownFormatting:
    """Markdown formatting templates."""
    NOTICE_TEMPLATE = "\n> **{icon} {type_name}:** {text}\n"