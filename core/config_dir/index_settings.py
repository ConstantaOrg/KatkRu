from typing import Literal
from core.config_dir.config import env

class SpecIndex:
    aliases = {
        env.search_index_spec: {}
    }

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "-1",
        "analysis": {
            "analyzer": {
                # Автокомплит для кодов
                "code_autocomplete": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_code",
                    "filter": ["lowercase"]
                },
                # Автокомплит для названий
                "title_autocomplete": {
                    "type": "custom", 
                    "tokenizer": "edge_ngram_title",
                    "filter": ["lowercase", "russian_stop"]
                },
                # Глубокий поиск (стандартный)
                "deep_search": {
                    "type": "custom",
                    "tokenizer": "standard", 
                    "filter": ["lowercase", "russian_stop"]
                }
            },
            "tokenizer": {
                "edge_ngram_code": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 8,
                    "token_chars": ["letter", "digit", "punctuation"]
                },
                "edge_ngram_title": {
                    "type": "edge_ngram", 
                    "min_gram": 2,
                    "max_gram": 10,
                    "token_chars": ["letter"]
                }
            },
            "filter": {
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
                "index": False
            },
            "code_autocomplete": {
                "type": "text",
                "analyzer": "code_autocomplete"
            },
            "title": {
                "type": "text",
                "analyzer": "deep_search",
                "fields": {
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "title_autocomplete"
                    }
                }
            }
        }
    }

    @staticmethod
    def search_ptn(search_phrase: str, search_mode: Literal["auto", "deep"]):
        if search_mode == "auto":
            return {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "code_autocomplete": {
                                    "query": search_phrase,
                                    "boost": 3
                                }
                            }
                        },
                        {
                            "match": {
                                "title.autocomplete": {
                                    "query": search_phrase,
                                    "boost": 2
                                }
                            }
                        }
                    ]
                }
            }
        return {         # == deep
            "multi_match": {
                "query": search_phrase,
                "fields": ["title", "code_autocomplete^2"],
                "fuzziness": "AUTO",
                "prefix_length": 1
            }
        }


class GroupIndex:
    aliases = {
        env.search_index_group: {}
    }

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "-1",
        "analysis": {
            "analyzer": {
                "group_autocomplete": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_group",
                    "filter": ["uppercase"]
                },
                "fulltext_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["uppercase", "russian_stop"]
                }
            },
            "tokenizer": {
                "edge_ngram_group": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 8,
                    "token_chars": ["letter", "digit", "punctuation"]
                }
            },
            'filter': {
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
                "index": False
            },
            "group_name": {
                "type": "text",
                "analyzer": "group_autocomplete",
                "fields": {
                    "deep": {
                        "type": "text",
                        "analyzer": "fulltext_search"
                    }
                }
            },
            "is_active": {
                "type": "boolean"
            }
        }
    }

    @staticmethod
    def search_ptn(search_phrase: str):
        return {
            "match": {
                "group_name": {
                    "query": search_phrase
                }
            }
        }

    @staticmethod
    def search_ptn_deep(search_phrase: str):
        return { # == 'deep'
            "match": {
                "group_name.deep": {
                    "query": search_phrase,
                    'fuzziness': 'auto',
                    'prefix_length': 1
                }
            }
        }


class DisciplinesIndex:
    aliases = {
        env.search_index_discip: {}
    }

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "-1",
        "analysis": {
            "analyzer": {
                "fulltext_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop"]
                }
            },
            "filter": {
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
                "index": False
            },
            "title": {
                "type": "text",
                "analyzer": "fulltext_search"
            },
            "is_active": {
                "type": "boolean"
            }
        }
    }

    @staticmethod
    def search_ptn(search_phrase: str):
        return {
            "match": {
                "title": {
                    "query": search_phrase,
                    "fuzziness": "auto",
                    "prefix_length": 1
                }
            }
        }


class TeachersIndex:
    aliases = {
        env.search_index_teachers: {}
    }

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "-1",
        "analysis": {
            "analyzer": {
                "fulltext_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop"]
                }
            },
            "filter": {
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
                "index": False
            },
            "fio": {
                "type": "text",
                "analyzer": "fulltext_search"
            },
            "is_active": {
                "type": "boolean"
            }
        }
    }

    @staticmethod
    def search_ptn(search_phrase: str):
        return {
            "match": {
                "fio": {
                    "query": search_phrase,
                    "fuzziness": "auto",
                    "prefix_length": 1
                }
            }
        }


class LogIndex:
    aliases = {env.log_index: {"is_write_index": True}}

    policy_name = "app-logs-policy"

    ilm_policy = {
        "policy": {
            "phases": {
                "hot": {
                    "actions": {
                        "rollover": {
                            "max_size": "1GB",
                            "max_age": "7d",
                            "max_docs": 1_000_000
                        },
                        "set_priority": {
                            "priority": 100
                        }
                    }
                },
                "warm": {
                    "min_age": "7d",
                    "actions": {
                        "allocate": {
                            "number_of_replicas": 0
                        },
                        "forcemerge": {
                            "max_num_segments": 1
                        },
                        "set_priority": {
                            "priority": 50
                        }
                    }
                },
                "cold": {
                    "min_age": "30d",
                    "actions": {
                        "allocate": {
                            "number_of_replicas": 0
                        },
                        "set_priority": {
                            "priority": 0
                        }
                    }
                },
                "delete": {
                    "min_age": "90d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    }
    settings = {
        "number_of_shards": 2,
        "number_of_replicas": 0,
        "refresh_interval": "30s",
        "index.mapping.total_fields.limit": 500,
        "index.codec": "best_compression",
        "analysis": {
            "analyzer": {
                "log_simple": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"]
                }
            }
        }
    }
    mappings = {
        "properties": {
            "@timestamp": {
                "type": "date"
            },
            "level": {
                "type": "keyword"
            },
            "message": {
                "type": "text",
                "analyzer": "log_simple"
            },
            "service": {
                "type": "keyword"
            },
            "environment": {
                "type": "keyword"
            },
            "method": {
                "type": "keyword"
            },
            "url": {
                "type": "keyword",
                "ignore_above": 2048
            },
            "http_status": {
                "type": "integer"
            },
            "func": {
                "type": "keyword"
            },
            "location": {
                "type": "keyword",
                "ignore_above": 512
            },
            "line": {
                "type": "integer"
            },
            "ip": {
                "type": "ip",
                "ignore_malformed": True
            },
            # HTTP метрики
            "response_time": {
                "type": "float"
            },
            # Метрики загруженности сервера
            "cpu_percent": {
                "type": "float"
            },
            "memory_percent": {
                "type": "float"
            },
            "memory_used_mb": {
                "type": "float"
            },
            "memory_total_mb": {
                "type": "float"
            },
            "metric_type": {
                "type": "keyword"
            },
            # Опционально: вложенная структура для будущего расширения
            # "hardware_usage": {
            #     "type": "object",
            #     "properties": {
            #         "cpu": {
            #             "type": "object",
            #             "properties": {
            #                 "percent": {"type": "float"},
            #                 "count": {"type": "integer"}
            #             }
            #         },
            #         "memory": {
            #             "type": "object",
            #             "properties": {
            #                 "percent": {"type": "float"},
            #                 "used_mb": {"type": "float"},
            #                 "total_mb": {"type": "float"},
            #                 "available_mb": {"type": "float"}
            #             }
            #         },
            #         "disk": {
            #             "type": "object",
            #             "properties": {
            #                 "percent": {"type": "float"},
            #                 "used_gb": {"type": "float"},
            #                 "total_gb": {"type": "float"}
            #             }
            #         }
            #     }
            # }
        }
    }
