from dataclasses import dataclass
from datetime import datetime


@dataclass
class LostLuggageReport:
    """
    In-code documentation of the lost_luggage_reports schema.

    MongoDB document structure:
    {
        _id: ObjectId,
        user_id: str,
        depot_id: str,
        item_name: str,
        item_description: str,
        date_lost: str (ISO date),
        bus_number: str,
        contact_phone: str,
        status: str,
        created_at: datetime,
    }
    """

    user_id: str
    depot_id: str
    item_name: str
    item_description: str
    date_lost: str
    bus_number: str
    contact_phone: str
    status: str = "reported"
    created_at: datetime | None = None

