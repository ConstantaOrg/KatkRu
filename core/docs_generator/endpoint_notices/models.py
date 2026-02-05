"""
Models for endpoint notices.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class NoticeConfig:
    """Configuration for endpoint notices."""
    endpoint_notices: Dict[str, Dict[str, str]]
    description: str = "Конфигурация дополнительных текстов для эндпоинтов API документации"
    format_info: str = "Ключ: 'METHOD /path', значение: объект с типами notices"
    available_types: List[str] = None
    
    def __post_init__(self):
        """Initialize default available types."""
        if self.available_types is None:
            self.available_types = [
                "info - общая информация",
                "warning - предупреждения", 
                "important - важные замечания",
                "tip - советы по использованию",
                "example - дополнительные примеры",
                "performance - замечания по производительности"
            ]


@dataclass
class EndpointNotice:
    """Represents a notice for a specific endpoint."""
    method: str
    path: str
    notice_type: str
    text: str
    
    @property
    def endpoint_key(self) -> str:
        """Get the endpoint key for this notice."""
        return f"{self.method.upper()} {self.path}"


@dataclass
class NoticeFormatting:
    """Configuration for notice formatting in documentation."""
    type_icons: Dict[str, str]
    markdown_template: str = "\n> **{icon} {type_name}:** {text}\n"
    
    def __post_init__(self):
        """Initialize default type icons if not provided."""
        if not hasattr(self, 'type_icons') or not self.type_icons:
            self.type_icons = {
                'info': 'ℹ️',
                'warning': '⚠️', 
                'important': '❗',
                'tip': '💡',
                'example': '📝',
                'performance': '⚡'
            }