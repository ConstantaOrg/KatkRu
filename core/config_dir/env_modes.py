from enum import Enum

class AppMode(str, Enum):
    LOCAL = "local"
    DOCKER = "docker"


APP_MODE_CONFIG = {
    AppMode.LOCAL: {
        "pg_host": "pg_host",
        "pg_port": "pg_port",
        "es_host": "elastic_host",
        "es_cert": "elastic_cert",
        "es_scheme": "http",
    },
    AppMode.DOCKER: {
        "pg_host": "pg_host_docker",
        "pg_port": "pg_port_docker",
        "es_host": "elastic_host_docker",
        "es_cert": "elastic_cert_docker",
        "es_scheme": "http",
    },
}
