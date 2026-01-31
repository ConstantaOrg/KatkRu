"""
Model Accuracy Verification Tools

This module provides tools to compare Pydantic response models with actual API
responses, identify mismatches, and generate reports for model-reality discrepancies.
"""

from typing import Dict, List, Any, Optional, Type, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import inspect
from datetime import datetime
from pydantic import BaseModel
from pydantic.fields import FieldInfo


class MismatchSeverity(Enum):
    """Severity levels for model-reality mismatches."""
    CRITICAL = "critical"      # Field missing or wrong type
    WARNING = "warning"        # Field optional but expected
    INFO = "info"             # Additional field in response
    MINOR = "minor"           # Type coercion possible


@dataclass
class FieldMismatch:
    """Represents a mismatch between model field and actual response."""
    field_name: str
    mismatch_type: str  # "missing", "extra", "type_mismatch", "value_mismatch"
    expected: Optional[str] = None
    actual: Optional[str] = None
    severity: MismatchSeverity = MismatchSeverity.WARNING
    description: str = ""
    suggestion: str = ""


@dataclass
class ModelAccuracyReport:
    """Report of model accuracy against actual API responses."""
    model_name: str
    endpoint: str
    method: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_fields_checked: int = 0
    mismatches: List[FieldMismatch] = field(default_factory=list)
    accuracy_score: float = 0.0
    sample_responses: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_mismatch(self, mismatch: FieldMismatch) -> None:
        """Add a mismatch to the report."""
        self.mismatches.append(mismatch)
    
    def calculate_accuracy_score(self) -> float:
        """Calculate accuracy score based on mismatches."""
        if self.total_fields_checked == 0:
            return 0.0
        
        # Weight mismatches by severity
        severity_weights = {
            MismatchSeverity.CRITICAL: 1.0,
            MismatchSeverity.WARNING: 0.7,
            MismatchSeverity.INFO: 0.3,
            MismatchSeverity.MINOR: 0.1
        }
        
        total_penalty = sum(
            severity_weights.get(mismatch.severity, 0.5) 
            for mismatch in self.mismatches
        )
        
        # Score is percentage of fields that are accurate
        self.accuracy_score = max(0.0, (self.total_fields_checked - total_penalty) / self.total_fields_checked)
        return self.accuracy_score
    
    def get_critical_issues(self) -> List[FieldMismatch]:
        """Get only critical mismatches."""
        return [m for m in self.mismatches if m.severity == MismatchSeverity.CRITICAL]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        severity_counts = {}
        for severity in MismatchSeverity:
            severity_counts[severity.value] = len([
                m for m in self.mismatches if m.severity == severity
            ])
        
        return {
            "model_name": self.model_name,
            "endpoint": self.endpoint,
            "accuracy_score": self.accuracy_score,
            "total_mismatches": len(self.mismatches),
            "severity_breakdown": severity_counts,
            "has_critical_issues": len(self.get_critical_issues()) > 0
        }


class ModelAnalyzer:
    """Analyzes Pydantic models to extract field information."""
    
    @staticmethod
    def extract_model_fields(model_class: Type[BaseModel]) -> Dict[str, Dict[str, Any]]:
        """
        Extract field information from a Pydantic model.
        
        Returns:
            Dictionary mapping field names to field metadata
        """
        fields = {}
        
        if hasattr(model_class, 'model_fields'):
            # Pydantic v2
            for field_name, field_info in model_class.model_fields.items():
                fields[field_name] = {
                    'type': field_info.annotation,
                    'required': field_info.is_required(),
                    'default': getattr(field_info, 'default', None),
                    'description': getattr(field_info, 'description', '')
                }
        else:
            # Pydantic v1 fallback
            for field_name, field_info in model_class.__fields__.items():
                fields[field_name] = {
                    'type': field_info.type_,
                    'required': field_info.required,
                    'default': field_info.default,
                    'description': getattr(field_info, 'description', '')
                }
        
        return fields
    
    @staticmethod
    def get_type_name(type_annotation: Any) -> str:
        """Get human-readable type name from type annotation."""
        if hasattr(type_annotation, '__name__'):
            return type_annotation.__name__
        elif hasattr(type_annotation, '_name'):
            return type_annotation._name
        elif str(type_annotation).startswith('typing.'):
            return str(type_annotation).replace('typing.', '')
        else:
            return str(type_annotation)


class ResponseAnalyzer:
    """Analyzes actual API responses to extract structure information."""
    
    @staticmethod
    def analyze_response_structure(response: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze the structure of an actual API response.
        
        Returns:
            Dictionary mapping field names to field metadata
        """
        fields = {}
        
        def analyze_value(value: Any) -> Dict[str, Any]:
            """Analyze a single value to determine its metadata."""
            value_type = type(value)
            
            metadata = {
                'type': value_type,
                'type_name': value_type.__name__,
                'nullable': value is None
            }
            
            if isinstance(value, list):
                if value:
                    # Analyze first item to determine list item type
                    first_item = value[0]
                    metadata['item_type'] = type(first_item)
                    metadata['item_type_name'] = type(first_item).__name__
                    
                    # Check if all items have same type
                    all_same_type = all(type(item) == type(first_item) for item in value)
                    metadata['homogeneous'] = all_same_type
                else:
                    metadata['item_type'] = None
                    metadata['homogeneous'] = True
                
                metadata['length'] = len(value)
            
            elif isinstance(value, dict):
                metadata['keys'] = list(value.keys())
                metadata['nested_structure'] = {
                    k: analyze_value(v) for k, v in value.items()
                }
            
            elif isinstance(value, str):
                metadata['length'] = len(value)
                metadata['empty'] = len(value) == 0
            
            return metadata
        
        for field_name, value in response.items():
            fields[field_name] = analyze_value(value)
        
        return fields


class ModelAccuracyVerifier:
    """
    Main class for verifying model accuracy against actual API responses.
    """
    
    def __init__(self):
        self.model_analyzer = ModelAnalyzer()
        self.response_analyzer = ResponseAnalyzer()
    
    def compare_model_with_response(self, model_class: Type[BaseModel], 
                                  response: Dict[str, Any],
                                  endpoint: str = "unknown",
                                  method: str = "GET") -> ModelAccuracyReport:
        """
        Compare a Pydantic model with an actual API response.
        
        Args:
            model_class: Pydantic model class to verify
            response: Actual API response data
            endpoint: API endpoint being tested
            method: HTTP method
            
        Returns:
            ModelAccuracyReport with detailed comparison results
        """
        report = ModelAccuracyReport(
            model_name=model_class.__name__,
            endpoint=endpoint,
            method=method
        )
        
        # Extract model and response structures
        model_fields = self.model_analyzer.extract_model_fields(model_class)
        response_fields = self.response_analyzer.analyze_response_structure(response)
        
        report.total_fields_checked = len(model_fields) + len(response_fields)
        report.sample_responses.append(response)
        
        # Check for missing fields (in model but not in response)
        for field_name, field_info in model_fields.items():
            if field_name not in response_fields:
                severity = MismatchSeverity.CRITICAL if field_info['required'] else MismatchSeverity.WARNING
                
                mismatch = FieldMismatch(
                    field_name=field_name,
                    mismatch_type="missing",
                    expected=f"Field '{field_name}' ({self.model_analyzer.get_type_name(field_info['type'])})",
                    actual="Field not present in response",
                    severity=severity,
                    description=f"Model expects field '{field_name}' but it's missing from response",
                    suggestion=f"Remove field from model or make it optional" if field_info['required'] 
                              else f"Verify if field should be present"
                )
                report.add_mismatch(mismatch)
        
        # Check for extra fields (in response but not in model)
        for field_name, field_info in response_fields.items():
            if field_name not in model_fields:
                mismatch = FieldMismatch(
                    field_name=field_name,
                    mismatch_type="extra",
                    expected="Field not in model",
                    actual=f"Field present ({field_info['type_name']})",
                    severity=MismatchSeverity.INFO,
                    description=f"Response contains field '{field_name}' not defined in model",
                    suggestion=f"Add field to model or verify if it should be ignored"
                )
                report.add_mismatch(mismatch)
        
        # Check for type mismatches (fields present in both)
        common_fields = set(model_fields.keys()) & set(response_fields.keys())
        for field_name in common_fields:
            model_field = model_fields[field_name]
            response_field = response_fields[field_name]
            
            expected_type = model_field['type']
            actual_type = response_field['type']
            
            # Compare types (handle common type coercions)
            if not self._types_compatible(expected_type, actual_type):
                severity = MismatchSeverity.CRITICAL
                
                # Check if it's a minor coercion issue
                if self._is_minor_type_issue(expected_type, actual_type):
                    severity = MismatchSeverity.MINOR
                
                mismatch = FieldMismatch(
                    field_name=field_name,
                    mismatch_type="type_mismatch",
                    expected=self.model_analyzer.get_type_name(expected_type),
                    actual=response_field['type_name'],
                    severity=severity,
                    description=f"Type mismatch for field '{field_name}'",
                    suggestion=f"Update model type to {response_field['type_name']} or verify response data"
                )
                report.add_mismatch(mismatch)
        
        report.calculate_accuracy_score()
        return report
    
    def _types_compatible(self, expected_type: Any, actual_type: type) -> bool:
        """Check if types are compatible (allowing for reasonable coercions)."""
        # Direct match
        if expected_type == actual_type:
            return True
        
        # Handle Union types (Optional, etc.)
        if hasattr(expected_type, '__origin__'):
            if expected_type.__origin__ is Union:
                # Check if actual type matches any of the union types
                union_args = expected_type.__args__
                return any(self._types_compatible(arg, actual_type) for arg in union_args)
        
        # Handle List types
        if hasattr(expected_type, '__origin__') and expected_type.__origin__ is list:
            return actual_type is list
        
        # Handle Dict types
        if hasattr(expected_type, '__origin__') and expected_type.__origin__ is dict:
            return actual_type is dict
        
        # Common compatible types
        compatible_pairs = [
            (int, float),  # int can be float
            (str, int),    # Sometimes IDs are strings
            (str, float),  # Sometimes numbers are strings
        ]
        
        for exp, act in compatible_pairs:
            if expected_type == exp and actual_type == act:
                return True
        
        return False
    
    def _is_minor_type_issue(self, expected_type: Any, actual_type: type) -> bool:
        """Check if type mismatch is minor (easily fixable)."""
        minor_issues = [
            (int, float),    # float instead of int
            (float, int),    # int instead of float
            (str, int),      # string ID instead of int
            (str, float),    # string number instead of float
        ]
        
        for exp, act in minor_issues:
            if expected_type == exp and actual_type == act:
                return True
        
        return False
    
    def verify_multiple_responses(self, model_class: Type[BaseModel],
                                responses: List[Dict[str, Any]],
                                endpoint: str = "unknown",
                                method: str = "GET") -> ModelAccuracyReport:
        """
        Verify model accuracy against multiple response samples.
        
        This provides more comprehensive analysis by checking consistency
        across multiple actual responses.
        """
        if not responses:
            return ModelAccuracyReport(
                model_name=model_class.__name__,
                endpoint=endpoint,
                method=method
            )
        
        # Start with first response
        report = self.compare_model_with_response(model_class, responses[0], endpoint, method)
        
        # Add additional responses to sample
        for response in responses[1:]:
            report.sample_responses.append(response)
            
            # Check for consistency issues across responses
            additional_report = self.compare_model_with_response(model_class, response, endpoint, method)
            
            # Merge mismatches (avoid duplicates)
            existing_mismatches = {
                (m.field_name, m.mismatch_type) for m in report.mismatches
            }
            
            for mismatch in additional_report.mismatches:
                mismatch_key = (mismatch.field_name, mismatch.mismatch_type)
                if mismatch_key not in existing_mismatches:
                    # New type of mismatch found in additional response
                    mismatch.description += f" (found in response sample {len(report.sample_responses)})"
                    report.add_mismatch(mismatch)
        
        # Recalculate accuracy with all samples
        report.calculate_accuracy_score()
        return report


class OverloadModelVerifier:
    """
    Specialized verifier for @overload response models.
    
    Verifies that @overload models produce clean JSON without null fields
    and maintain proper separation between different response scenarios.
    """
    
    def __init__(self):
        self.base_verifier = ModelAccuracyVerifier()
    
    def verify_clean_json_output(self, model_instance: BaseModel) -> FieldMismatch:
        """
        Verify that model instance produces clean JSON without null fields.
        
        This is the core benefit of @overload models - no null field pollution.
        """
        try:
            # Convert to dict and check for null values
            model_dict = model_instance.model_dump() if hasattr(model_instance, 'model_dump') else model_instance.dict()
            
            null_fields = []
            for field_name, value in model_dict.items():
                if value is None:
                    null_fields.append(field_name)
            
            if null_fields:
                return FieldMismatch(
                    field_name=", ".join(null_fields),
                    mismatch_type="null_field_pollution",
                    expected="No null fields (clean @overload pattern)",
                    actual=f"Null fields: {null_fields}",
                    severity=MismatchSeverity.CRITICAL,
                    description="@overload model contains null fields, violating clean JSON principle",
                    suggestion="Remove null fields or use separate response models for different scenarios"
                )
            
            return None  # No issues
            
        except Exception as e:
            return FieldMismatch(
                field_name="model_serialization",
                mismatch_type="serialization_error",
                expected="Successful JSON serialization",
                actual=f"Error: {str(e)}",
                severity=MismatchSeverity.CRITICAL,
                description="Model failed to serialize to JSON",
                suggestion="Fix model serialization issues"
            )
    
    def verify_scenario_separation(self, success_model: BaseModel, 
                                 conflict_model: BaseModel) -> List[FieldMismatch]:
        """
        Verify that @overload success and conflict models are properly separated.
        
        They should have different structures and both should be clean.
        """
        mismatches = []
        
        # Check both models for clean JSON
        success_clean = self.verify_clean_json_output(success_model)
        if success_clean:
            mismatches.append(success_clean)
        
        conflict_clean = self.verify_clean_json_output(conflict_model)
        if conflict_clean:
            mismatches.append(conflict_clean)
        
        # Check for proper separation
        try:
            success_dict = success_model.model_dump() if hasattr(success_model, 'model_dump') else success_model.dict()
            conflict_dict = conflict_model.model_dump() if hasattr(conflict_model, 'model_dump') else conflict_model.dict()
            
            # Both should have 'success' field with different values
            if success_dict.get('success') is not True:
                mismatches.append(FieldMismatch(
                    field_name="success",
                    mismatch_type="incorrect_success_value",
                    expected="True",
                    actual=str(success_dict.get('success')),
                    severity=MismatchSeverity.CRITICAL,
                    description="Success model should have success=True",
                    suggestion="Set success=True in success response model"
                ))
            
            if conflict_dict.get('success') is not False:
                mismatches.append(FieldMismatch(
                    field_name="success",
                    mismatch_type="incorrect_success_value",
                    expected="False",
                    actual=str(conflict_dict.get('success')),
                    severity=MismatchSeverity.CRITICAL,
                    description="Conflict model should have success=False",
                    suggestion="Set success=False in conflict response model"
                ))
            
        except Exception as e:
            mismatches.append(FieldMismatch(
                field_name="scenario_separation",
                mismatch_type="comparison_error",
                expected="Successful model comparison",
                actual=f"Error: {str(e)}",
                severity=MismatchSeverity.CRITICAL,
                description="Failed to compare success and conflict models",
                suggestion="Fix model serialization or comparison logic"
            ))
        
        return mismatches


def generate_accuracy_report_html(report: ModelAccuracyReport) -> str:
    """Generate HTML report for model accuracy verification."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Accuracy Report - {report.model_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
            .summary {{ margin: 20px 0; }}
            .mismatch {{ margin: 10px 0; padding: 10px; border-left: 4px solid; }}
            .critical {{ border-color: #d32f2f; background-color: #ffebee; }}
            .warning {{ border-color: #f57c00; background-color: #fff3e0; }}
            .info {{ border-color: #1976d2; background-color: #e3f2fd; }}
            .minor {{ border-color: #388e3c; background-color: #e8f5e9; }}
            .sample {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; }}
            pre {{ background-color: #f0f0f0; padding: 10px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Model Accuracy Report</h1>
            <p><strong>Model:</strong> {report.model_name}</p>
            <p><strong>Endpoint:</strong> {report.endpoint} ({report.method})</p>
            <p><strong>Generated:</strong> {report.timestamp}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Accuracy Score:</strong> {report.accuracy_score:.2%}</p>
            <p><strong>Total Mismatches:</strong> {len(report.mismatches)}</p>
            <p><strong>Critical Issues:</strong> {len(report.get_critical_issues())}</p>
        </div>
        
        <div class="mismatches">
            <h2>Mismatches</h2>
    """
    
    for mismatch in report.mismatches:
        severity_class = mismatch.severity.value
        html += f"""
            <div class="mismatch {severity_class}">
                <h3>{mismatch.field_name} ({mismatch.mismatch_type})</h3>
                <p><strong>Severity:</strong> {mismatch.severity.value.upper()}</p>
                <p><strong>Expected:</strong> {mismatch.expected}</p>
                <p><strong>Actual:</strong> {mismatch.actual}</p>
                <p><strong>Description:</strong> {mismatch.description}</p>
                <p><strong>Suggestion:</strong> {mismatch.suggestion}</p>
            </div>
        """
    
    html += """
        </div>
        
        <div class="samples">
            <h2>Sample Responses</h2>
    """
    
    for i, sample in enumerate(report.sample_responses):
        html += f"""
            <div class="sample">
                <h3>Sample {i + 1}</h3>
                <pre>{json.dumps(sample, indent=2)}</pre>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html