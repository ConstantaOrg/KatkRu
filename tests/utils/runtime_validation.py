"""
Runtime Validation System for Response Models

This module provides runtime validation of response models against actual API
responses, allowing continuous monitoring of model accuracy in tests and production.
"""

from typing import Dict, List, Any, Optional, Type, Callable, Set
from dataclasses import dataclass, field
import json
import logging
from datetime import datetime
from contextlib import contextmanager
from pydantic import BaseModel
from tests.utils.model_accuracy_tools import (
    ModelAccuracyVerifier, 
    ModelAccuracyReport, 
    OverloadModelVerifier,
    MismatchSeverity
)


@dataclass
class ValidationConfig:
    """Configuration for runtime validation."""
    enabled: bool = True
    log_mismatches: bool = True
    fail_on_critical: bool = False
    fail_on_warning: bool = False
    collect_samples: bool = True
    max_samples: int = 10
    report_file: Optional[str] = None


@dataclass
class ValidationSession:
    """Tracks validation results during a test session."""
    session_id: str
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    reports: List[ModelAccuracyReport] = field(default_factory=list)
    config: ValidationConfig = field(default_factory=ValidationConfig)
    
    def add_report(self, report: ModelAccuracyReport) -> None:
        """Add a validation report to the session."""
        self.reports.append(report)
        
        if self.config.log_mismatches and report.mismatches:
            logger = logging.getLogger(__name__)
            logger.warning(f"Model accuracy issues found for {report.model_name}: {len(report.mismatches)} mismatches")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results in this session."""
        total_reports = len(self.reports)
        total_mismatches = sum(len(r.mismatches) for r in self.reports)
        critical_issues = sum(len(r.get_critical_issues()) for r in self.reports)
        
        avg_accuracy = sum(r.accuracy_score for r in self.reports) / total_reports if total_reports > 0 else 0.0
        
        return {
            "session_id": self.session_id,
            "total_reports": total_reports,
            "total_mismatches": total_mismatches,
            "critical_issues": critical_issues,
            "average_accuracy": avg_accuracy,
            "models_tested": [r.model_name for r in self.reports]
        }


class RuntimeValidator:
    """
    Runtime validator that can be integrated into tests and API calls
    to continuously monitor model accuracy.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.verifier = ModelAccuracyVerifier()
        self.overload_verifier = OverloadModelVerifier()
        self.current_session: Optional[ValidationSession] = None
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def validation_session(self, session_id: str):
        """Context manager for validation sessions."""
        old_session = self.current_session
        self.current_session = ValidationSession(
            session_id=session_id,
            config=self.config
        )
        
        try:
            yield self.current_session
        finally:
            # Generate report if configured
            if self.config.report_file and self.current_session:
                self._generate_session_report(self.current_session)
            
            self.current_session = old_session
    
    def validate_response(self, model_class: Type[BaseModel], 
                         response_data: Dict[str, Any],
                         endpoint: str = "unknown",
                         method: str = "GET") -> ModelAccuracyReport:
        """
        Validate a response against a model and handle results based on config.
        
        Args:
            model_class: Pydantic model to validate against
            response_data: Actual API response data
            endpoint: API endpoint being tested
            method: HTTP method
            
        Returns:
            ModelAccuracyReport with validation results
            
        Raises:
            AssertionError: If configured to fail on critical/warning issues
        """
        if not self.config.enabled:
            # Return empty report if validation is disabled
            return ModelAccuracyReport(
                model_name=model_class.__name__,
                endpoint=endpoint,
                method=method
            )
        
        # Perform validation
        report = self.verifier.compare_model_with_response(
            model_class, response_data, endpoint, method
        )
        
        # Add to current session if active
        if self.current_session:
            self.current_session.add_report(report)
        
        # Handle results based on configuration
        self._handle_validation_result(report)
        
        return report
    
    def validate_overload_models(self, success_model: BaseModel, 
                               conflict_model: BaseModel,
                               endpoint: str = "unknown") -> List[ModelAccuracyReport]:
        """
        Validate @overload response models for clean JSON and proper separation.
        
        Args:
            success_model: Success scenario model instance
            conflict_model: Conflict scenario model instance
            endpoint: API endpoint being tested
            
        Returns:
            List of validation reports for both models
        """
        reports = []
        
        if not self.config.enabled:
            return reports
        
        # Verify clean JSON output and scenario separation
        mismatches = self.overload_verifier.verify_scenario_separation(
            success_model, conflict_model
        )
        
        # Create reports for both models
        success_report = ModelAccuracyReport(
            model_name=success_model.__class__.__name__,
            endpoint=endpoint,
            method="POST"  # Most @overload scenarios are POST
        )
        
        conflict_report = ModelAccuracyReport(
            model_name=conflict_model.__class__.__name__,
            endpoint=endpoint,
            method="POST"
        )
        
        # Distribute mismatches to appropriate reports
        for mismatch in mismatches:
            if "success" in mismatch.field_name.lower() and "true" in mismatch.expected.lower():
                success_report.add_mismatch(mismatch)
            elif "success" in mismatch.field_name.lower() and "false" in mismatch.expected.lower():
                conflict_report.add_mismatch(mismatch)
            else:
                # General mismatches go to both
                success_report.add_mismatch(mismatch)
                conflict_report.add_mismatch(mismatch)
        
        success_report.calculate_accuracy_score()
        conflict_report.calculate_accuracy_score()
        
        reports.extend([success_report, conflict_report])
        
        # Add to session and handle results
        if self.current_session:
            for report in reports:
                self.current_session.add_report(report)
        
        for report in reports:
            self._handle_validation_result(report)
        
        return reports
    
    def _handle_validation_result(self, report: ModelAccuracyReport) -> None:
        """Handle validation result based on configuration."""
        critical_issues = report.get_critical_issues()
        warning_issues = [m for m in report.mismatches if m.severity == MismatchSeverity.WARNING]
        
        # Log issues
        if self.config.log_mismatches:
            if critical_issues:
                self.logger.error(
                    f"Critical model accuracy issues in {report.model_name} "
                    f"for {report.endpoint}: {len(critical_issues)} critical mismatches"
                )
            elif warning_issues:
                self.logger.warning(
                    f"Model accuracy warnings in {report.model_name} "
                    f"for {report.endpoint}: {len(warning_issues)} warnings"
                )
        
        # Fail if configured to do so
        if self.config.fail_on_critical and critical_issues:
            error_details = "\n".join([
                f"- {m.field_name}: {m.description}" for m in critical_issues
            ])
            raise AssertionError(
                f"Critical model accuracy issues found in {report.model_name}:\n{error_details}"
            )
        
        if self.config.fail_on_warning and (critical_issues or warning_issues):
            all_issues = critical_issues + warning_issues
            error_details = "\n".join([
                f"- {m.field_name}: {m.description}" for m in all_issues
            ])
            raise AssertionError(
                f"Model accuracy issues found in {report.model_name}:\n{error_details}"
            )
    
    def _generate_session_report(self, session: ValidationSession) -> None:
        """Generate a comprehensive report for the validation session."""
        try:
            report_data = {
                "session_summary": session.get_summary(),
                "detailed_reports": [
                    {
                        "model_name": r.model_name,
                        "endpoint": r.endpoint,
                        "accuracy_score": r.accuracy_score,
                        "mismatches": [
                            {
                                "field_name": m.field_name,
                                "type": m.mismatch_type,
                                "severity": m.severity.value,
                                "description": m.description,
                                "suggestion": m.suggestion
                            }
                            for m in r.mismatches
                        ]
                    }
                    for r in session.reports
                ]
            }
            
            with open(self.config.report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"Validation session report written to {self.config.report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate session report: {str(e)}")


class ValidationDecorator:
    """
    Decorator for automatically validating API responses in tests.
    """
    
    def __init__(self, validator: RuntimeValidator):
        self.validator = validator
    
    def validate_response(self, model_class: Type[BaseModel], 
                         endpoint: str = None, method: str = "GET"):
        """
        Decorator to automatically validate API responses.
        
        Usage:
            @validator.validate_response(MyResponseModel, "/api/endpoint")
            async def test_my_endpoint(client):
                resp = await client.get("/api/endpoint")
                return resp.json()  # This will be validated automatically
        """
        def decorator(test_func):
            async def wrapper(*args, **kwargs):
                # Execute the test function
                result = await test_func(*args, **kwargs)
                
                # If result is a dict, validate it
                if isinstance(result, dict):
                    endpoint_name = endpoint or test_func.__name__
                    self.validator.validate_response(
                        model_class, result, endpoint_name, method
                    )
                
                return result
            
            return wrapper
        return decorator


# Global runtime validator instance
_global_validator = RuntimeValidator()


def configure_runtime_validation(config: ValidationConfig) -> None:
    """Configure the global runtime validator."""
    global _global_validator
    _global_validator.config = config


def get_runtime_validator() -> RuntimeValidator:
    """Get the global runtime validator instance."""
    return _global_validator


def validate_response_runtime(model_class: Type[BaseModel], 
                            response_data: Dict[str, Any],
                            endpoint: str = "unknown",
                            method: str = "GET") -> ModelAccuracyReport:
    """
    Convenience function for runtime response validation.
    
    This can be easily integrated into existing tests without major refactoring.
    """
    return _global_validator.validate_response(model_class, response_data, endpoint, method)


def validate_overload_runtime(success_model: BaseModel, 
                            conflict_model: BaseModel,
                            endpoint: str = "unknown") -> List[ModelAccuracyReport]:
    """
    Convenience function for runtime @overload model validation.
    """
    return _global_validator.validate_overload_models(success_model, conflict_model, endpoint)


# Context manager for validation sessions
def validation_session(session_id: str):
    """Context manager for validation sessions using global validator."""
    return _global_validator.validation_session(session_id)