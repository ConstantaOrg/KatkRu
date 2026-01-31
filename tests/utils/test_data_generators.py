"""
Test Data Generators for API Testing

This module provides generators that create test data matching actual database
constraints and real API response patterns, ensuring tests use realistic data.
"""

from typing import Dict, List, Any, Optional, Generator, Union
from dataclasses import dataclass
import random
import string
from datetime import datetime, timedelta


@dataclass
class DatabaseConstraints:
    """Represents database constraints for generating realistic test data."""
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    nullable: bool = False


class TestDataGenerator:
    """Generates test data that matches actual database constraints."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducible tests."""
        if seed is not None:
            random.seed(seed)
    
    def generate_group_name(self, constraints: Optional[DatabaseConstraints] = None) -> str:
        """Generate realistic group name matching database constraints."""
        if constraints and constraints.allowed_values:
            return random.choice(constraints.allowed_values)
        
        # Generate realistic group names like "ИС-21-1", "ПИ-22-2", etc.
        prefixes = ["ИС", "ПИ", "ИВТ", "БИ", "КС", "ТС"]
        year = random.randint(20, 25)  # 2020-2025
        group_num = random.randint(1, 4)
        
        name = f"{random.choice(prefixes)}-{year}-{group_num}"
        
        if constraints and constraints.max_length:
            name = name[:constraints.max_length]
        
        return name
    
    def generate_teacher_name(self, constraints: Optional[DatabaseConstraints] = None) -> str:
        """Generate realistic teacher name."""
        first_names = ["Иван", "Петр", "Сергей", "Александр", "Дмитрий", "Андрей", "Михаил"]
        last_names = ["Иванов", "Петров", "Сидоров", "Козлов", "Волков", "Зайцев", "Соколов"]
        patronymics = ["Иванович", "Петрович", "Сергеевич", "Александрович", "Дмитриевич"]
        
        name = f"{random.choice(last_names)} {random.choice(first_names)} {random.choice(patronymics)}"
        
        if constraints and constraints.max_length:
            name = name[:constraints.max_length]
        
        return name
    
    def generate_discipline_name(self, constraints: Optional[DatabaseConstraints] = None) -> str:
        """Generate realistic discipline name."""
        disciplines = [
            "Математика",
            "Информатика",
            "Программирование",
            "Базы данных",
            "Веб-технологии",
            "Алгоритмы и структуры данных",
            "Операционные системы",
            "Сети и телекоммуникации",
            "Безопасность информационных систем",
            "Проектирование ИС"
        ]
        
        name = random.choice(disciplines)
        
        if constraints and constraints.max_length:
            name = name[:constraints.max_length]
        
        return name
    
    def generate_audience_number(self, constraints: Optional[DatabaseConstraints] = None) -> str:
        """Generate realistic audience number."""
        if constraints and constraints.allowed_values:
            return random.choice(constraints.allowed_values)
        
        # Generate realistic audience numbers like "101", "202А", "Лаб-1"
        formats = [
            lambda: f"{random.randint(100, 599)}",  # Regular rooms
            lambda: f"{random.randint(100, 599)}{random.choice(['А', 'Б', 'В'])}",  # Rooms with letters
            lambda: f"Лаб-{random.randint(1, 10)}",  # Lab rooms
            lambda: f"Акт.зал",  # Special rooms
            lambda: f"Спорт.зал"
        ]
        
        return random.choice(formats)()
    
    def generate_id(self, min_id: int = 1, max_id: int = 1000000) -> int:
        """Generate realistic database ID."""
        return random.randint(min_id, max_id)
    
    def generate_boolean(self, true_probability: float = 0.5) -> bool:
        """Generate boolean with specified probability of True."""
        return random.random() < true_probability
    
    def generate_timestamp(self, days_back: int = 30) -> str:
        """Generate realistic timestamp."""
        base_time = datetime.now() - timedelta(days=random.randint(0, days_back))
        return base_time.isoformat()


class ResponseDataGenerator:
    """Generates complete response data structures matching API patterns."""
    
    def __init__(self, data_generator: Optional[TestDataGenerator] = None):
        self.data_gen = data_generator or TestDataGenerator()
    
    def generate_groups_response(self, count: int = 5, include_pagination: bool = False) -> Dict[str, Any]:
        """Generate realistic groups response."""
        groups = []
        for _ in range(count):
            group = {
                "id": self.data_gen.generate_id(),
                "name": self.data_gen.generate_group_name(),
                "specialty_id": self.data_gen.generate_id(1, 100),
                "course": random.randint(1, 4),
                "active": self.data_gen.generate_boolean(0.9)  # Most groups are active
            }
            groups.append(group)
        
        response = {"groups": groups}
        
        if include_pagination:
            response["pagination"] = {
                "total": count + random.randint(0, 50),
                "page": 1,
                "per_page": count,
                "pages": random.randint(1, 5)
            }
        
        return response
    
    def generate_teachers_response(self, count: int = 5) -> Dict[str, Any]:
        """Generate realistic teachers response."""
        teachers = []
        for _ in range(count):
            teacher = {
                "id": self.data_gen.generate_id(),
                "name": self.data_gen.generate_teacher_name(),
                "department_id": self.data_gen.generate_id(1, 20),
                "active": self.data_gen.generate_boolean(0.95)
            }
            teachers.append(teacher)
        
        return {"teachers": teachers}
    
    def generate_disciplines_response(self, count: int = 5) -> Dict[str, Any]:
        """Generate realistic disciplines response."""
        disciplines = []
        for _ in range(count):
            discipline = {
                "id": self.data_gen.generate_id(),
                "name": self.data_gen.generate_discipline_name(),
                "short_name": self.data_gen.generate_discipline_name()[:10],
                "active": self.data_gen.generate_boolean(0.9)
            }
            disciplines.append(discipline)
        
        return {"disciplines": disciplines}
    
    def generate_timetable_response(self, include_lessons: bool = True) -> Dict[str, Any]:
        """Generate realistic timetable response."""
        if not include_lessons:
            return {"timetable": {}}
        
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        timetable = {}
        
        for day in random.sample(days, random.randint(3, 6)):  # 3-6 days with lessons
            lessons = []
            for position in range(1, random.randint(3, 7)):  # 1-6 lessons per day
                lesson = {
                    "position": position,
                    "discipline": self.data_gen.generate_discipline_name(),
                    "teacher": self.data_gen.generate_teacher_name(),
                    "audience": self.data_gen.generate_audience_number(),
                    "type": random.choice(["Лекция", "Практика", "Лабораторная"])
                }
                lessons.append(lesson)
            
            timetable[day] = lessons
        
        return {"timetable": timetable}
    
    def generate_cards_save_success_response(self) -> Dict[str, Any]:
        """Generate successful cards save response."""
        return {
            "success": True,
            "new_card_hist_id": self.data_gen.generate_id()
        }
    
    def generate_cards_save_conflict_response(self) -> Dict[str, Any]:
        """Generate cards save conflict response."""
        return {
            "success": False,
            "conflicts": {
                "position_conflicts": [
                    {
                        "position": random.randint(1, 6),
                        "existing_lesson": {
                            "discipline": self.data_gen.generate_discipline_name(),
                            "teacher": self.data_gen.generate_teacher_name()
                        }
                    }
                ]
            }
        }
    
    def generate_n8n_diff_response(self, has_differences: bool = True) -> Dict[str, Any]:
        """Generate N8N UI diff response."""
        if not has_differences:
            return {"differences": []}
        
        differences = []
        for _ in range(random.randint(1, 5)):
            diff = {
                "type": random.choice(["added", "removed", "modified"]),
                "group_name": self.data_gen.generate_group_name(),
                "position": random.randint(1, 6),
                "discipline": self.data_gen.generate_discipline_name(),
                "teacher": self.data_gen.generate_teacher_name(),
                "audience": self.data_gen.generate_audience_number()
            }
            differences.append(diff)
        
        return {"differences": differences}


class OverloadResponseGenerator:
    """
    Generator for @overload response model scenarios.
    
    This generator creates responses that match the clean @overload pattern
    without null field pollution.
    """
    
    def __init__(self, data_generator: Optional[TestDataGenerator] = None):
        self.data_gen = data_generator or TestDataGenerator()
    
    def generate_success_response(self, response_type: str, **kwargs) -> Dict[str, Any]:
        """Generate clean success response without null fields."""
        base_response = {"success": True}
        
        if response_type == "cards_save":
            base_response["new_card_hist_id"] = kwargs.get("card_id", self.data_gen.generate_id())
        elif response_type == "ttable_commit":
            base_response["commit_id"] = kwargs.get("commit_id", self.data_gen.generate_id())
        elif response_type == "data_operation":
            base_response["affected_rows"] = kwargs.get("affected_rows", random.randint(1, 10))
        
        return base_response
    
    def generate_conflict_response(self, response_type: str, **kwargs) -> Dict[str, Any]:
        """Generate clean conflict response without null fields."""
        base_response = {"success": False}
        
        if response_type == "cards_save":
            base_response["conflicts"] = kwargs.get("conflicts", {
                "position_conflicts": [{"position": 1, "reason": "Occupied"}]
            })
        elif response_type == "ttable_commit":
            base_response["conflicts"] = kwargs.get("conflicts", {
                "version_conflicts": ["Outdated version"]
            })
        elif response_type == "data_operation":
            base_response["error"] = kwargs.get("error", "Constraint violation")
        
        return base_response
    
    def generate_error_response(self, response_type: str, **kwargs) -> Dict[str, Any]:
        """Generate clean error response without null fields."""
        error_messages = [
            "Invalid input data",
            "Resource not found",
            "Permission denied",
            "Database connection error",
            "Validation failed"
        ]
        
        return {
            "success": False,
            "error": kwargs.get("error", random.choice(error_messages)),
            "error_code": kwargs.get("error_code", random.randint(1000, 9999))
        }
    
    def validate_clean_json(self, response: Dict[str, Any]) -> bool:
        """
        Validate that response contains no null fields (clean @overload pattern).
        
        Returns True if response is clean (no null values).
        """
        def has_null_values(obj):
            if isinstance(obj, dict):
                return any(v is None or has_null_values(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(has_null_values(item) for item in obj)
            return obj is None
        
        return not has_null_values(response)


# Convenience functions for common scenarios
def create_realistic_groups_data(count: int = 5) -> Dict[str, Any]:
    """Create realistic groups response data."""
    generator = ResponseDataGenerator()
    return generator.generate_groups_response(count)


def create_realistic_teachers_data(count: int = 5) -> Dict[str, Any]:
    """Create realistic teachers response data."""
    generator = ResponseDataGenerator()
    return generator.generate_teachers_response(count)


def create_realistic_timetable_data(has_lessons: bool = True) -> Dict[str, Any]:
    """Create realistic timetable response data."""
    generator = ResponseDataGenerator()
    return generator.generate_timetable_response(has_lessons)


def create_overload_success_response(response_type: str, **kwargs) -> Dict[str, Any]:
    """Create clean @overload success response."""
    generator = OverloadResponseGenerator()
    return generator.generate_success_response(response_type, **kwargs)


def create_overload_conflict_response(response_type: str, **kwargs) -> Dict[str, Any]:
    """Create clean @overload conflict response."""
    generator = OverloadResponseGenerator()
    return generator.generate_conflict_response(response_type, **kwargs)