from typing import Literal
from core.config_dir.config import env

class SpecIndex:
    aliases = {
        env.search_index_spec: {}
    }

    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "5s",
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
        "refresh_interval": "5s",
        "analysis": {
            "analyzer": {
                "group_autocomplete": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_group",
                    "filter": ["uppercase"]
                }
            },
            "tokenizer": {
                "edge_ngram_group": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 8,
                    "token_chars": ["letter", "digit", "punctuation"]
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
                "analyzer": "group_autocomplete"
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


class LogIndex:
    aliases = {env.log_index: {"is_write_index": True}}
    
    # ILM Policy для автоматического управления жизненным циклом
    policy_name = "app-logs-policy"
    ilm_policy = {
        "policy": {
            "phases": {
                "hot": {
                    "actions": {
                        "rollover": {
                            "max_size": "1GB",
                            "max_age": "7d",
                            "max_docs": 1000000
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
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "30s",
        "index.mapping.total_fields.limit": 20,
        "index.codec": "best_compression",
        "index.lifecycle.name": policy_name,
        "index.lifecycle.rollover_alias": env.log_index,
        "analysis": {
            "analyzer": {
                "log_simple": {
                    "type": "custom",
                    "tokenizer": "simple_pattern",
                    "pattern": "[\\s\\-_\\.:/]+",
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
                "index": False,
                "store": True,
                "fields": {
                    "search": {
                        "type": "text",
                        "analyzer": "log_simple"
                    }
                }
            },
            "service": {
                "type": "keyword"
            },
            "method": {
                "type": "keyword"
            },
            "url": {
                "type": "keyword",
                "index": False,
                "ignore_above": 512
            },
            "func": {
                "type": "keyword"
            },
            "location": {
                "type": "keyword",
                "index": False,
                "ignore_above": 256
            },
            "line": {
                "type": "short",
                "index": False
            },
            "ip": {
                "type": "ip"
            }
        }
    }