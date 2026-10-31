import json
from pathlib import Path

BOOKINGS_PATH = Path(__file__).resolve().parents[2] / "data" / "bookings.json"

def get_booking(booking_id: str) -> dict:
    """Returns details of one booking from data/bookings.json
    or a clear not found result when it doesn't exist.

    Args:
        booking_id: Booking number, for example CW-1001.
    """
    with open(BOOKINGS_PATH, "r", encoding="utf-8") as file:
        bookings = json.load(file)
        fixed_booking_id = booking_id.strip().upper()
        for booking in bookings:
            if booking["id"] == fixed_booking_id:
                return {"found": True, "booking": booking}
        return {"found": False,
                "error": f"Booking {booking_id} not found.",
        }