from datetime import datetime
from agent.config import CURRENT_TIME
from agent.tools.bookings import get_booking


def calculate_refund(booking_id: str, cancel_time: str | None = None) -> dict:
    """Calculates how much a customer gets back if they cancel a booking.

    The amounts are calculated by this function using the cancellation rules.
    Give them to the customer exactly as returned.
    Never calculate refund amounts yourself.

    Args:
        booking_id: Booking number, for example CW-1001.
        cancel_time: Optional moment of cancellation in ISO format with time zone,
            for example "2026-06-11T09:00:00+02:00". If not given, the booking is cancelled now.

    Returns:
        A dictionary with can_cancel, hours_before_start, refund_percent,
        rental_refund_eur, deposit_refund_eur, booking_fee_eur, booking_fee_refund_eur,
        total_refund_eur and refund_method. If the booking cannot be cancelled, can_cancel
        is False with a reason. If the booking does not exist or cancel_time is invalid,
        an error is returned.
    """
    result = get_booking(booking_id)
    if not result["found"]:
        return result
    booking = result["booking"]
    if cancel_time is None:
        now = CURRENT_TIME
    else:
        try:
            now = datetime.fromisoformat(cancel_time)
            if now.tzinfo is None:
                return {"booking_id": booking["id"],
                        "error": "Invalid cancel_time, use ISO format like 2026-06-11T09:00:00+02:00"
                        }
        except ValueError:
            return {"booking_id": booking["id"],
                    "error": "Invalid cancel_time, use ISO format like 2026-06-11T09:00:00+02:00"
                    }
    if booking["status"] != "confirmed":
        return {"booking_id": booking["id"],
                "can_cancel": False,
                "reason": f"Booking with status {booking['status']} cannot be cancelled.",
                "total_refund_eur": 0,
                }
    start = datetime.fromisoformat(booking["start"])
    hours_before_start = (start - now).total_seconds() / 3600
    if hours_before_start >= 48:
        refund_percent = 1.0
    elif hours_before_start >= 24:
        refund_percent = 0.5
    else:
        refund_percent = 0.0
    rental_refund = round(booking["rental_price_eur"] * refund_percent, 2)
    deposit_refund = booking["deposit_eur"]
    total_refund = round(rental_refund + deposit_refund, 2)
    if booking["paid_with"] == "card":
        refund_method = "Refunded to the same card within 5 working days."
    else:
        refund_method = ("Refunded as a new voucher of the same value,"
                         " the deposit is refunded the same way it was paid.")

    return {"booking_id": booking["id"],
            "can_cancel": True,
            "hours_before_start": round(hours_before_start, 1),
            "refund_percent": refund_percent,
            "rental_refund_eur": rental_refund,
            "deposit_refund_eur": deposit_refund,
            "booking_fee_eur": booking["booking_fee_eur"],
            "booking_fee_refund_eur": 0,
            "total_refund_eur": total_refund,
            "refund_method": refund_method,
            }