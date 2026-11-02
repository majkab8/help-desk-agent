from agent.tools.bookings import get_booking


def test_existing_booking_is_found():
    result = get_booking("CW-1001")

    assert result["found"] is True
    assert result["booking"]["id"] == "CW-1001"
    assert result["booking"]["status"] == "confirmed"
    assert result["booking"]["rental_price_eur"] == 40.0


def test_not_first_on_the_list():
    result = get_booking("CW-1007")

    assert result["found"] is True
    assert result["booking"]["id"] == "CW-1007"


def test_normalizing_number():
    result = get_booking(" cw-1001 ")

    assert result["found"] is True
    assert result["booking"]["id"] == "CW-1001"


def test_booking_does_not_exist():
    result = get_booking("CW-9999")

    assert result["found"] is False
    assert result["error"]


def test_empty_booking_is_not_found():
    result = get_booking("")

    assert result["found"] is False
    assert result["error"]
