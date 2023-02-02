print("Initializing search_proxy Python package")
from .connect import(
    add_keyword_mapping,
    connect,
    connect_dev_environment,
    get_mappings_indice,
    get_mappings_properties_indice
)

__all__ = [
    "add_keyword_mapping",
    "connect",
    "connect_dev_environment",
    "get_mappings_indice",
    "get_mappings_properties_indice"
]
print("search_proxy Python package successfully initialized")

