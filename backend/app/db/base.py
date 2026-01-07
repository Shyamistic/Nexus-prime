from typing import Generic, TypeVar, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel

# T is a generic type that allows us to reuse this class for Incidents, Events, etc.
T = TypeVar("T", bound=BaseModel)

class BaseRepository(ABC, Generic[T]):
    """
    The Abstract Base Class (Interface).
    It defines the rules that CosmosRepository and MockCosmosRepository must follow.
    """
    
    @abstractmethod
    async def create(self, item: T) -> T:
        """Creates a new item."""
        pass

    @abstractmethod
    async def get(self, item_id: str, partition_key: str) -> Optional[T]:
        """Retrieves an item by ID and Partition Key."""
        pass

    @abstractmethod
    async def update(self, item_id: str, partition_key: str, updates: dict) -> T:
        """Updates an item."""
        pass
        
    @abstractmethod
    async def query(self, query: str, parameters: List[dict]) -> List[T]:
        """Executes a database query."""
        pass