"""Connector registry and factory."""

from typing import Dict, Type

from ingestao.connectors.base import BaseConnector


_registry: Dict[str, Type[BaseConnector]] = {}


def register(source_type: str):
    """Decorator to register a connector class for a given source type."""
    def wrapper(cls: Type[BaseConnector]):
        _registry[source_type] = cls
        return cls
    return wrapper


def get_connector(source_type: str, **kwargs) -> BaseConnector:
    """Factory: instantiate a registered connector by source type."""
    cls = _registry.get(source_type)
    if cls is None:
        raise KeyError(f"No connector registered for source_type={source_type!r}. "
                       f"Available: {list(_registry.keys())}")
    return cls(**kwargs)


def list_sources() -> Dict[str, Type[BaseConnector]]:
    """Return a copy of the registered source types."""
    return dict(_registry)
