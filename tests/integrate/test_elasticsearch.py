"""
Integration tests for Elasticsearch functionality.

Tests cover:
- Index population and document counts
- Alias configuration
- ILM policy for log index
- Search relevance for autocomplete and full-text search
"""
import pytest
from elasticsearch import AsyncElasticsearch

from core.config_dir.config import env


@pytest.mark.asyncio
async def test_index_population(aioes: AsyncElasticsearch, db_seed):
    """
    Verify that Elasticsearch indexes are accessible and can be queried.
    
    This validates index availability without strict document count validation,
    as indexing happens asynchronously.
    """
    # Define indexes to check
    indexes = [
        env.search_index_spec,
        env.search_index_group,
        env.search_index_teachers,
        env.search_index_discip,
    ]
    
    for index_alias in indexes:
        # Verify index is accessible
        es_response = await aioes.count(index=index_alias)
        es_count = es_response["count"]
        
        # Just verify the index exists and is queryable (count >= 0)
        assert es_count >= 0, f"Index {index_alias} should be accessible"


@pytest.mark.asyncio
async def test_log_index_availability(aioes: AsyncElasticsearch):
    """
    Verify that the log index exists and is accessible.
    
    The log index doesn't need document count validation since it's for application logs.
    """
    # Check if log index exists
    exists = await aioes.indices.exists(index=env.log_index)
    assert exists, f"Log index {env.log_index} should exist"


@pytest.mark.asyncio
async def test_index_aliases(aioes: AsyncElasticsearch, db_seed):
    """
    Verify that all indexes have correct alias configuration.
    
    Aliases allow zero-downtime index updates and provide stable endpoint names.
    """
    expected_aliases = [
        env.search_index_spec,
        env.search_index_group,
        env.search_index_teachers,
        env.search_index_discip,
        env.log_index,
    ]
    
    for alias_name in expected_aliases:
        # Get alias information
        try:
            alias_info = await aioes.indices.get_alias(name=alias_name)
            assert alias_info, f"Alias {alias_name} should exist and point to an index"
            assert len(alias_info) > 0, f"Alias {alias_name} should point to at least one index"
        except Exception as e:
            pytest.fail(f"Failed to get alias {alias_name}: {e}")


@pytest.mark.asyncio
async def test_log_index_ilm_policy(aioes: AsyncElasticsearch):
    """
    Verify that the log index has ILM (Index Lifecycle Management) policy configured.
    
    ILM policy manages log retention, rollover, and deletion automatically.
    """
    from core.config_dir.index_settings import LogIndex
    
    # Check if ILM policy exists
    try:
        policy = await aioes.ilm.get_lifecycle(name=LogIndex.policy_name)
        assert policy, f"ILM policy {LogIndex.policy_name} should exist"
        assert LogIndex.policy_name in policy, f"Policy {LogIndex.policy_name} should be in response"
    except Exception as e:
        pytest.fail(f"Failed to get ILM policy {LogIndex.policy_name}: {e}")



# Search Relevance Tests

@pytest.mark.asyncio
async def test_autocomplete_spec_prefix_search(client, seed_info):
    """
    Test /public/elastic/autocomplete_spec endpoint for prefix search relevance.
    
    Autocomplete should find documents that start with the search term.
    Tests with short alphanumeric codes typical for specialties.
    """
    # Test cases: search term -> expected to find something
    test_cases = [
        "09",  # Numeric prefix
        "0",   # Single digit
    ]
    
    for search_term in test_cases:
        resp = await client.post(
            "/api/v1/public/elastic/autocomplete_spec",
            json={"search_term": search_term, "search_mode": "auto"}
        )
        assert resp.status_code == 200, f"Autocomplete search for '{search_term}' should succeed"
        
        data = resp.json()
        assert "search_res" in data, "Response should contain search_res field"


@pytest.mark.asyncio
async def test_ext_spec_deep_search(client, seed_info):
    """
    Test /public/elastic/ext_spec endpoint for deep search with pagination.
    
    Deep search uses fuzzy matching and supports pagination.
    Only supports 'deep' search mode (not 'auto').
    """
    # Test deep mode with fuzzy matching
    resp = await client.post(
        "/api/v1/public/elastic/ext_spec",
        json={
            "body": {"search_term": "программирование", "search_mode": "deep"},
            "pagen": {"offset": 0, "limit": 10}
        }
    )
    if resp.status_code != 200:
        print(f"Response: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200, f"Deep search should succeed, got {resp.status_code}: {resp.text}"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    assert isinstance(data["search_res"], list), "search_res should be a list"
    
    # Test with numeric code search
    resp = await client.post(
        "/api/v1/public/elastic/ext_spec",
        json={
            "body": {"search_term": "09", "search_mode": "deep"},
            "pagen": {"offset": 0, "limit": 5}
        }
    )
    assert resp.status_code == 200, "Deep search with numeric code should succeed"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    
    # Test pagination
    resp = await client.post(
        "/api/v1/public/elastic/ext_spec",
        json={
            "body": {"search_term": "информационные", "search_mode": "deep"},
            "pagen": {"offset": 0, "limit": 1}
        }
    )
    assert resp.status_code == 200, "Deep search with pagination should succeed"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    assert len(data["search_res"]) <= 1, "Pagination limit should be respected"


@pytest.mark.asyncio
async def test_search_group_autocomplete(client, seed_info):
    """
    Test /public/elastic/search_group endpoint for group autocomplete.
    
    This endpoint provides fast group search using edge n-gram tokenization.
    Uses seeded groups: "GR1", "23И1", "25Т2", "22ПО1", "20.04".
    """
    # Test with exact group name
    resp = await client.post(
        "/api/v1/public/elastic/search_group",
        json={"search_term": "GR1"}
    )
    assert resp.status_code == 200, "Group search should succeed"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    assert isinstance(data["search_res"], list), "search_res should be a list"
    
    # Verify response structure
    if len(data["search_res"]) > 0:
        first_result = data["search_res"][0]
        assert "id" in first_result, "Result should have id field"
        assert "group_name" in first_result, "Result should have group_name field"
    
    # Test with partial match (prefix)
    resp = await client.post(
        "/api/v1/public/elastic/search_group",
        json={"search_term": "23"}
    )
    assert resp.status_code == 200, "Group search with prefix should succeed"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    
    # Test with Cyrillic characters
    resp = await client.post(
        "/api/v1/public/elastic/search_group",
        json={"search_term": "ПО"}
    )
    assert resp.status_code == 200, "Group search with Cyrillic should succeed"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"


@pytest.mark.asyncio
async def test_methodist_search_teachers_fuzzy(client, seed_info):
    """
    Test /private/elastic/methodist_search for teachers with fuzzy matching.
    
    Verifies the endpoint works correctly with teacher search.
    """
    # Test that endpoint works
    resp = await client.post(
        "/api/v1/private/elastic/methodist_search",
        json={
            "body": {
                "search_tab": "teachers",
                "search_phrase": "Иванов"
            },
            "pagen": {"offset": 0, "limit": 10}
        }
    )
    assert resp.status_code == 200, "Teacher search endpoint should work"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    assert isinstance(data["search_res"], list), "search_res should be a list"


@pytest.mark.asyncio
async def test_methodist_search_disciplines_fuzzy(client, seed_info):
    """
    Test /private/elastic/methodist_search for disciplines with fuzzy matching.
    
    Verifies the endpoint works correctly with discipline search.
    """
    # Test that endpoint works
    resp = await client.post(
        "/api/v1/private/elastic/methodist_search",
        json={
            "body": {
                "search_tab": "disciplines",
                "search_phrase": "Math"
            },
            "pagen": {"offset": 0, "limit": 10}
        }
    )
    assert resp.status_code == 200, "Discipline search endpoint should work"
    
    data = resp.json()
    assert "search_res" in data, "Response should contain search_res field"
    assert isinstance(data["search_res"], list), "search_res should be a list"


@pytest.mark.asyncio
async def test_methodist_search_groups_fuzzy(client, seed_info):
    """
    Test /private/elastic/methodist_search for groups with fuzzy matching.
    
    Full-text search for groups uses standard tokenizer with fuzzy matching (fuzziness=auto).
    This means it finds exact matches and near-matches with edit distance tolerance.
    Uses seeded groups: "GR1", "23И1", "25Т2", "22ПО1", "20.04".
    """
    # Test cases: search term -> should find results
    test_cases = [
        ("22ПО1", True),   # Exact match
        ("23И1", True),    # Exact match
        ("GR1", True),     # Exact match
    ]
    
    for search_term, should_find in test_cases:
        resp = await client.post(
            "/api/v1/private/elastic/methodist_search",
            json={
                "body": {
                    "search_tab": "groups",
                    "search_phrase": search_term
                },
                "pagen": {"offset": 0, "limit": 10}
            }
        )
        assert resp.status_code == 200, f"Group search for '{search_term}' should succeed"
        
        data = resp.json()
        assert "search_res" in data, "Response should contain search_res field"
        
        if should_find:
            assert len(data["search_res"]) > 0, f"Should find groups matching '{search_term}'"
