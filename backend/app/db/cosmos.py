import logging
from typing import Type, List, Optional, Any, TypeVar
from azure.cosmos.aio import CosmosClient, ContainerProxy
from azure.cosmos import exceptions
from pydantic import BaseModel
from .base import BaseRepository

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class CosmosRepository(BaseRepository[T]):
    def __init__(self, container: ContainerProxy, model: Type[T]):
        self.container = container
        self.model = model

    async def create(self, item: T) -> T:
        try:
            # exclude_none=True saves storage and bandwidth
            item_dict = item.model_dump(mode="json", exclude_none=True)
            # Ensure "id" is a string for Cosmos
            item_dict["id"] = str(item_dict["id"])
            
            resource = await self.container.create_item(body=item_dict)
            logger.info(f"Created {self.model.__name__} with ID {resource['id']}")
            return self.model(**resource)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            raise

    async def get(self, item_id: str, partition_key: str) -> Optional[T]:
        try:
            item = await self.container.read_item(item=item_id, partition_key=partition_key)
            return self.model(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Database error fetching {item_id}: {str(e)}")
            raise

    async def update(self, item_id: str, partition_key: str, updates: dict, etag: Optional[str] = None) -> T:
        """
        Production-grade update with Optimistic Concurrency Control.
        If etag is provided, the update fails if the record has changed since we last read it.
        """
        try:
            # 1. Fetch current item
            current_item = await self.container.read_item(item=item_id, partition_key=partition_key)
            
            # 2. Check ETag if provided (prevent race conditions)
            if etag and current_item.get("_etag") != etag:
                raise exceptions.CosmosAccessConditionFailedError(message="Data has changed since last read")

            # 3. Apply updates
            current_item.update(updates)
            
            # 4. Save
            updated_item = await self.container.replace_item(
                item=item_id,
                body=current_item
            )
            return self.model(**updated_item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Update failed for {item_id}: {str(e)}")
            raise

    async def query(self, query: str, parameters: List[dict] = []) -> List[T]:
        items = []
        try:
            items_iterable = self.container.query_items(
                query=query,
                parameters=parameters
            )
            async for item in items_iterable:
                items.append(self.model(**item))
            return items
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Query failed: {str(e)}")
            raise