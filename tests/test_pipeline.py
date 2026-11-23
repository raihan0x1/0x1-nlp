"""Pipeline public contract: config dict, step order, known steps."""

import re

import pytest

from ox1nlp.preprocessing import Pipeline


def test_process_empty_string_returns_empty():
    pipeline = Pipeline({"clean_html": True})
    assert pipeline.process("") == ""


def test_unknown_step_raises_value_error():
    with pytest.raises(ValueError, match="Unknown preprocessing steps"):
        Pipeline({"not_a_real_step": True})


def test_clean_html_strips_tags():
    pipeline = Pipeline({"clean_html": True})
    assert pipeline.process("<p>Hello <b>World</b></p>") == "Hello World"


def test_remove_urls_drops_the_url():
    pipeline = Pipeline({"remove_urls": True})
    result = pipeline.process("Visit https://example.com for more")
    assert "https://" not in result
    assert "Visit" in result
    assert "for more" in result


def test_spell_corrector_sentence_expands_slang():
    pipeline = Pipeline({"spell_corrector_sentence": True})
    result = pipeline.process("yg gk")
    assert result == "yang tidak"


def test_disabled_steps_are_skipped():
    pipeline = Pipeline({"clean_html": False, "remove_urls": True})
    result = pipeline.process("<p>Visit https://example.com</p>")
    assert "<p>" in result
    assert "https://" not in result


def test_tokenizer_returns_a_list_of_tokens():
    pipeline = Pipeline({"tokenizer": True})
    assert pipeline.process("satu dua tiga") == ["satu", "dua", "tiga"]


def test_update_config_rebuilds_enabled_steps():
    pipeline = Pipeline({"clean_html": True})
    pipeline.update_config({"remove_punctuation": True})
    assert pipeline.get_enabled_steps() == ["clean_html", "remove_punctuation"]
    assert pipeline.process("<p>Hello!</p>") == "Hello"


NUMBERS_TEXT = "Target 2.000 lokasi pada 2027, naik 15 persen di 1111 desa"
# Steps whose job is to drop or convert numbers.
CHANGES_NUMBERS = {"remove_numbers", "text_to_emoji"}


def test_steps_keep_the_digits_they_are_not_meant_to_touch():
    digits = re.findall(r"\d", NUMBERS_TEXT)
    for step in sorted(set(Pipeline.get_available_steps()) - CHANGES_NUMBERS):
        out = Pipeline({step: True}).process(NUMBERS_TEXT)
        assert re.findall(r"\d", str(out)) == digits, step


def test_remove_currency_drops_only_currency_amounts():
    out = Pipeline({"remove_currency": True}).process("harga Rp1.500.000 atau $20 untuk 2027")
    assert out == "harga atau untuk 2027"
