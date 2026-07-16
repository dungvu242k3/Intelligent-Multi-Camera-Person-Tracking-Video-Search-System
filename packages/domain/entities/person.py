import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

@dataclass
class Person:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    display_name: Optional[str] = None
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    total_appearances: int = 1

    def update_appearance(self, timestamp: datetime):
        """Updates the temporal values and increments appearances count."""
        if timestamp < self.first_seen:
            self.first_seen = timestamp
        if timestamp > self.last_seen:
            self.last_seen = timestamp
        self.total_appearances += 1
