import pytest

from agent.tools.refunds import calculate_refund


@pytest.mark.parametrize(
    "booking_id, expected_total, expected_percent",
    [
        ("CW-1001", 90.0, 1.0),   # 73 h before start -> 100%
        ("CW-1002", 340.0, 0.5),  # 33 h -> 50%
        ("CW-1003", 50.0, 0.0),   # 6 h -> 0%, deposit still refunded
        ("CW-1004", 73.0, 1.0),   # voucher, 240 h -> 100%
        ("CW-1007", 186.0, 1.0),  # exactly 48 h -> 100%
        ("CW-1009", 169.0, 1.0),  # long rental, 121 h -> 100%
        ("CW-1010", 170.0, 0.5),  # exactly 24 h -> 50%
    ],
)
def test_refund_for_confirmed_bookings(booking_id, expected_total, expected_percent):
    result = calculate_refund(booking_id)

    assert result["can_cancel"] is True
    assert result["total_refund_eur"] == expected_total
    assert result["refund_percent"] == expected_percent


@pytest.mark.parametrize("booking_id", ["CW-1005", "CW-1006", "CW-1008"])
def test_bookings_that_cannot_be_cancelled(booking_id):
    result = calculate_refund(booking_id)

    assert result["can_cancel"] is False
    assert result["total_refund_eur"] == 0
    assert "reason" in result


def test_booking_fee_is_never_refunded():
    result = calculate_refund("CW-1002")

    assert result["booking_fee_eur"] == 2.0
    assert result["booking_fee_refund_eur"] == 0


def test_deposit_is_always_refunded():
    result = calculate_refund("CW-1003")

    assert result["refund_percent"] == 0.0
    assert result["deposit_refund_eur"] == 50.0


def test_card_refund_method():
    result = calculate_refund("CW-1001")

    assert "card" in result["refund_method"]


def test_voucher_refund_method():
    result = calculate_refund("CW-1004")

    assert "voucher" in result["refund_method"]


def test_unknown_booking():
    result = calculate_refund("CW-9999")

    assert result["found"] is False
    assert "error" in result


@pytest.mark.parametrize(
    "cancel_time, expected_percent",
    [
        ("2026-06-11T10:00:00+02:00", 1.0),  # exactly 48 h before CW-1001
        ("2026-06-11T10:01:00+02:00", 0.5),  # 47 h 59 min
        ("2026-06-12T10:00:00+02:00", 0.5),  # exactly 24 h
        ("2026-06-12T10:01:00+02:00", 0.0),  # 23 h 59 min
    ],
)
def test_refund_percent_around_thresholds(cancel_time, expected_percent):
    result = calculate_refund("CW-1001", cancel_time)

    assert result["refund_percent"] == expected_percent


@pytest.mark.parametrize("cancel_time", ["tomorrow", "2026-06-12T09:00"])
def test_invalid_cancel_time(cancel_time):
    result = calculate_refund("CW-1001", cancel_time)

    assert "error" in result