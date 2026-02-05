"""
Property-based tests for @overload Response Models

These tests validate the correctness properties of the @overload response model framework,
ensuring clean response generation without inheritance-based field pollution.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, List, Union
import json

from core.utils.response_model_utils import (
    CardsSaveResponse,
    CardsSaveSuccessResponse, 
    CardsSaveConflictResponse,
    create_cards_save_response,
    TtableVersionsPreCommitResponse,
    TtableVersionsPreCommitSuccessResponse,
    TtableVersionsPreCommitConflictResponse,
    create_ttable_precommit_response,
    create_response_json
)
from core.utils.overload_response_framework import (
    ResponseModelFramework,
    create_binary_response_models
)


# Generators for test data
@st.composite
def cards_save_success_data(draw):
    """Generate valid data for cards save success responses."""
    return {
        'new_card_hist_id': draw(st.integers(min_value=1, max_value=10000)),
        'message': draw(st.text(min_size=1, max_size=100))
    }


@st.composite
def cards_save_conflict_data(draw):
    """Generate valid data for cards save conflict responses."""
    return {
        'conflicts': draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.integers(), st.text(), st.lists(st.integers(), max_size=5)),
            min_size=1, max_size=5
        )),
        'description': draw(st.text(min_size=1, max_size=200)),
        'message': draw(st.text(min_size=1, max_size=100))
    }


@st.composite
def ttable_precommit_success_data(draw):
    """Generate valid data for ttable precommit success responses."""
    return {
        'message': draw(st.text(min_size=1, max_size=100))
    }


@st.composite
def ttable_precommit_conflict_data(draw):
    """Generate valid data for ttable precommit conflict responses."""
    return {
        'needed_groups': draw(st.lists(st.integers(min_value=1, max_value=10000), min_size=1, max_size=10)),
        'ttable_id': draw(st.integers(min_value=1, max_value=10000)),
        'message': draw(st.text(min_size=1, max_size=100))
    }


class TestOverloadResponseModelProperties:
    """Property-based tests for @overload response models."""
    
    @given(cards_save_success_data())
    @settings(max_examples=100)
    def test_property_4_overload_response_model_correctness_cards_success(self, success_data: Dict[str, Any]):
        """
        **Property 4: Overload Response Model Correctness - Cards Save Success**
        
        For any valid success data, the @overload function should create a clean response model
        without null fields and with precise typing.
        
        **Validates: Requirements 2.2, 2.4, 5.1**
        """
        # Use @overload function to create response
        response = create_cards_save_response(
            success=True,
            new_card_hist_id=success_data['new_card_hist_id'],
            message=success_data.get('message', "Card saved successfully")
        )
        
        # Property: Response should be of correct type
        assert isinstance(response, CardsSaveSuccessResponse), (
            f"Expected CardsSaveSuccessResponse, got {type(response)}"
        )
        
        # Property: Response should have success=True
        assert response.success is True, "Success response should have success=True"
        
        # Property: Response should contain all required fields
        assert hasattr(response, 'new_card_hist_id'), "Success response should have new_card_hist_id"
        assert hasattr(response, 'message'), "Success response should have message"
        assert hasattr(response, 'success'), "Success response should have success"
        
        # Property: Response should have correct field values
        assert response.new_card_hist_id == success_data['new_card_hist_id'], (
            f"Expected new_card_hist_id {success_data['new_card_hist_id']}, got {response.new_card_hist_id}"
        )
        
        # Property: JSON serialization should not contain null fields
        json_response = create_response_json(response)
        json_content = json.loads(json_response.body.decode())
        
        # Should not have null/None values
        null_fields = [k for k, v in json_content.items() if v is None]
        assert len(null_fields) == 0, f"Response should not contain null fields: {null_fields}"
        
        # Should not have conflict-related fields
        conflict_fields = ['conflicts', 'description']
        present_conflict_fields = [f for f in conflict_fields if f in json_content]
        assert len(present_conflict_fields) == 0, (
            f"Success response should not contain conflict fields: {present_conflict_fields}"
        )
        
        # Property: Should contain exactly the expected fields
        expected_fields = {'success', 'message', 'new_card_hist_id'}
        actual_fields = set(json_content.keys())
        assert actual_fields == expected_fields, (
            f"Expected fields {expected_fields}, got {actual_fields}"
        )
    
    @given(cards_save_conflict_data())
    @settings(max_examples=100)
    def test_property_4_overload_response_model_correctness_cards_conflict(self, conflict_data: Dict[str, Any]):
        """
        **Property 4: Overload Response Model Correctness - Cards Save Conflict**
        
        For any valid conflict data, the @overload function should create a clean response model
        without null fields and with precise typing.
        
        **Validates: Requirements 2.2, 2.4, 5.1**
        """
        # Use @overload function to create response
        response = create_cards_save_response(
            success=False,
            conflicts=conflict_data['conflicts'],
            description=conflict_data['description'],
            message=conflict_data.get('message', "Conflicts detected during save")
        )
        
        # Property: Response should be of correct type
        assert isinstance(response, CardsSaveConflictResponse), (
            f"Expected CardsSaveConflictResponse, got {type(response)}"
        )
        
        # Property: Response should have success=False
        assert response.success is False, "Conflict response should have success=False"
        
        # Property: Response should contain all required fields
        assert hasattr(response, 'conflicts'), "Conflict response should have conflicts"
        assert hasattr(response, 'description'), "Conflict response should have description"
        assert hasattr(response, 'message'), "Conflict response should have message"
        assert hasattr(response, 'success'), "Conflict response should have success"
        
        # Property: Response should have correct field values
        assert response.conflicts == conflict_data['conflicts'], (
            f"Expected conflicts {conflict_data['conflicts']}, got {response.conflicts}"
        )
        assert response.description == conflict_data['description'], (
            f"Expected description {conflict_data['description']}, got {response.description}"
        )
        
        # Property: JSON serialization should not contain null fields
        json_response = create_response_json(response)
        json_content = json.loads(json_response.body.decode())
        
        # Should not have null/None values
        null_fields = [k for k, v in json_content.items() if v is None]
        assert len(null_fields) == 0, f"Response should not contain null fields: {null_fields}"
        
        # Should not have success-related fields
        success_fields = ['new_card_hist_id']
        present_success_fields = [f for f in success_fields if f in json_content]
        assert len(present_success_fields) == 0, (
            f"Conflict response should not contain success fields: {present_success_fields}"
        )
        
        # Property: Should contain exactly the expected fields
        expected_fields = {'success', 'message', 'conflicts', 'description'}
        actual_fields = set(json_content.keys())
        assert actual_fields == expected_fields, (
            f"Expected fields {expected_fields}, got {actual_fields}"
        )
    
    @given(ttable_precommit_success_data())
    @settings(max_examples=100)
    def test_property_4_overload_response_model_correctness_ttable_success(self, success_data: Dict[str, Any]):
        """
        **Property 4: Overload Response Model Correctness - Ttable PreCommit Success**
        
        For any valid success data, the @overload function should create a clean response model
        without null fields and with precise typing.
        
        **Validates: Requirements 2.2, 2.4, 5.1**
        """
        # Use @overload function to create response
        response = create_ttable_precommit_response(
            success=True,
            message=success_data.get('message', "Timetable version ready for commit")
        )
        
        # Property: Response should be of correct type
        assert isinstance(response, TtableVersionsPreCommitSuccessResponse), (
            f"Expected TtableVersionsPreCommitSuccessResponse, got {type(response)}"
        )
        
        # Property: Response should have success=True
        assert response.success is True, "Success response should have success=True"
        
        # Property: JSON serialization should not contain null fields
        json_response = create_response_json(response)
        json_content = json.loads(json_response.body.decode())
        
        # Should not have null/None values
        null_fields = [k for k, v in json_content.items() if v is None]
        assert len(null_fields) == 0, f"Response should not contain null fields: {null_fields}"
        
        # Should not have conflict-related fields
        conflict_fields = ['needed_groups', 'ttable_id']
        present_conflict_fields = [f for f in conflict_fields if f in json_content]
        assert len(present_conflict_fields) == 0, (
            f"Success response should not contain conflict fields: {present_conflict_fields}"
        )
        
        # Property: Should contain exactly the expected fields
        expected_fields = {'success', 'message'}
        actual_fields = set(json_content.keys())
        assert actual_fields == expected_fields, (
            f"Expected fields {expected_fields}, got {actual_fields}"
        )
    
    @given(ttable_precommit_conflict_data())
    @settings(max_examples=100)
    def test_property_4_overload_response_model_correctness_ttable_conflict(self, conflict_data: Dict[str, Any]):
        """
        **Property 4: Overload Response Model Correctness - Ttable PreCommit Conflict**
        
        For any valid conflict data, the @overload function should create a clean response model
        without null fields and with precise typing.
        
        **Validates: Requirements 2.2, 2.4, 5.1**
        """
        # Use @overload function to create response
        response = create_ttable_precommit_response(
            success=False,
            needed_groups=conflict_data['needed_groups'],
            ttable_id=conflict_data['ttable_id'],
            message=conflict_data.get('message', "Conflicts detected in timetable version")
        )
        
        # Property: Response should be of correct type
        assert isinstance(response, TtableVersionsPreCommitConflictResponse), (
            f"Expected TtableVersionsPreCommitConflictResponse, got {type(response)}"
        )
        
        # Property: Response should have success=False
        assert response.success is False, "Conflict response should have success=False"
        
        # Property: Response should have correct field values
        assert response.needed_groups == conflict_data['needed_groups'], (
            f"Expected needed_groups {conflict_data['needed_groups']}, got {response.needed_groups}"
        )
        assert response.ttable_id == conflict_data['ttable_id'], (
            f"Expected ttable_id {conflict_data['ttable_id']}, got {response.ttable_id}"
        )
        
        # Property: JSON serialization should not contain null fields
        json_response = create_response_json(response)
        json_content = json.loads(json_response.body.decode())
        
        # Should not have null/None values
        null_fields = [k for k, v in json_content.items() if v is None]
        assert len(null_fields) == 0, f"Response should not contain null fields: {null_fields}"
        
        # Property: Should contain exactly the expected fields
        expected_fields = {'success', 'message', 'needed_groups', 'ttable_id'}
        actual_fields = set(json_content.keys())
        assert actual_fields == expected_fields, (
            f"Expected fields {expected_fields}, got {actual_fields}"
        )
    
    @given(st.booleans(), st.integers(min_value=1, max_value=10000))
    @settings(max_examples=100)
    def test_property_overload_type_safety(self, success: bool, card_id: int):
        """
        **Property: Overload Type Safety**
        
        For any boolean success flag, the @overload function should return the correct
        response type and the type system should provide accurate type hints.
        
        **Validates: Requirements 2.2, 5.1**
        """
        if success:
            # Test success path
            response = create_cards_save_response(
                success=True,
                new_card_hist_id=card_id
            )
            
            # Property: Should return success response type
            assert isinstance(response, CardsSaveSuccessResponse)
            assert not isinstance(response, CardsSaveConflictResponse)
            
            # Property: Should have success-specific fields
            assert hasattr(response, 'new_card_hist_id')
            assert response.new_card_hist_id == card_id
            
        else:
            # Test conflict path
            test_conflicts = {"test": "conflict"}
            test_description = "Test conflict description"
            
            response = create_cards_save_response(
                success=False,
                conflicts=test_conflicts,
                description=test_description
            )
            
            # Property: Should return conflict response type
            assert isinstance(response, CardsSaveConflictResponse)
            assert not isinstance(response, CardsSaveSuccessResponse)
            
            # Property: Should have conflict-specific fields
            assert hasattr(response, 'conflicts')
            assert hasattr(response, 'description')
            assert response.conflicts == test_conflicts
            assert response.description == test_description
    
    @given(st.text(min_size=1, max_size=50), st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.integers(), st.text()),
        min_size=1, max_size=5
    ))
    @settings(max_examples=50)
    def test_property_framework_extensibility(self, base_name: str, additional_fields: Dict[str, Any]):
        """
        **Property: Framework Extensibility**
        
        For any base name and additional fields, the framework should be able to create
        clean response models without inheritance pollution.
        
        **Validates: Requirements 2.2, 5.1**
        """
        # Filter out problematic characters for class names
        clean_base_name = ''.join(c for c in base_name if c.isalnum() or c == '_')
        assume(len(clean_base_name) > 0)
        
        # Create additional fields in the correct format
        formatted_fields = {}
        for field_name, field_value in additional_fields.items():
            clean_field_name = ''.join(c for c in field_name if c.isalnum() or c == '_')
            # Pydantic v2 doesn't allow field names starting with underscores
            # Also ensure the field name is a valid identifier and doesn't start with underscore
            if (clean_field_name and 
                clean_field_name.isidentifier() and 
                not clean_field_name.startswith('_') and
                clean_field_name != '_'):
                from pydantic import Field
                # Use default values instead of required fields for testing
                formatted_fields[clean_field_name] = (type(field_value), Field(default=field_value, description=f"Test field {clean_field_name}"))
        
        if not formatted_fields:
            # Skip if no valid fields
            assume(False)
        
        try:
            # Use framework to create binary response models
            success_model, error_model, union_type = create_binary_response_models(
                base_name=clean_base_name,
                success_fields=formatted_fields,
                error_fields=formatted_fields
            )
            
            # Property: Should create valid model classes
            assert success_model is not None
            assert error_model is not None
            assert union_type is not None
            
            # Property: Models should be different classes
            assert success_model != error_model
            
            # Property: Should be able to instantiate models
            success_instance = success_model()
            error_instance = error_model()
            
            # Property: Instances should have correct success flags
            assert success_instance.success is True
            assert error_instance.success is False
            
            # Property: Should have additional fields
            for field_name in formatted_fields.keys():
                assert hasattr(success_instance, field_name)
                assert hasattr(error_instance, field_name)
            
        except Exception as e:
            # If framework fails, it should fail gracefully
            assert False, f"Framework should handle field creation gracefully: {e}"
    
    @given(st.integers(min_value=200, max_value=599))
    @settings(max_examples=50)
    def test_property_json_response_status_codes(self, status_code: int):
        """
        **Property: JSON Response Status Codes**
        
        For any valid HTTP status code, the create_response_json function should
        create a JSONResponse with the correct status code.
        
        **Validates: Requirements 2.4, 5.1**
        """
        # Create a test response model
        response = create_cards_save_response(
            success=True,
            new_card_hist_id=123
        )
        
        # Create JSON response with specified status code
        json_response = create_response_json(response, status_code=status_code)
        
        # Property: Should have correct status code
        assert json_response.status_code == status_code, (
            f"Expected status code {status_code}, got {json_response.status_code}"
        )
        
        # Property: Should have valid JSON content
        content = json.loads(json_response.body.decode())
        assert isinstance(content, dict)
        
        # Property: Should contain expected fields
        assert 'success' in content
        assert content['success'] is True
        assert 'new_card_hist_id' in content
        assert content['new_card_hist_id'] == 123


class TestOverloadResponseModelIntegration:
    """Integration tests for @overload response models with actual API patterns."""
    
    @given(st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_property_multiple_response_scenarios(self, card_ids: List[int]):
        """
        **Property: Multiple Response Scenarios**
        
        For any list of card IDs, the system should handle multiple response scenarios
        correctly and consistently.
        
        **Validates: Requirements 2.2, 2.4, 3.1**
        """
        responses = []
        
        # Create multiple responses using @overload functions
        for i, card_id in enumerate(card_ids):
            if i % 2 == 0:  # Even indices: success
                response = create_cards_save_response(
                    success=True,
                    new_card_hist_id=card_id
                )
                responses.append(('success', response))
            else:  # Odd indices: conflict
                response = create_cards_save_response(
                    success=False,
                    conflicts={"card_id": card_id},
                    description=f"Conflict for card {card_id}"
                )
                responses.append(('conflict', response))
        
        # Property: All responses should be valid instances
        for response_type, response in responses:
            if response_type == 'success':
                assert isinstance(response, CardsSaveSuccessResponse)
                assert response.success is True
                assert hasattr(response, 'new_card_hist_id')
            else:
                assert isinstance(response, CardsSaveConflictResponse)
                assert response.success is False
                assert hasattr(response, 'conflicts')
                assert hasattr(response, 'description')
        
        # Property: JSON serialization should be consistent
        for response_type, response in responses:
            json_response = create_response_json(response)
            content = json.loads(json_response.body.decode())
            
            # Should not have null fields
            null_fields = [k for k, v in content.items() if v is None]
            assert len(null_fields) == 0, f"Response should not contain null fields: {null_fields}"
            
            # Should have correct success flag
            assert content['success'] == (response_type == 'success')


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v"])