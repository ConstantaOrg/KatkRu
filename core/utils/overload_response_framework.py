"""
@overload Response Model Framework

This module provides utilities for creating clean, type-safe response models
without inheritance-based field pollution. It implements the @overload pattern
for FastAPI endpoints that can return different response structures.

Key benefits:
- No null fields in JSON responses
- Precise type safety with @overload functions
- Clean separation of response scenarios
- Proper OpenAPI documentation generation
"""

from typing import overload, Union, Literal, TypeVar, Generic, Type, Dict, Any
from pydantic import BaseModel, Field
from fastapi import Response
from fastapi.responses import JSONResponse


# Type variables for generic response creation
T = TypeVar('T', bound=BaseModel)
ResponseType = TypeVar('ResponseType', bound=BaseModel)


class ResponseModelFramework:
    """
    Framework for creating @overload response models without inheritance pollution.
    
    This class provides utilities for:
    1. Creating clean response models without base class field pollution
    2. Type-safe response generation with @overload functions
    3. Proper FastAPI Union response type configuration
    """
    
    @staticmethod
    def create_clean_response_model(
        name: str,
        fields: Dict[str, Any],
        description: str = None,
        example: Dict[str, Any] = None
    ) -> Type[BaseModel]:
        """
        Create a clean response model without inheritance.
        
        Args:
            name: Name of the response model class
            fields: Dictionary of field definitions
            description: Optional model description
            example: Optional example for OpenAPI documentation
            
        Returns:
            Clean Pydantic model class without inherited fields
        """
        from pydantic import ConfigDict, create_model
        
        # Prepare field definitions for create_model
        field_definitions = {}
        
        # Process fields into the format expected by create_model
        for field_name, field_def in fields.items():
            if isinstance(field_def, tuple):
                field_type, field_info = field_def
                field_definitions[field_name] = (field_type, field_info)
            else:
                # If it's just a Field object, try to extract type information
                if hasattr(field_def, 'annotation') and field_def.annotation is not None:
                    field_definitions[field_name] = (field_def.annotation, field_def)
                else:
                    # Default to Any type if we can't determine the type
                    field_definitions[field_name] = (Any, field_def)
        
        # Create model_config for Pydantic v2
        config_dict = {}
        if example:
            config_dict['json_schema_extra'] = {"example": example}
        
        # Use Pydantic's create_model function for proper v2 compatibility
        model = create_model(
            name,
            **field_definitions,
            __config__=ConfigDict(**config_dict) if config_dict else None,
            __module__=__name__
        )
        
        # Add docstring if description provided
        if description:
            model.__doc__ = description
        
        return model
    
    @staticmethod
    def create_success_response_model(
        name: str,
        additional_fields: Dict[str, Any] = None,
        success_message: str = "Operation completed successfully",
        example: Dict[str, Any] = None
    ) -> Type[BaseModel]:
        """
        Create a success response model with clean fields.
        
        Args:
            name: Name of the response model class
            additional_fields: Additional fields beyond success/message
            success_message: Default success message
            example: Optional example for documentation
            
        Returns:
            Clean success response model
        """
        fields = {
            'success': (Literal[True], Field(True, description="Success flag")),
            'message': (str, Field(success_message, description="Success message"))
        }
        
        if additional_fields:
            fields.update(additional_fields)
        
        if not example:
            example = {
                "success": True,
                "message": success_message
            }
            if additional_fields:
                for field_name, field_def in additional_fields.items():
                    if isinstance(field_def, tuple) and len(field_def) > 1:
                        field_info = field_def[1]
                        if hasattr(field_info, 'default') and field_info.default is not ...:
                            example[field_name] = field_info.default
        
        return ResponseModelFramework.create_clean_response_model(
            name=name,
            fields=fields,
            description=f"Success response for {name}",
            example=example
        )
    
    @staticmethod
    def create_error_response_model(
        name: str,
        additional_fields: Dict[str, Any] = None,
        error_message: str = "Operation failed",
        example: Dict[str, Any] = None
    ) -> Type[BaseModel]:
        """
        Create an error response model with clean fields.
        
        Args:
            name: Name of the response model class
            additional_fields: Additional fields beyond success/message
            error_message: Default error message
            example: Optional example for documentation
            
        Returns:
            Clean error response model
        """
        fields = {
            'success': (Literal[False], Field(False, description="Success flag")),
            'message': (str, Field(error_message, description="Error message"))
        }
        
        if additional_fields:
            fields.update(additional_fields)
        
        if not example:
            example = {
                "success": False,
                "message": error_message
            }
            if additional_fields:
                for field_name, field_def in additional_fields.items():
                    if isinstance(field_def, tuple) and len(field_def) > 1:
                        field_info = field_def[1]
                        if hasattr(field_info, 'default') and field_info.default is not ...:
                            example[field_name] = field_info.default
        
        return ResponseModelFramework.create_clean_response_model(
            name=name,
            fields=fields,
            description=f"Error response for {name}",
            example=example
        )


class OverloadResponseBuilder:
    """
    Builder for creating @overload response functions with type safety.
    
    This class helps create the @overload pattern for endpoints that
    can return different response structures based on conditions.
    """
    
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.overloads = []
        self.union_type = None
    
    def add_overload(
        self,
        condition_type: Type,
        response_model: Type[BaseModel],
        **kwargs
    ):
        """
        Add an @overload signature to the builder.
        
        Args:
            condition_type: Type for the condition parameter (e.g., Literal[True])
            response_model: Response model class for this overload
            **kwargs: Additional parameters for the overload
        """
        self.overloads.append({
            'condition_type': condition_type,
            'response_model': response_model,
            'kwargs': kwargs
        })
        return self
    
    def build_union_type(self):
        """Build the Union type from all registered overloads."""
        if not self.overloads:
            raise ValueError("No overloads registered")
        
        response_types = [overload['response_model'] for overload in self.overloads]
        self.union_type = Union[tuple(response_types)]
        return self.union_type
    
    def generate_overload_signatures(self) -> str:
        """
        Generate the @overload function signatures as a string.
        
        Returns:
            String containing the @overload function definitions
        """
        if not self.overloads:
            raise ValueError("No overloads registered")
        
        signatures = []
        
        # Generate @overload signatures
        for overload in self.overloads:
            condition_type = overload['condition_type']
            response_model = overload['response_model']
            kwargs = overload['kwargs']
            
            # Build parameter list
            params = []
            for param_name, param_type in kwargs.items():
                params.append(f"{param_name}: {param_type.__name__}")
            
            param_str = ", ".join(params)
            
            signature = f"""@overload
def {self.function_name}({param_str}) -> {response_model.__name__}: ..."""
            
            signatures.append(signature)
        
        # Generate implementation signature
        impl_params = []
        for overload in self.overloads:
            for param_name, param_type in overload['kwargs'].items():
                if param_name not in [p.split(':')[0] for p in impl_params]:
                    impl_params.append(f"{param_name}: {param_type.__name__} = None")
        
        impl_param_str = ", ".join(impl_params)
        union_type_str = f"Union[{', '.join([o['response_model'].__name__ for o in self.overloads])}]"
        
        implementation = f"""def {self.function_name}({impl_param_str}) -> {union_type_str}:
    \"\"\"Implementation with conditional logic.\"\"\"
    # Implementation logic goes here
    pass"""
        
        signatures.append(implementation)
        
        return "\n\n".join(signatures)


def create_fastapi_union_response(
    success_model: Type[BaseModel],
    error_model: Type[BaseModel],
    success_status: int = 200,
    error_status: int = 400
) -> Dict[int, Dict[str, Any]]:
    """
    Create FastAPI responses configuration for Union response types.
    
    Args:
        success_model: Success response model
        error_model: Error response model  
        success_status: HTTP status code for success (default: 200)
        error_status: HTTP status code for error (default: 400)
        
    Returns:
        FastAPI responses configuration dictionary
    """
    return {
        success_status: {
            "model": success_model,
            "description": "Successful operation"
        },
        error_status: {
            "model": error_model,
            "description": "Operation failed"
        }
    }


def create_json_response(
    model_instance: BaseModel,
    status_code: int = 200
) -> JSONResponse:
    """
    Create a JSONResponse from a Pydantic model instance.
    
    Args:
        model_instance: Pydantic model instance
        status_code: HTTP status code
        
    Returns:
        FastAPI JSONResponse
    """
    return JSONResponse(
        status_code=status_code,
        content=model_instance.model_dump(exclude_none=True)
    )


# Utility functions for common patterns
def create_binary_response_models(
    base_name: str,
    success_fields: Dict[str, Any] = None,
    error_fields: Dict[str, Any] = None,
    success_message: str = "Operation completed successfully",
    error_message: str = "Operation failed"
) -> tuple[Type[BaseModel], Type[BaseModel], Type]:
    """
    Create a pair of success/error response models and their Union type.
    
    Args:
        base_name: Base name for the response models
        success_fields: Additional fields for success response
        error_fields: Additional fields for error response
        success_message: Default success message
        error_message: Default error message
        
    Returns:
        Tuple of (SuccessModel, ErrorModel, UnionType)
    """
    success_model = ResponseModelFramework.create_success_response_model(
        name=f"{base_name}SuccessResponse",
        additional_fields=success_fields,
        success_message=success_message
    )
    
    error_model = ResponseModelFramework.create_error_response_model(
        name=f"{base_name}ErrorResponse", 
        additional_fields=error_fields,
        error_message=error_message
    )
    
    union_type = Union[success_model, error_model]
    
    return success_model, error_model, union_type