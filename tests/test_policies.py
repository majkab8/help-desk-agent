import pytest
from agent.tools.policies import split_policies_into_sections, split_text_into_words, search_policies


def test_sections_amount():
    result = split_policies_into_sections()

    assert len(result) == 22


def test_prices_md_header_exists():
    result = split_policies_into_sections()

    prices_section = next(
        (section for section in result if section["header"] == "Prices"), None,
    )

    assert prices_section is not None
    assert "EUR" in prices_section["content"]


def test_last_section_exists():
    result = split_policies_into_sections()
    headers = [section["header"] for section in result]

    assert "Do you sell bikes?" in headers


def test_headers_are_clear_from_hashtag():
    result = split_policies_into_sections()
    headers = [section["header"] for section in result]

    assert all(not header.startswith("#") for header in headers)

def test_split_text_into_words_normalizes_question():
    words = split_text_into_words("What is the deposit for an E-bike?")

    assert {"depo", "elec", "bike"} <= words
    assert "the" not in words
    assert "is" not in words


def test_e_bike_and_electric_bike_give_same_words():
    assert split_text_into_words("e-bike") == split_text_into_words("Electric bike")

@pytest.mark.parametrize(
    "query, expected_header",
    [
        ("opening hours", "When are you open?"),
        ("deposit e-bike", "Deposit"),
        ("cancel refund", "Cancelling a booking"),
        ("helmet", "Do I have to wear a helmet?"),
    ],
)
def test_search_finds_right_section(query, expected_header):
    result = search_policies(query)

    assert result["results"][0]["header"] == expected_header

def test_search_without_match_returns_error():
    result = search_policies("pizza")

    assert result["results"] == []
    assert "error" in result


def test_search_returns_at_most_three_results():
    result = search_policies("bike")

    assert len(result["results"]) <= 3