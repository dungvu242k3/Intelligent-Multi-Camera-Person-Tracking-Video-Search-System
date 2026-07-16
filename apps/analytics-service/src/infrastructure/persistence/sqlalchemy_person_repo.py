import uuid
from typing import Any, Optional, cast
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from packages.domain.entities.person import Person
from infrastructure.persistence.models import PersonModel

class SqlAlchemyPersonRepository:
    """SQLAlchemy Repository implementation handling Person entities."""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, person_id: uuid.UUID, for_update: bool = False) -> Optional[Person]:
        """Fetches a person by ID and maps it to domain entity."""
        stmt = select(PersonModel).where(PersonModel.id == person_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def upsert_person(self, person: Person) -> Person:
        """Saves or updates a Person identity model. 
        Note: Transaction commits are managed by the orchestrator unit-of-work.
        """
        # Read the person row with for_update to prevent concurrent update anomalies
        stmt = select(PersonModel).where(PersonModel.id == person.id).with_for_update()
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            # Create new persistent model
            model = PersonModel(
                id=person.id,
                display_name=person.display_name,
                first_seen=person.first_seen,
                last_seen=person.last_seen,
                total_appearances=person.total_appearances
            )
            self.session.add(model)
        else:
            # Update existing persistent model
            model_any = cast(Any, model)
            model_any.display_name = person.display_name
            model_any.first_seen = person.first_seen
            model_any.last_seen = person.last_seen
            model_any.total_appearances = person.total_appearances

        # Commit is deferred to the main transaction boundary in main.py callback
        return self._to_entity(model)

    def _to_entity(self, model: PersonModel) -> Person:
        """Helper mapping SQL model to pure Domain entity."""
        model_any = cast(Any, model)
        return Person(
            id=model_any.id,
            display_name=model_any.display_name,
            first_seen=model_any.first_seen,
            last_seen=model_any.last_seen,
            total_appearances=model_any.total_appearances
        )
