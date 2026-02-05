"""
Property-based tests for Multi-Response Scenario Handling

These tests validate the correctness properties of the Union response types
and @overload implementations for endpoints with multiple response scenarios.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, Any, List, Union
import json

from core.utils.response_model_utils import (
    # Cards Save
    CardsSaveResponse, CardsSaveSuccessResponse, CardsSaveConflictResponse,
    create_cards_save_response,
    
    # User Registration
    UserRegistrationResponse, UserRegistrationSuccessResponse, UserRegistrationConflictResponse,
    create_user_registration_response,
    
    # User Login
    UserLoginResponse, UserLoginSuccessResponse, UserLoginUnauthorizedResponse,
    create_user_login_response,
    
    # Groups Add
    GroupsAddResponse, GroupsAddSuccessResponse, GroupsAddConflictResponse,
    create_groups_add_response,
    
    # Teachers Add
    TeachersAddResponse, TeachersAddSuccessResponse, TeachersAddConflictResponse,
    create_teachers_add_response,
    
    # Disciplines Add
    DisciplinesAddResponse, DisciplinesAddSuccessResponse, DisciplinesAddConflictResponse,
    create_disciplines_add_response,
    
    # Ttable PreCommit
    TtableVersionsPreCommitResponse, TtableVersionsPreCommitSuccessResponse, TtableVersionsPreCommitConflictResponse,
    create_ttable_precommit_response,
    
    # Utility functions
    create_response_json
)


# Generators for test data
@st.composite
def cards_save_data(draw):
    """Generate data for cards save scenarios."""
    success = draw(st.booleans())
    if success:
        return {
            'success': True,
            'new_card_hist_id': draw(st.integers(min_value=1, max_value=10000)),
            'message': draw(st.text(min_size=1, max_size=100))
        }
    else:
        return {
            'success': False,
            'conflicts': draw(st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(st.integers(), st.text(), st.lists(st.integers())),
                min_size=1, max_size=5
            )),
            'description': draw(st.text(min_size=1, max_size=200)),
            'message': draw(st.text(min_size=1, max_size=100))
        }


@st.composite
def user_registration_data(draw):
    """Generate data for user registration scenarios."""
    success = draw(st.booleans())
    return {
        'success': success,
        'message': draw(st.text(min_size=1, max_size=100)),
        'detail': None if success else draw(st.text(min_size=1, max_size=200))
    }


@st.composite
def groups_add_data(draw):
    """Generate data for groups add scenarios."""
    success = draw(st.booleans())
    if success:
        return {
            'success': True,
            'group_id': draw(st.integers(min_value=1, max_value=10000)),
            'message': draw(st.text(min_size=1, max_size=100))
        }
    else:
        return {
            'success': False,
            'message': draw(st.text(min_size=1, max_size=100)),
            'detail': draw(st.text(min_size=1, max_size=200))
        }


@st.composite
def ttable_precommit_data(draw):
    """Generate data for ttable precommit scenarios."""
    success = draw(st.booleans())
    if success:
        return {
            'success': True,
            'message': draw(st.text(min_size=1, max_size=100))
        }
    else:
        return {
            'success': False,
            'needed_groups': draw(st.lists(st.integers(min_value=1, max_value=10000), min_size=1, max_size=10)),
            'ttable_id': draw(st.integers(min_value=1, max_value=10000)),
            'message': draw(st.text(min_size=1, max_size=100))
        }


class TestMultiResponseScenarioProperties:
    """Property-based tests for multi-response scenario handling."""
    
    @given(cards_save_data())
    def test_property_5_cards_save_multi_response_handling(self, scenario_data: Dict[str, Any]):
        """
        **Property 5: Multi-Response Scenario Handling - Cards Save**
        
        For any cards save endpoint scenario (success or conflict), the @overload function
        should return the correct response type and the Union type should handle both scenarios.
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        success = scenario_data['success']
        
        if success:
            # Test success scenario
            response = create_cards_save_response(
                success=True,
                new_card_hist_id=scenario_data['new_card_hist_id'],
                message=scenario_data.get('message', "Card saved successfully")
            )
            
            # Property: Success response should be of correct type
            assert isinstance(response, CardsSaveSuccessResponse), (
                f"Expected CardsSaveSuccessResponse, got {type(response)}"
            )
            
            # Property: Success response should have required fields
            assert response.success is True
            assert response.new_card_hist_id == scenario_data['new_card_hist_id']
            assert isinstance(response.message, str)
            
            # Property: Success response should serialize to clean JSON
            json_response = create_response_json(response, status_code=200)
            assert json_response.status_code == 200
            
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is True
            assert response_dict['new_card_hist_id'] == scenario_data['new_card_hist_id']
            assert 'conflicts' not in response_dict  # Should not have conflict fields
            
        else:
            # Test conflict scenario
            response = create_cards_save_response(
                success=False,
                conflicts=scenario_data['conflicts'],
                description=scenario_data['description'],
                message=scenario_data.get('message', "Conflicts detected during save")
            )
            
            # Property: Conflict response should be of correct type
            assert isinstance(response, CardsSaveConflictResponse), (
                f"Expected CardsSaveConflictResponse, got {type(response)}"
            )
            
            # Property: Conflict response should have required fields
            assert response.success is False
            assert response.conflicts == scenario_data['conflicts']
            assert response.description == scenario_data['description']
            assert isinstance(response.message, str)
            
            # Property: Conflict response should serialize to clean JSON
            json_response = create_response_json(response, status_code=409)
            assert json_response.status_code == 409
            
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is False
            assert response_dict['conflicts'] == scenario_data['conflicts']
            assert 'new_card_hist_id' not in response_dict  # Should not have success fields
    
    @given(user_registration_data())
    def test_property_5_user_registration_multi_response_handling(self, scenario_data: Dict[str, Any]):
        """
        **Property 5: Multi-Response Scenario Handling - User Registration**
        
        For any user registration endpoint scenario (success or conflict), the @overload function
        should return the correct response type and handle different status codes appropriately.
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        success = scenario_data['success']
        
        if success:
            # Test success scenario
            response = create_user_registration_response(
                success=True,
                message=scenario_data.get('message', "Пользователь добавлен")
            )
            
            # Property: Success response should be of correct type
            assert isinstance(response, UserRegistrationSuccessResponse), (
                f"Expected UserRegistrationSuccessResponse, got {type(response)}"
            )
            
            # Property: Success response should have literal True for success field
            assert response.success is True
            assert isinstance(response.message, str)
            
            # Property: Success response should serialize correctly for 200 status
            json_response = create_response_json(response, status_code=200)
            assert json_response.status_code == 200
            
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is True
            assert 'detail' not in response_dict or response_dict['detail'] is None
            
        else:
            # Test conflict scenario
            response = create_user_registration_response(
                success=False,
                message=scenario_data.get('message', "Пользователь уже существует"),
                detail=scenario_data.get('detail', "Пользователь уже существует")
            )
            
            # Property: Conflict response should be of correct type
            assert isinstance(response, UserRegistrationConflictResponse), (
                f"Expected UserRegistrationConflictResponse, got {type(response)}"
            )
            
            # Property: Conflict response should have literal False for success field
            assert response.success is False
            assert isinstance(response.message, str)
            assert isinstance(response.detail, str)
            
            # Property: Conflict response should serialize correctly for 409 status
            json_response = create_response_json(response, status_code=409)
            assert json_response.status_code == 409
            
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is False
            assert 'detail' in response_dict
    
    @given(groups_add_data())
    def test_property_5_groups_add_multi_response_handling(self, scenario_data: Dict[str, Any]):
        """
        **Property 5: Multi-Response Scenario Handling - Groups Add**
        
        For any groups add endpoint scenario, the system should handle both success
        and conflict responses with appropriate status codes and clean JSON output.
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        success = scenario_data['success']
        
        if success:
            response = create_groups_add_response(
                success=True,
                group_id=scenario_data['group_id'],
                message=scenario_data.get('message', "Группа добавлена")
            )
            
            # Property: Success response type and fields
            assert isinstance(response, GroupsAddSuccessResponse)
            assert response.success is True
            assert response.group_id == scenario_data['group_id']
            
            # Property: Clean JSON serialization
            json_response = create_response_json(response, status_code=200)
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is True
            assert response_dict['group_id'] == scenario_data['group_id']
            assert 'detail' not in response_dict
            
        else:
            response = create_groups_add_response(
                success=False,
                message=scenario_data.get('message', "Группа с таким названием в этом здании уже существует"),
                detail=scenario_data.get('detail', "Группа с таким названием в этом здании уже существует")
            )
            
            # Property: Conflict response type and fields
            assert isinstance(response, GroupsAddConflictResponse)
            assert response.success is False
            
            # Property: Clean JSON serialization with correct status code
            json_response = create_response_json(response, status_code=409)
            assert json_response.status_code == 409
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is False
            assert 'group_id' not in response_dict
    
    @given(ttable_precommit_data())
    def test_property_5_ttable_precommit_multi_response_handling(self, scenario_data: Dict[str, Any]):
        """
        **Property 5: Multi-Response Scenario Handling - Ttable PreCommit**
        
        For any ttable precommit endpoint scenario, the system should handle both success
        and conflict responses with different status codes (200 vs 409).
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        success = scenario_data['success']
        
        if success:
            response = create_ttable_precommit_response(
                success=True,
                message=scenario_data.get('message', "Timetable version ready for commit")
            )
            
            # Property: Success response should be correct type
            assert isinstance(response, TtableVersionsPreCommitSuccessResponse)
            assert response.success is True
            
            # Property: Should serialize to 200 status code
            json_response = create_response_json(response, status_code=200)
            assert json_response.status_code == 200
            
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is True
            assert 'needed_groups' not in response_dict
            assert 'ttable_id' not in response_dict
            
        else:
            response = create_ttable_precommit_response(
                success=False,
                needed_groups=scenario_data['needed_groups'],
                ttable_id=scenario_data['ttable_id'],
                message=scenario_data.get('message', "Conflicts detected in timetable version")
            )
            
            # Property: Conflict response should be correct type
            assert isinstance(response, TtableVersionsPreCommitConflictResponse)
            assert response.success is False
            assert response.needed_groups == scenario_data['needed_groups']
            assert response.ttable_id == scenario_data['ttable_id']
            
            # Property: Should serialize to 409 status code
            json_response = create_response_json(response, status_code=409)
            assert json_response.status_code == 409
            
            response_dict = json.loads(json_response.body.decode())
            assert response_dict['success'] is False
            assert response_dict['needed_groups'] == scenario_data['needed_groups']
            assert response_dict['ttable_id'] == scenario_data['ttable_id']
    
    @given(st.lists(st.booleans(), min_size=2, max_size=10))
    def test_property_5_multiple_scenarios_consistency(self, success_flags: List[bool]):
        """
        **Property 5: Multi-Response Scenario Handling - Consistency Across Multiple Calls**
        
        For any sequence of success/failure scenarios, the @overload functions should
        consistently return the correct response types and maintain type safety.
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        responses = []
        
        # Generate responses for each scenario
        for i, success in enumerate(success_flags):
            if success:
                # Create success response
                response = create_cards_save_response(
                    success=True,
                    new_card_hist_id=i + 100,
                    message=f"Success {i}"
                )
                responses.append(('success', response))
            else:
                # Create conflict response
                response = create_cards_save_response(
                    success=False,
                    conflicts={"test": f"conflict_{i}"},
                    description=f"Conflict description {i}",
                    message=f"Conflict {i}"
                )
                responses.append(('conflict', response))
        
        # Property: All success responses should be of success type
        success_responses = [r for scenario, r in responses if scenario == 'success']
        for response in success_responses:
            assert isinstance(response, CardsSaveSuccessResponse), (
                f"All success responses should be CardsSaveSuccessResponse, got {type(response)}"
            )
            assert response.success is True
            assert hasattr(response, 'new_card_hist_id')
            assert not hasattr(response, 'conflicts')
        
        # Property: All conflict responses should be of conflict type
        conflict_responses = [r for scenario, r in responses if scenario == 'conflict']
        for response in conflict_responses:
            assert isinstance(response, CardsSaveConflictResponse), (
                f"All conflict responses should be CardsSaveConflictResponse, got {type(response)}"
            )
            assert response.success is False
            assert hasattr(response, 'conflicts')
            assert not hasattr(response, 'new_card_hist_id')
        
        # Property: Response types should be mutually exclusive
        assert len(success_responses) + len(conflict_responses) == len(responses), (
            "All responses should be either success or conflict type"
        )
    
    @given(st.integers(min_value=1, max_value=1000))
    def test_property_5_union_type_compatibility(self, test_id: int):
        """
        **Property 5: Multi-Response Scenario Handling - Union Type Compatibility**
        
        For any Union response type, both success and error variants should be
        compatible with the Union type and maintain proper type annotations.
        
        **Validates: Requirements 1.5, 2.2, 2.4**
        """
        # Test Cards Save Union compatibility
        success_response = create_cards_save_response(
            success=True,
            new_card_hist_id=test_id
        )
        
        conflict_response = create_cards_save_response(
            success=False,
            conflicts={"test_id": test_id},
            description="Test conflict"
        )
        
        # Property: Both responses should be valid CardsSaveResponse Union members
        def is_valid_cards_save_response(response) -> bool:
            return isinstance(response, (CardsSaveSuccessResponse, CardsSaveConflictResponse))
        
        assert is_valid_cards_save_response(success_response), (
            "Success response should be valid Union member"
        )
        assert is_valid_cards_save_response(conflict_response), (
            "Conflict response should be valid Union member"
        )
        
        # Property: Responses should have discriminator field (success)
        assert hasattr(success_response, 'success')
        assert hasattr(conflict_response, 'success')
        assert success_response.success is True
        assert conflict_response.success is False
        
        # Property: JSON serialization should preserve discriminator
        success_json = json.loads(create_response_json(success_response).body.decode())
        conflict_json = json.loads(create_response_json(conflict_response).body.decode())
        
        assert success_json['success'] is True
        assert conflict_json['success'] is False
        
        # Property: Each response should only contain its relevant fields
        assert 'new_card_hist_id' in success_json
        assert 'conflicts' not in success_json
        
        assert 'conflicts' in conflict_json
        assert 'new_card_hist_id' not in conflict_json


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--tb=short"])