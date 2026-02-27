from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Generic, TypeVar, Type, cast, final

T = TypeVar("T", bound="ServiceBase[Any]")
S = TypeVar("S")

class ServiceBase(ABC, Generic[S]):
    __instances: ClassVar[Dict[Type["ServiceBase[Any]"], object]] = {}

    def __init__(self):
        cls = type(self)
        if cls in ServiceBase.__instances:
            raise RuntimeError("Use get_instance()")
        self.__state: S | None = None
        
    @classmethod
    @final
    def get_instance(cls: Type[T]) -> T:
        instance = ServiceBase.__instances.get(cls)
        if instance is None:
            instance = cls()
            ServiceBase.__instances[cls] = instance
        return cast(T, instance)
    
    @final
    def _get_state(self) -> S:
        if self.__state is None:
            raise RuntimeError(f"{type(self).__name__} state not initialized")
        return self.__state
    
    @final
    def _set_state(self, state: S) -> None:
        self.__state = state
    
    @abstractmethod
    async def reload(self) -> None:
        pass
