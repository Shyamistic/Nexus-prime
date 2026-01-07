import logging
from typing import Type, List, Optional, TypeVar, Dict
from uuid import uuid4
from pydantic import BaseModel
from .base import BaseRepository

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# In-memory storage (Resets when you restart the server)
_MOCK_STORAGE: Dict[str, Dict[str, dict]] = {
    "incidents": {},
    "events": {},
    "actions": {}
}

class MockCosmosRepository(BaseRepository[T]):
    def __init__(self, container_name: str, model: Type[T]):
        self.container_name = container_name
        self.model = model
        if container_name not in _MOCK_STORAGE:
            _MOCK_STORAGE[container_name] = {}

    async def create(self, item: T) -> T:
        item_dict = item.model_dump(mode="json", exclude_none=True)
        # Ensure ID exists
        if "id" not in item_dict:
            item_dict["id"] = str(uuid4())
        
        _MOCK_STORAGE[self.container_name][item_dict["id"]] = item_dict
        logger.info(f"[MOCK DB] Created {self.container_name}: {item_dict['id']}")
        return self.model(**item_dict)

    async def get(self, item_id: str, partition_key: str) -> Optional[T]:
        data = _MOCK_STORAGE[self.container_name].get(item_id)
        if data:
            return self.model(**data)
        return None

    async def update(self, item_id: str, partition_key: str, updates: dict, etag: Optional[str] = None) -> T:
        data = _MOCK_STORAGE[self.container_name].get(item_id)
        if data:
            data.update(updates)
            return self.model(**data)
        raise ValueError("Item not found")

    async def query(self, query: str, parameters: List[dict]) -> List[T]:
        # Simple Mock Query: Returns ALL items (ignores the SQL query for now)
        # In a real mock, we might filter, but for MVP this is fine.
        items = []
        for doc in _MOCK_STORAGE[self.container_name].values():
            items.append(self.model(**doc))
        return items