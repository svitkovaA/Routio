"""
file_ service_base.py

This file defines the abstract base class for all application services.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import hashlib
from typing import Any, ClassVar, Dict, Generic, TypeVar, Type, cast, final

# Type variable representing concrete ServiceBase subclass
T = TypeVar("T", bound="ServiceBase[Any]")

# Type variable representing internal state type
S = TypeVar("S")

class ServiceBase(ABC, Generic[S]):
    """
    Abstract base class for singleton services.
    """
    
    # Stores singleton instances per concrete service class
    __instances: ClassVar[Dict[Type["ServiceBase[Any]"], object]] = {}

    def __init__(self) -> None:
        cls = type(self)
        if cls in ServiceBase.__instances:
            raise RuntimeError("Use get_instance()")
        self.__state: S | None = None
        
    @classmethod
    @final
    def get_instance(cls: Type[T]) -> T:
        # Return existing singleton instance if available
        instance = ServiceBase.__instances.get(cls)

        # Create an instance
        if instance is None:
            instance = cls()
            ServiceBase.__instances[cls] = instance

        return cast(T, instance)
    
    @final
    def _get_state(self) -> S:
        # Ensure state has been initialized
        if self.__state is None:
            raise RuntimeError(f"{type(self).__name__} state not initialized")
        return self.__state
    
    @final
    def _set_state(self, state: S) -> None:
        # Atomically replace internal state
        self.__state = state
    
    @abstractmethod
    async def reload(self) -> None:
        # Reload internal state
        pass

    @final
    @staticmethod
    def _hash_label(value: str) -> str:
        """
        Compute short deterministic hash for filesystem naming.

        Args:
            value: Value to be hashed

        Returns:
            stop_label hash
        """
        return hashlib.blake2b(
            value.encode("utf-8"),
            digest_size=8
        ).hexdigest()
    
    @final
    def service_available(self) -> bool:
        """
        Signalizes if service is available.

        Returns:
            True if service is available, false otherwise
        """
        try:
            self._get_state()
            return True
        except:
            return False
        
    async def _shutdown(self) -> None:
        """
        Gracefully releases service resources.
        """
        pass
        
    @classmethod
    @final
    async def shutdown_services(cls) -> None:
        """
        Gracefully releases resources of all instantiated services.
        """
        for instance in cls.__instances.values():
            if isinstance(instance, ServiceBase):
                await instance._shutdown()

# End of file service_base.py
