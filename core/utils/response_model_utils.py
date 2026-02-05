"""
Response Model Utilities

Utility functions for creating clean @overload response models
without inheritance-based field pollution.
"""

from typing import overload, Union, Literal, List, Dict, Any, Type, Optional, Tuple
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

from .overload_response_framework import ResponseModelFramework


# Cards Save Response Models
class CardsSaveSuccessResponse(BaseModel):
    """Clean success response for cards/save endpoint."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Card saved successfully", description="Success message")
    new_card_hist_id: int = Field(..., description="ID of the new card history record")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Card saved successfully",
                "new_card_hist_id": 150
            }
        }


class CardsSaveConflictResponse(BaseModel):
    """Clean conflict response for cards/save endpoint."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Conflicts detected during save", description="Error message")
    conflicts: Dict[str, Any] = Field(..., description="Conflict information")
    description: str = Field(..., description="Detailed conflict description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Conflicts detected during save",
                "conflicts": {
                    "columns": ["position", "teacher_id", "sched_ver_id"],
                    "values": [1, 1, 2]
                },
                "description": "This teacher already has a group at this time slot"
            }
        }


# Union type for cards/save
CardsSaveResponse = Union[CardsSaveSuccessResponse, CardsSaveConflictResponse]


# @overload functions for cards/save
@overload
def create_cards_save_response(
    success: Literal[True],
    new_card_hist_id: int,
    message: str = "Card saved successfully"
) -> CardsSaveSuccessResponse: ...


@overload
def create_cards_save_response(
    success: Literal[False],
    conflicts: Dict[str, Any],
    description: str,
    message: str = "Conflicts detected during save"
) -> CardsSaveConflictResponse: ...


def create_cards_save_response(
    success: bool,
    new_card_hist_id: int = None,
    conflicts: Dict[str, Any] = None,
    description: str = None,
    message: str = None
) -> CardsSaveResponse:
    """
    Create a type-safe response for cards/save endpoint.
    
    Args:
        success: Whether the operation was successful
        new_card_hist_id: ID of new card history record (success only)
        conflicts: Conflict information (failure only)
        description: Detailed conflict description (failure only)
        message: Custom message (optional)
        
    Returns:
        Appropriate response model instance
    """
    if success:
        return CardsSaveSuccessResponse(
            new_card_hist_id=new_card_hist_id,
            message=message or "Card saved successfully"
        )
    else:
        return CardsSaveConflictResponse(
            conflicts=conflicts,
            description=description,
            message=message or "Conflicts detected during save"
        )


# Ttable Versions PreCommit Response Models
class TtableVersionsPreCommitSuccessResponse(BaseModel):
    """Clean success response for ttable versions pre-commit."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Timetable version ready for commit", description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Timetable version ready for commit"
            }
        }


class TtableVersionsPreCommitConflictResponse(BaseModel):
    """Clean conflict response for ttable versions pre-commit."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Conflicts detected in timetable version", description="Error message")
    needed_groups: List[int] = Field(default_factory=list, description="List of group IDs that need to be included")
    ttable_id: int = Field(..., description="ID of the timetable version")
    # Optional fields for 202 case (existing active version)
    cur_active_ver: Optional[int] = Field(None, description="ID of currently active version (202 case)")
    pending_ver_id: Optional[int] = Field(None, description="ID of pending version (202 case)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Insufficient groups in timetable",
                "needed_groups": ["ИС-21-1", "ПР-21-2"],
                "ttable_id": 42
            }
        }


# Union type for ttable versions pre-commit
TtableVersionsPreCommitResponse = Union[
    TtableVersionsPreCommitSuccessResponse,
    TtableVersionsPreCommitConflictResponse
]


# @overload functions for ttable versions pre-commit
@overload
def create_ttable_precommit_response(
    success: Literal[True],
    message: str = "Timetable version ready for commit"
) -> TtableVersionsPreCommitSuccessResponse: ...


@overload
def create_ttable_precommit_response(
    success: Literal[False],
    needed_groups: List[int] = None,
    ttable_id: int = None,
    message: str = "Conflicts detected in timetable version",
    cur_active_ver: int = None,
    pending_ver_id: int = None
) -> TtableVersionsPreCommitConflictResponse: ...


def create_ttable_precommit_response(
    success: bool,
    needed_groups: List[str] | Tuple[str]= None,
    ttable_id: int = None,
    message: str = None,
    cur_active_ver: int = None,
    pending_ver_id: int = None
) -> TtableVersionsPreCommitResponse:
    """
    Create a type-safe response for ttable versions pre-commit endpoint.
    
    Args:
        success: Whether the operation was successful
        needed_groups: List of groups needed (failure only)
        ttable_id: Timetable version ID (failure only)
        message: Custom message (optional)
        cur_active_ver: Currently active version ID (202 case only)
        pending_ver_id: Pending version ID (202 case only)
        
    Returns:
        Appropriate response model instance
    """
    if success:
        return TtableVersionsPreCommitSuccessResponse(
            message=message or "Timetable version ready for commit"
        )
    else:
        return TtableVersionsPreCommitConflictResponse(
            needed_groups=needed_groups or [],
            ttable_id=ttable_id,
            message=message or "Conflicts detected in timetable version",
            cur_active_ver=cur_active_ver,
            pending_ver_id=pending_ver_id
        )


# Utility function to create JSON responses
def create_response_json(
    model_instance: BaseModel,
    status_code: int = 200
) -> JSONResponse:
    """
    Create a JSONResponse from a clean response model instance.
    
    Args:
        model_instance: Pydantic model instance
        status_code: HTTP status code
        
    Returns:
        FastAPI JSONResponse with clean JSON (no null fields)
    """
    return JSONResponse(
        status_code=status_code,
        content=model_instance.model_dump(exclude_none=True)
    )


# Generic @overload pattern for future endpoints
def create_generic_success_error_models(
    base_name: str,
    success_fields: Dict[str, Any] = None,
    error_fields: Dict[str, Any] = None
) -> tuple[Type[BaseModel], Type[BaseModel], Type]:
    """
    Create generic success/error response models for any endpoint.
    
    Args:
        base_name: Base name for the response models (e.g., "UserLogin")
        success_fields: Additional fields for success response
        error_fields: Additional fields for error response
        
    Returns:
        Tuple of (SuccessModel, ErrorModel, UnionType)
    """
    from .overload_response_framework import create_binary_response_models
    
    return create_binary_response_models(
        base_name=base_name,
        success_fields=success_fields,
        error_fields=error_fields
    )


# User Registration Response Models
class UserRegistrationSuccessResponse(BaseModel):
    """Clean success response for user registration."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Пользователь добавлен", description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Пользователь добавлен"
            }
        }


class UserRegistrationConflictResponse(BaseModel):
    """Clean conflict response for user registration."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Пользователь уже существует", description="Error message")
    detail: str = Field("Пользователь уже существует", description="Detailed error description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Пользователь уже существует",
                "detail": "Пользователь уже существует"
            }
        }


# Union type for user registration
UserRegistrationResponse = Union[UserRegistrationSuccessResponse, UserRegistrationConflictResponse]


# User Login Response Models
class UserLoginSuccessResponse(BaseModel):
    """Clean success response for user login."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Куки у Юзера", description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Куки у Юзера"
            }
        }


class UserLoginUnauthorizedResponse(BaseModel):
    """Clean unauthorized response for user login."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Неверный логин или пароль", description="Error message")
    detail: str = Field("Неверный логин или пароль. Если вы входили через Google/Github и т.п. Пройдите регистрацию, чтобы установить пароль", description="Detailed error description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Неверный логин или пароль",
                "detail": "Неверный логин или пароль. Если вы входили через Google/Github и т.п. Пройдите регистрацию, чтобы установить пароль"
            }
        }


# Union type for user login
UserLoginResponse = Union[UserLoginSuccessResponse, UserLoginUnauthorizedResponse]


# @overload functions for user registration
@overload
def create_user_registration_response(
    success: Literal[True],
    message: str = "Пользователь добавлен"
) -> UserRegistrationSuccessResponse: ...


@overload
def create_user_registration_response(
    success: Literal[False],
    message: str = "Пользователь уже существует",
    detail: str = "Пользователь уже существует"
) -> UserRegistrationConflictResponse: ...


def create_user_registration_response(
    success: bool,
    message: str = None,
    detail: str = None
) -> UserRegistrationResponse:
    """
    Create a type-safe response for user registration endpoint.
    
    Args:
        success: Whether the registration was successful
        message: Custom message (optional)
        detail: Detailed error description (failure only)
        
    Returns:
        Appropriate response model instance
    """
    if success:
        return UserRegistrationSuccessResponse(
            message=message or "Пользователь добавлен"
        )
    else:
        return UserRegistrationConflictResponse(
            message=message or "Пользователь уже существует",
            detail=detail or "Пользователь уже существует"
        )


# @overload functions for user login
@overload
def create_user_login_response(
    success: Literal[True],
    message: str = "Куки у Юзера"
) -> UserLoginSuccessResponse: ...


@overload
def create_user_login_response(
    success: Literal[False],
    message: str = "Неверный логин или пароль",
    detail: str = "Неверный логин или пароль. Если вы входили через Google/Github и т.п. Пройдите регистрацию, чтобы установить пароль"
) -> UserLoginUnauthorizedResponse: ...


def create_user_login_response(
    success: bool,
    message: str = None,
    detail: str = None
) -> UserLoginResponse:
    """
    Create a type-safe response for user login endpoint.
    
    Args:
        success: Whether the login was successful
        message: Custom message (optional)
        detail: Detailed error description (failure only)
        
    Returns:
        Appropriate response model instance
    """
    if success:
        return UserLoginSuccessResponse(
            message=message or "Куки у Юзера"
        )
    else:
        return UserLoginUnauthorizedResponse(
            message=message or "Неверный логин или пароль",
            detail=detail or "Неверный логин или пароль. Если вы входили через Google/Github и т.п. Пройдите регистрацию, чтобы установить пароль"
        )


# FastAPI responses configuration helpers for user endpoints
def get_user_registration_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for user registration endpoint."""
    return {
        200: {
            "model": UserRegistrationSuccessResponse,
            "description": "User registered successfully"
        },
        409: {
            "model": UserRegistrationConflictResponse,
            "description": "User already exists"
        }
    }


# Groups Add Response Models
class GroupsAddSuccessResponse(BaseModel):
    """Clean success response for groups add endpoint."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Группа добавлена", description="Success message")
    group_id: int = Field(..., description="ID of the new group")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Группа добавлена",
                "group_id": 123
            }
        }


class GroupsAddConflictResponse(BaseModel):
    """Clean conflict response for groups add endpoint."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Группа с таким названием в этом здании уже существует", description="Error message")
    detail: str = Field("Группа с таким названием в этом здании уже существует", description="Detailed error description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Группа с таким названием в этом здании уже существует",
                "detail": "Группа с таким названием в этом здании уже существует"
            }
        }


# Union type for groups add
GroupsAddResponse = Union[GroupsAddSuccessResponse, GroupsAddConflictResponse]


# Teachers Add Response Models
class TeachersAddSuccessResponse(BaseModel):
    """Clean success response for teachers add endpoint."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Учитель добавлен", description="Success message")
    teacher_id: int = Field(..., description="ID of the new teacher")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Учитель добавлен",
                "teacher_id": 456
            }
        }


class TeachersAddConflictResponse(BaseModel):
    """Clean conflict response for teachers add endpoint."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Такой учитель уже добавлен", description="Error message")
    detail: str = Field("Такой учитель уже добавлен", description="Detailed error description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Такой учитель уже добавлен",
                "detail": "Такой учитель уже добавлен"
            }
        }


# Union type for teachers add
TeachersAddResponse = Union[TeachersAddSuccessResponse, TeachersAddConflictResponse]


# Disciplines Add Response Models
class DisciplinesAddSuccessResponse(BaseModel):
    """Clean success response for disciplines add endpoint."""
    success: Literal[True] = Field(True, description="Success flag")
    message: str = Field("Дисциплина добавлена", description="Success message")
    discipline_id: int = Field(..., description="ID of the new discipline")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Дисциплина добавлена",
                "discipline_id": 789
            }
        }


class DisciplinesAddConflictResponse(BaseModel):
    """Clean conflict response for disciplines add endpoint."""
    success: Literal[False] = Field(False, description="Success flag")
    message: str = Field("Такой предмет уже есть", description="Error message")
    detail: str = Field("Такой предмет уже есть", description="Detailed error description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Такой предмет уже есть",
                "detail": "Такой предмет уже есть"
            }
        }


# Union type for disciplines add
DisciplinesAddResponse = Union[DisciplinesAddSuccessResponse, DisciplinesAddConflictResponse]


# @overload functions for groups add
@overload
def create_groups_add_response(
    success: Literal[True],
    group_id: int,
    message: str = "Группа добавлена"
) -> GroupsAddSuccessResponse: ...


@overload
def create_groups_add_response(
    success: Literal[False],
    message: str = "Группа с таким названием в этом здании уже существует",
    detail: str = "Группа с таким названием в этом здании уже существует"
) -> GroupsAddConflictResponse: ...


def create_groups_add_response(
    success: bool,
    group_id: int = None,
    message: str = None,
    detail: str = None
) -> GroupsAddResponse:
    """Create a type-safe response for groups add endpoint."""
    if success:
        return GroupsAddSuccessResponse(
            group_id=group_id,
            message=message or "Группа добавлена"
        )
    else:
        return GroupsAddConflictResponse(
            message=message or "Группа с таким названием в этом здании уже существует",
            detail=detail or "Группа с таким названием в этом здании уже существует"
        )


# @overload functions for teachers add
@overload
def create_teachers_add_response(
    success: Literal[True],
    teacher_id: int,
    message: str = "Учитель добавлен"
) -> TeachersAddSuccessResponse: ...


@overload
def create_teachers_add_response(
    success: Literal[False],
    message: str = "Такой учитель уже добавлен",
    detail: str = "Такой учитель уже добавлен"
) -> TeachersAddConflictResponse: ...


def create_teachers_add_response(
    success: bool,
    teacher_id: int = None,
    message: str = None,
    detail: str = None
) -> TeachersAddResponse:
    """Create a type-safe response for teachers add endpoint."""
    if success:
        return TeachersAddSuccessResponse(
            teacher_id=teacher_id,
            message=message or "Учитель добавлен"
        )
    else:
        return TeachersAddConflictResponse(
            message=message or "Такой учитель уже добавлен",
            detail=detail or "Такой учитель уже добавлен"
        )


# @overload functions for disciplines add
@overload
def create_disciplines_add_response(
    success: Literal[True],
    discipline_id: int,
    message: str = "Дисциплина добавлена"
) -> DisciplinesAddSuccessResponse: ...


@overload
def create_disciplines_add_response(
    success: Literal[False],
    message: str = "Такой предмет уже есть",
    detail: str = "Такой предмет уже есть"
) -> DisciplinesAddConflictResponse: ...


def create_disciplines_add_response(
    success: bool,
    discipline_id: int = None,
    message: str = None,
    detail: str = None
) -> DisciplinesAddResponse:
    """Create a type-safe response for disciplines add endpoint."""
    if success:
        return DisciplinesAddSuccessResponse(
            discipline_id=discipline_id,
            message=message or "Дисциплина добавлена"
        )
    else:
        return DisciplinesAddConflictResponse(
            message=message or "Такой предмет уже есть",
            detail=detail or "Такой предмет уже есть"
        )


# FastAPI responses configuration helpers for user endpoints
def get_user_registration_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for user registration endpoint."""
    return {
        200: {
            "model": UserRegistrationSuccessResponse,
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Пользователь добавлен"
                    }
                }
            }
        },
        409: {
            "model": UserRegistrationConflictResponse,
            "description": "User already exists",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Пользователь уже существует",
                        "detail": "Пользователь уже существует"
                    }
                }
            }
        }
    }


def get_user_login_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for user login endpoint."""
    return {
        200: {
            "model": UserLoginSuccessResponse,
            "description": "User logged in successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Куки у Юзера"
                    }
                }
            }
        },
        401: {
            "model": UserLoginUnauthorizedResponse,
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Неверный логин или пароль",
                        "detail": "Неверный логин или пароль. Если вы входили через Google/Github и т.п. Пройдите регистрацию, чтобы установить пароль"
                    }
                }
            }
        }
    }


def get_groups_add_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for groups add endpoint."""
    return {
        200: {
            "model": GroupsAddSuccessResponse,
            "description": "Group added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Группа добавлена",
                        "group_id": 123
                    }
                }
            }
        },
        409: {
            "model": GroupsAddConflictResponse,
            "description": "Group already exists",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Группа с таким названием в этом здании уже существует",
                        "detail": "Группа с таким названием в этом здании уже существует"
                    }
                }
            }
        }
    }


def get_teachers_add_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for teachers add endpoint."""
    return {
        200: {
            "model": TeachersAddSuccessResponse,
            "description": "Teacher added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Учитель добавлен",
                        "teacher_id": 456
                    }
                }
            }
        },
        409: {
            "model": TeachersAddConflictResponse,
            "description": "Teacher already exists",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Такой учитель уже добавлен",
                        "detail": "Такой учитель уже добавлен"
                    }
                }
            }
        }
    }


def get_disciplines_add_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for disciplines add endpoint."""
    return {
        200: {
            "model": DisciplinesAddSuccessResponse,
            "description": "Discipline added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Дисциплина добавлена",
                        "discipline_id": 789
                    }
                }
            }
        },
        409: {
            "model": DisciplinesAddConflictResponse,
            "description": "Discipline already exists",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Такой предмет уже есть",
                        "detail": "Такой предмет уже есть"
                    }
                }
            }
        }
    }


def get_cards_save_responses_config() -> Dict[int, Dict[str, Any]]:
    """Get FastAPI responses configuration for cards/save endpoint."""
    return {
        200: {
            "model": CardsSaveSuccessResponse,
            "description": "Card saved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Card saved successfully",
                        "new_card_hist_id": 150
                    }
                }
            }
        },
        409: {
            "model": CardsSaveConflictResponse,
            "description": "Conflicts detected during save",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Conflicts detected during save",
                        "conflicts": {
                            "columns": ["position", "teacher_id", "sched_ver_id"],
                            "values": [1, 1, 2]
                        },
                        "description": "This teacher already has a group at this time slot"
                    }
                }
            }
        }
    }


def create_openapi_union_response_config(
    success_model: Type[BaseModel],
    error_model: Type[BaseModel],
    success_status: int = 200,
    error_status: int = 400,
    success_description: str = "Successful operation",
    error_description: str = "Operation failed",
    discriminator_field: str = "success"
) -> Dict[int, Dict[str, Any]]:
    """
    Create OpenAPI configuration for Union response types with discriminator.
    
    Args:
        success_model: Success response model
        error_model: Error response model  
        success_status: HTTP status code for success (default: 200)
        error_status: HTTP status code for error (default: 400)
        success_description: Description for success response
        error_description: Description for error response
        discriminator_field: Field name to use as discriminator (default: "success")
        
    Returns:
        FastAPI responses configuration dictionary with discriminator
    """
    config = {
        success_status: {
            "model": success_model,
            "description": success_description
        },
        error_status: {
            "model": error_model,
            "description": error_description
        }
    }
    
    # Add discriminator information if both models have the discriminator field
    if (hasattr(success_model, '__fields__') and discriminator_field in success_model.__fields__ and
        hasattr(error_model, '__fields__') and discriminator_field in error_model.__fields__):
        
        # Add discriminator to the Union schema
        union_schema = {
            "discriminator": {
                "propertyName": discriminator_field,
                "mapping": {
                    "true": f"#/components/schemas/{success_model.__name__}",
                    "false": f"#/components/schemas/{error_model.__name__}"
                }
            }
        }
        
        # Add the discriminator info to both response configs
        for status_config in config.values():
            if "content" not in status_config:
                status_config["content"] = {"application/json": {}}
            if "schema" not in status_config["content"]["application/json"]:
                status_config["content"]["application/json"]["schema"] = {}
            
            status_config["content"]["application/json"]["schema"].update(union_schema)
    
    return config


def create_openapi_examples_for_union_responses(
    responses_config: Dict[int, Dict[str, Any]],
    examples: Dict[int, Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """
    Add OpenAPI examples to Union response configurations.
    
    Args:
        responses_config: Base responses configuration
        examples: Dictionary mapping status codes to example data
        
    Returns:
        Updated responses configuration with examples
    """
    updated_config = responses_config.copy()
    
    for status_code, example_data in examples.items():
        if status_code in updated_config:
            if "content" not in updated_config[status_code]:
                updated_config[status_code]["content"] = {"application/json": {}}
            
            updated_config[status_code]["content"]["application/json"]["example"] = example_data
    
    return updated_config
    """Get FastAPI responses configuration for ttable pre-commit endpoint."""
    return {
        200: {
            "model": TtableVersionsPreCommitSuccessResponse,
            "description": "Timetable version ready for commit",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Timetable version ready for commit"
                    }
                }
            }
        },
        409: {
            "model": TtableVersionsPreCommitConflictResponse,
            "description": "Conflicts detected in timetable version",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Insufficient groups in timetable",
                        "needed_groups": ["ИС-21-1", "ПР-21-2"],
                        "ttable_id": 42
                    }
                }
            }
        }
    }