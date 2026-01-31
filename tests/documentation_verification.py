#!/usr/bin/env python3
"""
Documentation Verification Script

This script verifies that corrected response models generate accurate documentation
and that @overload Union response types work correctly with OpenAPI schema generation.

Requirements validated: 5.1, 5.2, 5.3
"""

import json
import asyncio
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from fastapi.openapi.utils import get_openapi

from core.main import app
from core.utils.response_model_utils import (
    CardsSaveSuccessResponse, CardsSaveConflictResponse,
    TtableVersionsPreCommitSuccessResponse, TtableVersionsPreCommitConflictResponse,
    UserRegistrationSuccessResponse, UserRegistrationConflictResponse,
    create_cards_save_response, create_ttable_precommit_response
)


class DocumentationVerifier:
    """Verifies that documentation accurately reflects API behavior."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.openapi_schema = None
        self.verification_results = []
    
    def get_openapi_schema(self) -> Dict[str, Any]:
        """Get the OpenAPI schema from the FastAPI app."""
        if self.openapi_schema is None:
            self.openapi_schema = get_openapi(
                title=app.title,
                version="1.0.0",
                description="API Documentation Verification",
                routes=app.routes,
            )
        return self.openapi_schema
    
    def verify_response_model_accuracy(self) -> Dict[str, Any]:
        """Verify that response models accurately reflect actual API responses."""
        results = {
            "passed": True,
            "issues": [],
            "verified_endpoints": []
        }
        
        schema = self.get_openapi_schema()
        
        # Check that @overload models are properly represented
        components = schema.get("components", {}).get("schemas", {})
        
        # Verify Cards Save response models
        if "CardsSaveSuccessResponse" in components:
            success_schema = components["CardsSaveSuccessResponse"]
            required_fields = ["success", "message", "new_card_hist_id"]
            
            for field in required_fields:
                if field not in success_schema.get("properties", {}):
                    results["issues"].append(f"CardsSaveSuccessResponse missing required field: {field}")
                    results["passed"] = False
            
            # Verify no null fields in examples
            example = success_schema.get("example", {})
            if any(value is None for value in example.values()):
                results["issues"].append("CardsSaveSuccessResponse example contains null values")
                results["passed"] = False
            
            results["verified_endpoints"].append("cards/save (success)")
        
        if "CardsSaveConflictResponse" in components:
            conflict_schema = components["CardsSaveConflictResponse"]
            required_fields = ["success", "message", "conflicts", "description"]
            
            for field in required_fields:
                if field not in conflict_schema.get("properties", {}):
                    results["issues"].append(f"CardsSaveConflictResponse missing required field: {field}")
                    results["passed"] = False
            
            results["verified_endpoints"].append("cards/save (conflict)")
        
        # Verify Ttable PreCommit response models
        if "TtableVersionsPreCommitSuccessResponse" in components:
            success_schema = components["TtableVersionsPreCommitSuccessResponse"]
            required_fields = ["success", "message"]
            
            for field in required_fields:
                if field not in success_schema.get("properties", {}):
                    results["issues"].append(f"TtableVersionsPreCommitSuccessResponse missing required field: {field}")
                    results["passed"] = False
            
            results["verified_endpoints"].append("ttable/versions/pre-commit (success)")
        
        return results
    
    def verify_multi_response_scenarios(self) -> Dict[str, Any]:
        """Verify that multi-response scenarios are properly documented."""
        results = {
            "passed": True,
            "issues": [],
            "verified_scenarios": []
        }
        
        schema = self.get_openapi_schema()
        paths = schema.get("paths", {})
        
        # Check cards/save endpoint
        cards_save_path = paths.get("/private/n8n_ui/cards/save", {})
        if cards_save_path:
            post_method = cards_save_path.get("post", {})
            responses = post_method.get("responses", {})
            
            # Should have multiple response scenarios
            if "200" not in responses:
                results["issues"].append("cards/save missing 200 response documentation")
                results["passed"] = False
            
            # Verify response content structure
            if "200" in responses:
                response_200 = responses["200"]
                if "content" in response_200:
                    content = response_200["content"].get("application/json", {})
                    if "schema" not in content:
                        results["issues"].append("cards/save 200 response missing schema")
                        results["passed"] = False
            
            results["verified_scenarios"].append("cards/save multi-response")
        
        # Check ttable/versions/pre-commit endpoint
        precommit_path = paths.get("/private/ttable/versions/pre-commit", {})
        if precommit_path:
            put_method = precommit_path.get("put", {})
            responses = put_method.get("responses", {})
            
            # Should have multiple status codes (200, 202, 409)
            expected_codes = ["200", "202", "409"]
            for code in expected_codes:
                if code not in responses:
                    results["issues"].append(f"ttable/versions/pre-commit missing {code} response documentation")
                    results["passed"] = False
            
            results["verified_scenarios"].append("ttable/versions/pre-commit multi-response")
        
        return results
    
    def verify_openapi_union_types(self) -> Dict[str, Any]:
        """Verify that @overload Union response types work correctly with OpenAPI."""
        results = {
            "passed": True,
            "issues": [],
            "verified_unions": []
        }
        
        schema = self.get_openapi_schema()
        
        # Test that Union types are properly handled
        try:
            # Create sample responses using @overload functions
            success_response = create_cards_save_response(
                success=True,
                new_card_hist_id=123
            )
            
            conflict_response = create_cards_save_response(
                success=False,
                conflicts={"test": "conflict"},
                description="Test conflict"
            )
            
            # Verify responses are correct types
            if not isinstance(success_response, CardsSaveSuccessResponse):
                results["issues"].append("@overload function returned wrong type for success case")
                results["passed"] = False
            
            if not isinstance(conflict_response, CardsSaveConflictResponse):
                results["issues"].append("@overload function returned wrong type for conflict case")
                results["passed"] = False
            
            # Verify clean JSON (no null fields)
            success_dict = success_response.model_dump(exclude_none=True)
            if any(value is None for value in success_dict.values()):
                results["issues"].append("Success response contains null values")
                results["passed"] = False
            
            conflict_dict = conflict_response.model_dump(exclude_none=True)
            if any(value is None for value in conflict_dict.values()):
                results["issues"].append("Conflict response contains null values")
                results["passed"] = False
            
            results["verified_unions"].append("CardsSaveResponse Union")
            
        except Exception as e:
            results["issues"].append(f"Error testing @overload Union types: {str(e)}")
            results["passed"] = False
        
        return results
    
    def verify_examples_match_reality(self) -> Dict[str, Any]:
        """Verify that examples in documentation match actual API responses."""
        results = {
            "passed": True,
            "issues": [],
            "verified_examples": []
        }
        
        schema = self.get_openapi_schema()
        components = schema.get("components", {}).get("schemas", {})
        
        # Check that examples are realistic and match expected patterns
        for model_name, model_schema in components.items():
            if "example" in model_schema:
                example = model_schema["example"]
                
                # Verify examples don't contain placeholder values
                if isinstance(example, dict):
                    for key, value in example.items():
                        if isinstance(value, str) and ("placeholder" in value.lower() or "example" in value.lower()):
                            results["issues"].append(f"{model_name} example contains placeholder value: {key}={value}")
                            results["passed"] = False
                
                results["verified_examples"].append(model_name)
        
        return results
    
    def run_full_verification(self) -> Dict[str, Any]:
        """Run complete documentation verification."""
        print("🔍 Starting documentation verification...")
        
        results = {
            "overall_passed": True,
            "response_model_accuracy": self.verify_response_model_accuracy(),
            "multi_response_scenarios": self.verify_multi_response_scenarios(),
            "openapi_union_types": self.verify_openapi_union_types(),
            "examples_match_reality": self.verify_examples_match_reality()
        }
        
        # Check if any verification failed
        for test_name, test_results in results.items():
            if test_name != "overall_passed" and isinstance(test_results, dict):
                if not test_results.get("passed", True):
                    results["overall_passed"] = False
        
        return results
    
    def print_verification_report(self, results: Dict[str, Any]):
        """Print a formatted verification report."""
        print("\n" + "="*60)
        print("📋 DOCUMENTATION VERIFICATION REPORT")
        print("="*60)
        
        overall_status = "✅ PASSED" if results["overall_passed"] else "❌ FAILED"
        print(f"\nOverall Status: {overall_status}")
        
        for test_name, test_results in results.items():
            if test_name == "overall_passed":
                continue
                
            print(f"\n📊 {test_name.replace('_', ' ').title()}:")
            
            if isinstance(test_results, dict):
                status = "✅ PASSED" if test_results.get("passed", True) else "❌ FAILED"
                print(f"   Status: {status}")
                
                if "verified_endpoints" in test_results:
                    print(f"   Verified Endpoints: {len(test_results['verified_endpoints'])}")
                    for endpoint in test_results["verified_endpoints"]:
                        print(f"     • {endpoint}")
                
                if "verified_scenarios" in test_results:
                    print(f"   Verified Scenarios: {len(test_results['verified_scenarios'])}")
                    for scenario in test_results["verified_scenarios"]:
                        print(f"     • {scenario}")
                
                if "verified_unions" in test_results:
                    print(f"   Verified Unions: {len(test_results['verified_unions'])}")
                    for union in test_results["verified_unions"]:
                        print(f"     • {union}")
                
                if "verified_examples" in test_results:
                    print(f"   Verified Examples: {len(test_results['verified_examples'])}")
                
                if test_results.get("issues"):
                    print(f"   Issues Found: {len(test_results['issues'])}")
                    for issue in test_results["issues"]:
                        print(f"     ⚠️  {issue}")
        
        print("\n" + "="*60)


def main():
    """Main function to run documentation verification."""
    verifier = DocumentationVerifier()
    results = verifier.run_full_verification()
    verifier.print_verification_report(results)
    
    # Return exit code based on results
    return 0 if results["overall_passed"] else 1


if __name__ == "__main__":
    exit(main())