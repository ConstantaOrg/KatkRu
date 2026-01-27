"""
Анализатор API endpoints для создания response схем.
Помогает понять структуру ответов и предлагает схемы.
"""

import ast
import inspect
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

class EndpointAnalyzer:
    """Анализирует endpoints и предлагает response схемы."""
    
    def __init__(self):
        self.api_dir = Path("core/api")
        self.endpoints = []
    
    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Анализирует один API файл."""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Ищем декораторы router
                    for decorator in node.decorator_list:
                        if self._is_router_decorator(decorator):
                            endpoint_info = self._extract_endpoint_info(node, decorator, content)
                            if endpoint_info:
                                endpoints.append(endpoint_info)
        
        except Exception as e:
            print(f"Ошибка анализа {file_path}: {e}")
        
        return endpoints
    
    def _is_router_decorator(self, decorator) -> bool:
        """Проверяет, является ли декоратор router методом."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']
        return False
    
    def _extract_endpoint_info(self, func_node, decorator, content: str) -> Optional[Dict[str, Any]]:
        """Извлекает информацию об endpoint."""
        try:
            # Получаем HTTP метод
            method = decorator.func.attr.upper()
            
            # Получаем путь
            path = None
            if decorator.args:
                if isinstance(decorator.args[0], ast.Constant):
                    path = decorator.args[0].value
            
            # Получаем имя функции
            func_name = func_node.name
            
            # Анализируем return statements
            return_examples = self._extract_return_statements(func_node, content)
            
            return {
                'method': method,
                'path': path,
                'function_name': func_name,
                'return_examples': return_examples,
                'line_number': func_node.lineno
            }
        
        except Exception:
            return None
    
    def _extract_return_statements(self, func_node, content: str) -> List[str]:
        """Извлекает примеры return statements."""
        returns = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value:
                # Получаем строку с return
                lines = content.split('\n')
                if node.lineno <= len(lines):
                    return_line = lines[node.lineno - 1].strip()
                    returns.append(return_line)
        
        return returns
    
    def analyze_all_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Анализирует все API файлы."""
        results = {}
        
        # Анализируем файлы в корне api/
        for file_path in self.api_dir.glob("*.py"):
            if file_path.name not in ['__init__.py', 'middleware.py']:
                endpoints = self.analyze_file(file_path)
                if endpoints:
                    results[file_path.name] = endpoints
        
        # Анализируем подпапки
        for subdir in self.api_dir.iterdir():
            if subdir.is_dir() and subdir.name not in ['__pycache__', 'one_time_scripts']:
                for file_path in subdir.glob("*.py"):
                    if file_path.name != '__init__.py':
                        endpoints = self.analyze_file(file_path)
                        if endpoints:
                            key = f"{subdir.name}/{file_path.name}"
                            results[key] = endpoints
        
        return results
    
    def suggest_response_schema(self, endpoint: Dict[str, Any]) -> str:
        """Предлагает response схему для endpoint."""
        method = endpoint['method']
        func_name = endpoint['function_name']
        returns = endpoint['return_examples']
        
        # Анализируем return statements
        schema_suggestions = []
        
        for return_stmt in returns:
            if 'success' in return_stmt and 'message' in return_stmt:
                schema_suggestions.append("SuccessResponse")
            elif 'groups' in return_stmt:
                schema_suggestions.append("GroupsResponse")
            elif 'specialties' in return_stmt:
                schema_suggestions.append("SpecialtiesResponse")
            elif 'users' in return_stmt:
                schema_suggestions.append("UsersResponse")
            elif method == 'POST' and 'id' in return_stmt:
                schema_suggestions.append("SuccessWithIdResponse")
        
        # Генерируем имя схемы
        class_name = self._generate_schema_name(func_name, method)
        
        return f"""
class {class_name}(BaseModel):
    # Анализ return statements: {returns}
    # Предлагаемые базовые классы: {schema_suggestions}
    pass  # TODO: Определить поля
"""
    
    def _generate_schema_name(self, func_name: str, method: str) -> str:
        """Генерирует имя для response схемы."""
        # Убираем префиксы
        name = func_name.replace('get_', '').replace('add_', '').replace('update_', '').replace('delete_', '')
        
        # Преобразуем в CamelCase
        parts = name.split('_')
        camel_name = ''.join(word.capitalize() for word in parts)
        
        # Добавляем метод если нужно
        if method in ['POST', 'PUT', 'DELETE']:
            camel_name += method.capitalize()
        
        return f"{camel_name}Response"
    
    def generate_report(self) -> str:
        """Генерирует отчет по всем endpoints."""
        results = self.analyze_all_files()
        
        report = "# Анализ API Endpoints для создания Response схем\n\n"
        
        for file_name, endpoints in results.items():
            report += f"## {file_name}\n\n"
            
            for endpoint in endpoints:
                report += f"### {endpoint['method']} {endpoint['path']} - {endpoint['function_name']}\n"
                report += f"**Строка:** {endpoint['line_number']}\n\n"
                
                if endpoint['return_examples']:
                    report += "**Return statements:**\n"
                    for ret in endpoint['return_examples']:
                        report += f"- `{ret}`\n"
                    report += "\n"
                
                # Предлагаем схему
                schema = self.suggest_response_schema(endpoint)
                report += f"**Предлагаемая схема:**\n```python{schema}```\n\n"
                report += "---\n\n"
        
        return report


if __name__ == "__main__":
    analyzer = EndpointAnalyzer()
    report = analyzer.generate_report()
    
    # Сохраняем отчет
    with open("response_schemas_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("Анализ завершен! Отчет сохранен в response_schemas_analysis.md")
    print(f"Найдено файлов: {len(analyzer.analyze_all_files())}")