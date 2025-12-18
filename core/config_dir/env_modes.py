from enum import Enum

class AppMode(str, Enum):
    LOCAL = "local"
    DOCKER = "docker"
    PROD = "prod"


APP_MODE_CONFIG = {
    AppMode.LOCAL: {
        "pg_host": "pg_host",
        "pg_port": "pg_port",
        "es_host": "elastic_host",
        "es_cert": "elastic_cert",
        "es_scheme": "http",
        'redis_host': 'redis_host',
        'redis_port': 'redis_port',
    },
    AppMode.DOCKER: {
        "pg_host": "pg_host_docker",
        "pg_port": "pg_port_docker",
        "es_host": "elastic_host_docker",
        "es_cert": "elastic_cert_docker",
        "es_scheme": "http",
        'redis_host': 'redis_host_docker',
        'redis_port': 'redis_port_docker',
    },
    AppMode.PROD: {
        "pg_host": "pg_host_docker",
        "pg_port": "pg_port_docker",
        "es_host": "elastic_host_docker",
        "es_cert": "elastic_cert_docker",
        "es_scheme": "http",
        'redis_host': 'redis_host_docker',
        'redis_port': 'redis_port_docker',
    },
}
