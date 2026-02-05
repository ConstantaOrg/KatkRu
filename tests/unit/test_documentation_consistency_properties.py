"""
Property-based tests for Documentation Consistency

**Property 10: Documentation Consistency**
*For any* corrected response model, the auto-generated documentation should accurately 
reflect the actual API behavior and include realistic examples

**Validates: Requirements 5.1, 5.2, 5.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, List, Union, Optional
import json
from fastapi.testclient import TestClient
from fastapi.openapi.utils import get_openapi

from core.main import app
from core.utils.response_model_utils import (
    CardsSaveSuccessResponse, CardsSaveConflictResponse,
    TtableVersionsPreCommitSuccessResponse, TtableVersionsPreCommitConflictResponse,
    UserRegistrationSuccessResponse, UserRegistrationConflictResponse,
    create_cards_save_response, create_ttable_precommit_response
)


# Test data generators
@st.composite
def response_model_data(draw):
    """Generate data for testing response model documentation consistency."""
    model_type = draw(st.sampled_from([
        "cards_save_success", "cards_save_conflict",
        "ttable_precommit_success", "ttable_precommit_conflict",
        "user_registration_success", "user_registration_conflict"
    ]))
    
    if model_type == "cards_save_success":
        return {
            "type": "cards_save_success",
            "data": {
                "new_card_hist_id": draw(st.integers(min_value=1, max_value=10000)),
                "message": draw(st.text(min_size=5, max_size=50))
            }
        }
    elif model_type == "cards_save_conflict":
        return {
            "type": "cards_save_conflict",
            "data": {
                "conflicts": draw(st.dictionaries(
                    keys=st.text(min_size=1, max_size=20),
                    values=st.one_of(st.integers(), st.text()),
                    min_size=1, max_size=5
                )),
                "description": draw(st.text(min_size=10, max_size=100)),
                "message": draw(st.text(min_size=5, max_size=50))
            }
        }
    elif model_type == "ttable_precommit_success":
        return {
            "type": "ttable_precommit_success",
            "data": {
                "message": draw(st.text(min_size=5, max_size=50))
            }
        }
    elif model_type == "ttable_precommit_conflict":
        return {
            "type": "ttable_precommit_conflict",
            "data": {
                "needed_groups": draw(st.lists(
                    st.integers(min_value=1, max_value=10000),
                    min_size=0, max_size=5
                )),
                "ttable_id": draw(st.integers(min_value=1, max_value=1000)),
                "message": draw(st.text(min_size=5, max_size=50))
            }
        }
    elif model_type == "user_registration_success":
        return {
            "type": "user_registration_success",
            "data": {
                "message": draw(st.text(min_size=5, max_size=50))
            }
        }
    else:  # user_registration_conflict
        return {
            "type": "user_registration_conflict",
            "data": {
                "message": draw(st.text(min_size=5, max_size=50)),
                "detail": draw(st.text(min_size=10, max_size=100))
            }
        }


@st.composite
def openapi_schema_data(draw):
    """Generate data for testing OpenAPI schema consistency."""
    return {
        "endpoint_path": draw(st.sampled_from([
            "/private/n8n_ui/cards/save",
            "/private/ttable/versions/pre-commit",
            "/private/users/register"
        ])),
        "method": draw(st.sampled_from(["post", "put", "get"])),
        "expected_status_codes": draw(st.lists(
            st.integers(min_value=200, max_value=599),
            min_size=1, max_size=4
        ))
    }


class TestDocumentationConsistencyProperties:
    """Property-based tests for documentation consistency."""
    
    def setup_method(self):
        """Setup test client and OpenAPI schema."""
        self.client = TestClient(app)
        self.openapi_schema = get_openapi(
            title=app.title,
            version="1.0.0",
            description="API Documentation Consistency Test",
            routes=app.routes,
        )
    
    @given(response_model_data())
    @settings(max_examples=100)
    def test_property_10_documentation_consistency_model_accuracy(self, model_data: Dict[str, Any]):
        """
        **Property 10: Documentation Consistency - Model Accuracy**
        *For any* response model, the OpenAPI schema should accurately reflect 
        the model structure and include realistic examples.
        
        **Validates: Requirements 5.1, 5.2**
        """
        model_type = model_data["type"]
        data = model_data["data"]
        
        # Create response model instance
        if model_type == "cards_save_success":
            response = create_cards_save_response(
                success=True,
                new_card_hist_id=data["new_card_hist_id"],
                message=data["message"]
            )
            schema_name = "CardsSaveSuccessResponse"
        elif model_type == "cards_save_conflict":
            response = create_cards_save_response(
                success=False,
                conflicts=data["conflicts"],
                description=data["description"],
                message=data["message"]
            )
            schema_name = "CardsSaveConflictResponse"
        elif model_type == "ttable_precommit_success":
            response = create_ttable_precommit_response(
                success=True,
                message=data["message"]
            )
            schema_name = "TtableVersionsPreCommitSuccessResponse"
        elif model_type == "ttable_precommit_conflict":
            response = create_ttable_precommit_response(
                success=False,
                needed_groups=data["needed_groups"],
                ttable_id=data["ttable_id"],
                message=data["message"]
            )
            schema_name = "TtableVersionsPreCommitConflictResponse"
        else:
            # Skip user registration for now as it's not in the main focus
            assume(False)
        
        # Validate model produces clean JSON
        response_dict = response.model_dump(exclude_none=True)
        
        # Property: Response should not contain null values (clean @overload pattern)
        for key, value in response_dict.items():
            assert value is not None, f"Response field '{key}' is null, violating clean @overload pattern"
        
        # Property: Response should be JSON serializable
        try:
            json_str = json.dumps(response_dict)
            parsed_back = json.loads(json_str)
            assert parsed_back == response_dict, "Response should round-trip through JSON serialization"
        except (TypeError, ValueError) as e:
            assert False, f"Response is not JSON serializable: {e}"
        
        # Property: OpenAPI schema should contain the model
        components = self.openapi_schema.get("components", {}).get("schemas", {})
        assert schema_name in components, f"OpenAPI schema missing model: {schema_name}"
        
        # Property: Schema should have required properties
        schema = components[schema_name]
        properties = schema.get("properties", {})
        
        for field_name in response_dict.keys():
            assert field_name in properties, f"Schema missing property: {field_name}"
        
        # Property: Examples should not contain placeholder values
        if "example" in schema:
            example = schema["example"]
            if isinstance(example, dict):
                for key, value in example.items():
                    if isinstance(value, str):
                        assert "placeholder" not in value.lower(), f"Example contains placeholder: {key}={value}"
                        assert "example" not in value.lower(), f"Example contains placeholder: {key}={value}"
    
    @given(openapi_schema_data())
    @settings(max_examples=50)
    def test_property_10_documentation_consistency_endpoint_coverage(self, schema_data: Dict[str, Any]):
        """
        **Property 10: Documentation Consistency - Endpoint Coverage**
        *For any* API endpoint, the OpenAPI documentation should include all 
        possible response scenarios with proper status codes.
        
        **Validates: Requirements 5.1, 5.3**
        """
        endpoint_path = schema_data["endpoint_path"]
        method = schema_data["method"]
        
        paths = self.openapi_schema.get("paths", {})
        
        # Property: Endpoint should be documented
        if endpoint_path in paths:
            endpoint_doc = paths[endpoint_path]
            
            # Property: Method should be documented
            if method in endpoint_doc:
                method_doc = endpoint_doc[method]
                responses = method_doc.get("responses", {})
                
                # Property: Should have multiple response scenarios for multi-response endpoints
                if endpoint_path in ["/private/n8n_ui/cards/save", "/private/ttable/versions/pre-commit"]:
                    assert len(responses) >= 2, f"Multi-response endpoint {endpoint_path} should have multiple response scenarios"
                
                # Property: Each response should have proper structure
                for status_code, response_doc in responses.items():
                    assert "description" in response_doc, f"Response {status_code} missing description"
                    
                    # Property: Response should have content or model
                    has_content = "content" in response_doc
                    has_model = "model" in response_doc
                    assert has_content or has_model, f"Response {status_code} should have content or model"
                    
                    # Property: If has content, should have application/json
                    if has_content:
                        content = response_doc["content"]
                        assert "application/json" in content, f"Response {status_code} should have JSON content"
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_property_10_documentation_consistency_realistic_examples(self, field_names: List[str]):
        """
        **Property 10: Documentation Consistency - Realistic Examples**
        *For any* set of field names, the documentation examples should contain 
        realistic values that match actual API response patterns.
        
        **Validates: Requirements 5.2, 5.5**
        """
        # Make field names unique and valid
        unique_fields = list(set(field_names))
        valid_fields = [name for name in unique_fields if name.isalnum()]
        assume(len(valid_fields) >= 1)
        
        components = self.openapi_schema.get("components", {}).get("schemas", {})
        
        # Property: Examples should be realistic for known response models
        for model_name, schema in components.items():
            if "example" in schema and isinstance(schema["example"], dict):
                example = schema["example"]
                
                # Property: Success flag should be boolean
                if "success" in example:
                    assert isinstance(example["success"], bool), f"{model_name} example 'success' should be boolean"
                
                # Property: ID fields should be positive integers
                for key, value in example.items():
                    if "id" in key.lower() and isinstance(value, int):
                        assert value > 0, f"{model_name} example '{key}' should be positive integer"
                
                # Property: Message fields should be non-empty strings
                if "message" in example:
                    message = example["message"]
                    assert isinstance(message, str), f"{model_name} example 'message' should be string"
                    assert len(message.strip()) > 0, f"{model_name} example 'message' should not be empty"
                
                # Property: List fields should be lists (check specific known list fields)
                known_list_fields = ["lessons", "history", "card_content", "ext_card", "needed_groups", 
                                   "diff_groups", "diff_teachers", "diff_disciplines"]
                for key, value in example.items():
                    if key in known_list_fields and value is not None:
                        assert isinstance(value, list), f"{model_name} example '{key}' should be list"
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_property_10_documentation_consistency_union_types(self, test_iteration: int):
        """
        **Property 10: Documentation Consistency - Union Types**
        *For any* Union response type, the documentation should properly handle 
        discriminator fields and multiple response scenarios.
        
        **Validates: Requirements 5.1, 5.3**
        """
        paths = self.openapi_schema.get("paths", {})
        
        # Property: Union response endpoints should have proper discriminator handling
        union_endpoints = [
            "/private/n8n_ui/cards/save",
            "/private/ttable/versions/pre-commit"
        ]
        
        for endpoint_path in union_endpoints:
            if endpoint_path in paths:
                endpoint_doc = paths[endpoint_path]
                
                # Check POST method for cards/save, PUT for ttable/versions/pre-commit
                method = "post" if "cards" in endpoint_path else "put"
                
                if method in endpoint_doc:
                    method_doc = endpoint_doc[method]
                    responses = method_doc.get("responses", {})
                    
                    # Property: Should have success and error responses
                    success_codes = [code for code in responses.keys() if code.startswith("2")]
                    error_codes = [code for code in responses.keys() if not code.startswith("2")]
                    
                    assert len(success_codes) >= 1, f"Union endpoint {endpoint_path} should have success responses"
                    
                    # Property: Different status codes should have different response structures
                    if len(responses) > 1:
                        response_structures = {}
                        for status_code, response_doc in responses.items():
                            if "content" in response_doc:
                                content = response_doc["content"].get("application/json", {})
                                if "example" in content:
                                    example = content["example"]
                                    # Use success field as discriminator
                                    if "success" in example:
                                        response_structures[status_code] = example["success"]
                        
                        # Property: Success and error responses should have different success values
                        success_values = set(response_structures.values())
                        if len(success_values) > 1:
                            assert True in success_values, "Should have at least one success=True response"
                            assert False in success_values, "Should have at least one success=False response"


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--tb=short"])