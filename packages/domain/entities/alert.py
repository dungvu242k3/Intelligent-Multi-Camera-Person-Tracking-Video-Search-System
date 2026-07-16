import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from packages.domain.enums.alert_severity import AlertSeverity

@dataclass
class Alert:
    type: str # 'fire', 'intrusion', 'object'
    severity: AlertSeverity
    title: str
    timestamp: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: Optional[str] = None
    camera_id: Optional[uuid.UUID] = None
    person_id: Optional[uuid.UUID] = None
    is_read: bool = False

    def mark_as_read(self):
        self.is_read = True
