import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from packages.domain.entities.person import Person
from infrastructure.persistence.models import PersonModel

class SqlAlchemyPersonRepository:
    """SQLAlchemy Repository implementation handling Person entities."""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, person_id: uuid.UUID) -> Optional[Person]:
        """Fetches a person by ID and maps it to domain entity."""
        result = await self.session.execute(
            select(PersonModel).where(PersonModel.id == person_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def upsert_person(self, person: Person) -> Person:
        """Saves or updates a Person identity model."""
        result = await self.session.execute(
            select(PersonModel).where(PersonModel.id == person.id)
        )
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
            model.display_name = person.display_name
            model.first_seen = person.first_seen
            model.last_seen = person.last_seen
            model.total_appearances = person.total_appearances

        await self.session.commit()
        return self._to_entity(model)

    def _to_entity(self, model: PersonModel) -> Person:
        """Helper mapping SQL model to pure Domain entity."""
        return Person(
            id=model.id,
            display_name=model.display_name,
            first_seen=model.first_seen,
            last_seen=model.last_seen,
            total_appearances=model.total_appearances
        )
