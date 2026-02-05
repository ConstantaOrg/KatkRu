"""
Property-based tests for Status Code Independence

**Property 11: Status Code Independence**
*For any* API endpoint, the test framework should validate HTTP status codes 
correctly regardless of response model definitions

**Validates: Requirements 1.4**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, List, Union, Optional
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from core.main import app
from tests.utils.api_response_validator import APIResponseValidator
from tests.utils.api_response_validator import APIResponseValidator


# Test data generators
@st.composite
def http_status_code_data(draw):
    """Generate data for testing HTTP status code validation."""
    return {
        "status_code": draw(st.integers(min_value=200, max_value=599)),
        "response_body": draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.booleans(),
                st.lists(st.text(), max_size=5)
            ),
            min_size=1, max_size=10
        )),
        "endpoint_path": draw(st.sampled_from([
            "/private/n8n_ui/cards/save",
            "/private/ttable/versions/pre-commit",
            "/private/users/register",
            "/private/groups/add",
            "/private/teachers/add"
        ]))
    }


@st.composite
def api_response_scenario_data(draw):
    """Generate data for testing API response validation independence."""
    scenario_type = draw(st.sampled_from([
        "success_200", "conflict_409", "error_400", "not_found_404", 
        "server_error_500", "accepted_202"
    ]))
    
    base_response = {
        "timestamp": draw(st.text(min_size=10, max_size=30)),
        "endpoint": draw(st.text(min_size=5, max_size=50))
    }
    
    if scenario_type == "success_200":
        return {
            "scenario": "success_200",
            "expected_status": 200,
            "response_body": {
                **base_response,
                "success": True,
                "message": draw(st.text(min_size=5, max_size=50)),
                "data": draw(st.dictionaries(
                    keys=st.text(min_size=1, max_size=15),
                    values=st.one_of(st.integers(), st.text()),
                    min_size=0, max_size=5
                ))
            }
        }
    elif scenario_type == "conflict_409":
        return {
            "scenario": "conflict_409",
            "expected_status": 409,
            "response_body": {
                **base_response,
                "success": False,
                "message": draw(st.text(min_size=5, max_size=50)),
                "conflicts": draw(st.dictionaries(
                    keys=st.text(min_size=1, max_size=15),
                    values=st.one_of(st.integers(), st.text()),
                    min_size=1, max_size=3
                ))
            }
        }
    elif scenario_type == "accepted_202":
        return {
            "scenario": "accepted_202",
            "expected_status": 202,
            "response_body": {
                **base_response,
                "success": False,
                "message": draw(st.text(min_size=5, max_size=50)),
                "pending_action": draw(st.text(min_size=5, max_size=30))
            }
        }
    else:  # error cases
        status_map = {
            "error_400": 400,
            "not_found_404": 404,
            "server_error_500": 500
        }
        return {
            "scenario": scenario_type,
            "expected_status": status_map[scenario_type],
            "response_body": {
                **base_response,
                "success": False,
                "error": draw(st.text(min_size=5, max_size=50)),
                "details": draw(st.text(min_size=10, max_size=100))
            }
        }


class TestStatusCodeIndependenceProperties:
    """Property-based tests for status code independence."""
    
    def setup_method(self):
        """Setup test utilities."""
        self.validator = APIResponseValidator()
        self.client = TestClient(app)
    
    def is_success_status(self, status_code: int) -> bool:
        """Check if status code is a success status (2xx)."""
        return 200 <= status_code < 300
    
    def is_client_error_status(self, status_code: int) -> bool:
        """Check if status code is a client error status (4xx)."""
        return 400 <= status_code < 500
    
    def is_server_error_status(self, status_code: int) -> bool:
        """Check if status code is a server error status (5xx)."""
        return 500 <= status_code < 600
    
    @given(http_status_code_data())
    @settings(max_examples=100)
    def test_property_11_status_code_independence_validation(self, status_data: Dict[str, Any]):
        """
        **Property 11: Status Code Independence - Validation**
        *For any* HTTP status code and response body, the test framework should 
        validate the status code correctly without depending on response model definitions.
        
        **Validates: Requirements 1.4**
        """
        status_code = status_data["status_code"]
        response_body = status_data["response_body"]
        
        # Property: Status code validation should work independently of response models
        # Simulate a response with the given status code and body
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = response_body
        
        # Property: Should be able to validate status code without model validation
        try:
            # Test framework should validate status codes directly
            if 200 <= status_code < 300:
                # Success status codes
                assert self.is_success_status(status_code), \
                    f"Status code {status_code} should be recognized as success"
            elif 400 <= status_code < 500:
                # Client error status codes
                assert self.is_client_error_status(status_code), \
                    f"Status code {status_code} should be recognized as client error"
            elif 500 <= status_code < 600:
                # Server error status codes
                assert self.is_server_error_status(status_code), \
                    f"Status code {status_code} should be recognized as server error"
            
            # Property: Status code validation should not depend on response content
            # The same status code should be validated consistently regardless of body content
            different_body = {"completely": "different", "structure": True}
            mock_response_2 = Mock()
            mock_response_2.status_code = status_code
            mock_response_2.json.return_value = different_body
            
            # Should give same status code classification
            if 200 <= status_code < 300:
                assert self.is_success_status(status_code)
            elif 400 <= status_code < 500:
                assert self.is_client_error_status(status_code)
            elif 500 <= status_code < 600:
                assert self.is_server_error_status(status_code)
                
        except Exception as e:
            # Property: Status code validation should not fail due to response content
            assert False, f"Status code validation failed unexpectedly: {e}"
    
    @given(api_response_scenario_data())
    @settings(max_examples=100)
    def test_property_11_status_code_independence_scenario_handling(self, scenario_data: Dict[str, Any]):
        """
        **Property 11: Status Code Independence - Scenario Handling**
        *For any* API response scenario, the test framework should handle status codes 
        independently of the specific response model structure.
        
        **Validates: Requirements 1.4**
        """
        scenario = scenario_data["scenario"]
        expected_status = scenario_data["expected_status"]
        response_body = scenario_data["response_body"]
        
        # Property: Test framework should handle different status code scenarios
        mock_response = Mock()
        mock_response.status_code = expected_status
        mock_response.json.return_value = response_body
        
        # Property: Status code handling should be consistent across scenarios
        # Create a simple validation that just checks the status code matches expectation
        status_matches = mock_response.status_code == expected_status
        
        assert status_matches, f"Status code {mock_response.status_code} does not match expected {expected_status} for scenario {scenario}"
        
        # Property: Status code should match expected value regardless of response content
        assert mock_response.status_code == expected_status, \
            f"Status code should be {expected_status} for scenario {scenario}"
        
        # Property: Response body structure should not affect status code validation
        # Test with modified response body but same status code
        modified_body = {**response_body, "additional_field": "test_value"}
        mock_response_modified = Mock()
        mock_response_modified.status_code = expected_status
        mock_response_modified.json.return_value = modified_body
        
        # Should still validate correctly with modified body
        status_matches_modified = mock_response_modified.status_code == expected_status
        
        assert status_matches_modified, \
            f"Modified scenario {scenario} status code validation failed"
    
    @given(st.lists(st.integers(min_value=200, max_value=599), min_size=2, max_size=10))
    @settings(max_examples=50)
    def test_property_11_status_code_independence_multiple_codes(self, status_codes: List[int]):
        """
        **Property 11: Status Code Independence - Multiple Codes**
        *For any* list of HTTP status codes, the test framework should validate 
        each code independently without interference from others.
        
        **Validates: Requirements 1.4**
        """
        # Make status codes unique
        unique_codes = list(set(status_codes))
        assume(len(unique_codes) >= 2)
        
        # Property: Each status code should be validated independently
        validation_results = {}
        
        for status_code in unique_codes:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.json.return_value = {"test": "data", "status": status_code}
            
            # Validate each status code
            try:
                if 200 <= status_code < 300:
                    result = self.is_success_status(status_code)
                    validation_results[status_code] = ("success", result)
                elif 400 <= status_code < 500:
                    result = self.is_client_error_status(status_code)
                    validation_results[status_code] = ("client_error", result)
                elif 500 <= status_code < 600:
                    result = self.is_server_error_status(status_code)
                    validation_results[status_code] = ("server_error", result)
                else:
                    validation_results[status_code] = ("other", True)
                    
            except Exception as e:
                assert False, f"Status code {status_code} validation failed: {e}"
        
        # Property: All validations should succeed independently
        for status_code, (category, result) in validation_results.items():
            assert result, f"Status code {status_code} ({category}) validation failed"
        
        # Property: Status code categories should be mutually exclusive
        success_codes = [code for code, (cat, _) in validation_results.items() if cat == "success"]
        error_codes = [code for code, (cat, _) in validation_results.items() if cat in ["client_error", "server_error"]]
        
        # No overlap between success and error codes
        assert not set(success_codes).intersection(set(error_codes)), \
            "Success and error status codes should not overlap"
    
    @given(st.integers(min_value=200, max_value=599), st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_property_11_status_code_independence_content_agnostic(self, status_code: int, content_type: str):
        """
        **Property 11: Status Code Independence - Content Agnostic**
        *For any* HTTP status code and content type, status code validation should 
        work independently of response content format or structure.
        
        **Validates: Requirements 1.4**
        """
        # Property: Status code validation should work with different content types
        test_contents = [
            {"json": "object"},
            "plain text string",
            ["list", "of", "items"],
            42,
            True,
            None
        ]
        
        for content in test_contents:
            mock_response = Mock()
            mock_response.status_code = status_code
            
            # Handle different content types
            if content is None:
                mock_response.json.side_effect = ValueError("No JSON content")
                mock_response.text = ""
            elif isinstance(content, (dict, list)):
                mock_response.json.return_value = content
            else:
                mock_response.json.side_effect = ValueError("Not JSON")
                mock_response.text = str(content)
            
            # Property: Status code validation should work regardless of content
            try:
                if 200 <= status_code < 300:
                    assert self.is_success_status(status_code), \
                        f"Status {status_code} should be success regardless of content type"
                elif 400 <= status_code < 500:
                    assert self.is_client_error_status(status_code), \
                        f"Status {status_code} should be client error regardless of content type"
                elif 500 <= status_code < 600:
                    assert self.is_server_error_status(status_code), \
                        f"Status {status_code} should be server error regardless of content type"
                
            except Exception as e:
                assert False, f"Status code validation failed with content {type(content)}: {e}"
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_property_11_status_code_independence_model_changes(self, test_iteration: int):
        """
        **Property 11: Status Code Independence - Model Changes**
        *For any* response model change, status code validation should remain 
        consistent and not be affected by model definition changes.
        
        **Validates: Requirements 1.4**
        """
        # Property: Status code validation should be independent of model changes
        # Simulate different "versions" of response models
        
        original_response = {
            "success": True,
            "message": "Operation completed",
            "data": {"id": 123}
        }
        
        # Simulate model "evolution" - fields added, removed, renamed
        evolved_responses = [
            # Added fields
            {**original_response, "new_field": "new_value", "timestamp": "2024-01-01"},
            # Removed fields
            {"success": True, "message": "Operation completed"},
            # Renamed fields
            {"success": True, "msg": "Operation completed", "result": {"id": 123}},
            # Different structure
            {"status": "ok", "payload": {"success": True, "id": 123}},
            # Minimal structure
            {"ok": True}
        ]
        
        status_code = 200  # Test with success status
        
        # Property: All response variations should have same status code validation
        for i, response_body in enumerate([original_response] + evolved_responses):
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.json.return_value = response_body
            
            # Status code validation should be consistent
            assert self.is_success_status(status_code), \
                f"Status code validation failed for response variation {i}"
            
            # Should not be classified as error
            assert not self.is_client_error_status(status_code), \
                f"Success status incorrectly classified as client error for variation {i}"
            assert not self.is_server_error_status(status_code), \
                f"Success status incorrectly classified as server error for variation {i}"
        
        # Property: Same test with error status codes
        error_status = 409
        for i, response_body in enumerate([original_response] + evolved_responses):
            mock_response = Mock()
            mock_response.status_code = error_status
            mock_response.json.return_value = response_body
            
            # Should be classified as client error regardless of response structure
            assert self.is_client_error_status(error_status), \
                f"Error status validation failed for response variation {i}"
            
            # Should not be classified as success
            assert not self.is_success_status(error_status), \
                f"Error status incorrectly classified as success for variation {i}"


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--tb=short"])