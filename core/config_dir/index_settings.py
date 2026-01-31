from typing import Literal

from core.config_dir.config import env

class SpecIndex:
    aliases = {
        env.search_index_spec: {}
    }

    settings = {
        "index": {
            "number_of_shards": 3,
            "routing.allocation.total_shards_per_node": 4
        },
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "ngram_code_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_code",
                    "filter": ["lowercase"]
                },
                "ngram_spec_prefix": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ngram_spec_filter"]
                },
                "ngram_spec_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop", "ngram_spec_filter"]
                }
            },
            "tokenizer": {
                "edge_ngram_code": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 10,
                    "token_chars": ["punctuation", "digit"]
                }
            },
            "filter": {
                "ngram_spec_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 15,
                    "token_chars": ["letter"]
                },
                "russian_stop": {
                    "type": "stop",
                    "ignore_case": True,
                    "stopwords": "_russian_"
                }
            }
        }
    }
    mappings = {
        "properties": {
            "id": {
                "type": "long",
                "index": False,
                "coerce": False
            },
            "code_prefix": {
                "type": "text",
                "analyzer": "ngram_code_analyzer"
            },
            "spec_title_prefix": {
                "type": "text",
                "analyzer": "ngram_spec_prefix"
            },
            "spec_title_search": {
                "type": "text",
                "analyzer": "ngram_spec_search"
            }
        }
    }


    @staticmethod
    def search_ptn(search_phrase: str, search_mode: Literal["auto", "deep"]):
        query_autocomplete = {
            "multi_match": {
              "query": search_phrase,
              "fields": ["code_prefix^3" ,"spec_title_prefix"],
              "type": "bool_prefix"
            }
        }
        query_deep_search = {
            "match": {
              "spec_title_search": {
                "query": search_phrase,
                "fuzziness": "auto",
                "prefix_length": 1
              }
            }
        }

        search_modes = {
            "auto": query_autocomplete,
            "deep": query_deep_search
        }

        return search_modes[search_mode]


class GroupIndex:
    aliases = {
        env.search_index_group: {}
    }

    settings = {
        "index": {
            "number_of_shards": 3,
            "routing.allocation.total_shards_per_node": 4
        },
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "ngram_group_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_group",
                    "filter": ["uppercase"]
                }
            },
            "tokenizer": {
                "edge_ngram_group": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 10,
                    "token_chars": ["letter", "digit", "punctuation"]
                }
            }
        }
    }
    mappings = {
        "properties": {
            "id": {
                "type": "long",
                "index": False,
                "coerce": False
            },
            "group_name": {
                "type": "text",
                "analyzer": "ngram_group_analyzer"
            }
        }
    }

    @staticmethod
    def search_ptn(search_phrase: str):
        query = {
            'match': {
                'group_name': {
                    'query': search_phrase
                }
            }
        }
        return query


