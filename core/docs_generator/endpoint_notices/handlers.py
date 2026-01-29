"""
Handler functions for endpoint notices.
"""

import json
import os
from typing import Dict, Optional, List
from pathlib import Path

from .models import NoticeConfig, EndpointNotice, NoticeFormatting
from .constants import (
    ConfigFilePaths, NoticeTypes, NoticeIcons, ErrorMessages, 
    InfoMessages, ConfigKeys, ExampleConfigTemplate, MarkdownFormatting
)


def find_config_file() -> Optional[str]:
    """Find configuration file in standard locations."""
    for path in ConfigFilePaths.all_paths():
        if os.path.exists(path):
            return path
    return None


def load_config_from_file(config_path: str) -> Dict[str, Dict[str, str]]:
    """Load configuration from file."""
    if not config_path or not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(ConfigKeys.ENDPOINT_NOTICES, {})
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(ErrorMessages.CONFIG_LOAD_FAILED.format(error=e))
        return {}


def get_notice_for_endpoint(notices: Dict[str, Dict[str, str]], method: str, path: str) -> Optional[Dict[str, str]]:
    """
    Get notice for endpoint.
    
    Args:
        notices: Dictionary of all notices
        method: HTTP method (GET, POST, etc.)
        path: Endpoint path
        
    Returns:
        Dictionary with notice texts or None if not found
    """
    endpoint_key = f"{method.upper()} {path}"
    return notices.get(endpoint_key)


def add_notice_to_config(notices: Dict[str, Dict[str, str]], method: str, path: str, 
                        notice_type: str, text: str) -> Dict[str, Dict[str, str]]:
    """
    Add notice for endpoint.
    
    Args:
        notices: Current notices dictionary
        method: HTTP method
        path: Endpoint path
        notice_type: Type of notice (warning, info, important, etc.)
        text: Notice text
        
    Returns:
        Updated notices dictionary
    """
    endpoint_key = f"{method.upper()} {path}"
    if endpoint_key not in notices:
        notices[endpoint_key] = {}
    notices[endpoint_key][notice_type] = text
    return notices


def save_config_to_file(notices: Dict[str, Dict[str, str]], output_path: str):
    """
    Save configuration to file.
    
    Args:
        notices: Notices dictionary to save
        output_path: Path to save configuration
    """
    config_data = {
        ConfigKeys.ENDPOINT_NOTICES: notices,
        ConfigKeys.DESCRIPTION: "Конфигурация дополнительных текстов для эндпоинтов API документации",
        ConfigKeys.FORMAT: "Ключ: 'METHOD /path', значение: объект с типами notices"
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(ErrorMessages.CONFIG_SAVE_FAILED.format(error=e))


def create_example_config_file(output_path: str = ConfigFilePaths.PRIMARY):
    """Create example configuration file."""
    example_config = ExampleConfigTemplate.get_template()
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        
        print(InfoMessages.CONFIG_CREATED.format(path=output_path))
    except Exception as e:
        raise RuntimeError(ErrorMessages.CONFIG_SAVE_FAILED.format(error=e))


def format_notice_for_markdown(notice_type: str, text: str) -> str:
    """
    Format notice for insertion into Markdown documentation.
    
    Args:
        notice_type: Type of notice
        text: Notice text
        
    Returns:
        Formatted Markdown text
    """
    type_icons = NoticeIcons.get_icon_map()
    icon = type_icons.get(notice_type, NoticeIcons.DEFAULT)
    type_name = notice_type.upper()
    
    return MarkdownFormatting.NOTICE_TEMPLATE.format(
        icon=icon,
        type_name=type_name,
        text=text
    )


def validate_notice_type(notice_type: str) -> bool:
    """Validate if notice type is supported."""
    return notice_type in NoticeTypes.all_types()


def get_available_notice_types() -> List[str]:
    """Get list of all available notice types."""
    return NoticeTypes.all_types()


def create_endpoint_key(method: str, path: str) -> str:
    """Create standardized endpoint key."""
    return f"{method.upper()} {path}"