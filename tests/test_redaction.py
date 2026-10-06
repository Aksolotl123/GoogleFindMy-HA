# tests/test_redaction.py
"""Tests for the dependency-free redaction helpers in ``redaction``."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from custom_components.googlefindmy import redaction
from custom_components.googlefindmy.redaction import (
    REDACTED,
    async_redact_data,
    describe_keys,
    describe_payload,
)


def test_redacts_matching_keys_at_any_depth() -> None:
    data = {
        "keep": "visible",
        "vaultKeys": "super-secret",
        "nested": {"vaultKeys": "also-secret", "other": 1},
        "listed": [{"vaultKeys": "third"}],
    }

    result = async_redact_data(data, {"vaultKeys"})

    assert result["keep"] == "visible"
    assert result["vaultKeys"] == REDACTED
    assert result["nested"]["vaultKeys"] == REDACTED
    assert result["nested"]["other"] == 1
    assert result["listed"][0]["vaultKeys"] == REDACTED
    # the input is left untouched
    assert data["vaultKeys"] == "super-secret"


def test_passes_through_scalars_and_keeps_empty_values() -> None:
    assert async_redact_data("plain", {"plain"}) == "plain"
    assert async_redact_data({"vaultKeys": None}, {"vaultKeys"}) == {"vaultKeys": None}
    assert async_redact_data({"vaultKeys": ""}, {"vaultKeys"}) == {"vaultKeys": ""}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("abcdef", "str len=6"),
        (b"ab", "bytes len=2"),
        ({"a": 1}, "dict len=1"),
        ([], "list len=0"),
        (None, "None"),
        (123, "int"),
    ],
)
def test_describe_payload_reports_shape_never_content(
    value: object, expected: str
) -> None:
    assert describe_payload(value) == expected


def test_describe_payload_never_echoes_the_value() -> None:
    secret = "0123456789abcdef" * 4
    assert secret not in describe_payload(secret)


def test_module_stays_free_of_home_assistant_imports() -> None:
    """The CLI login run imports this module; HA must not come with it.

    Guards the layering reason this module exists at all: ``diagnostics`` pulls
    ``homeassistant.config_entries``, ``homeassistant.core`` and both registries
    at module level.
    """

    tree = ast.parse(Path(redaction.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "homeassistant" not in imported
    assert imported <= {"__future__", "collections", "re", "typing"}


def test_describe_keys_reports_names_without_values() -> None:
    payload = {"method": "x", "vaultKeys": "secret", "surprise": "also-secret"}

    described = describe_keys(payload)

    assert described == "keys=[method, surprise, vaultKeys]"
    assert "secret" not in described


def test_describe_keys_falls_back_to_shape_for_non_mappings() -> None:
    assert describe_keys(["a", "b"]) == "list len=2"
    assert describe_keys("abc") == "str len=3"


# Fork change: keys scoped by account e-mail ("<base>_<email>").


@pytest.mark.parametrize("value", [None, "", "secret-token"])
def test_email_scoped_key_is_masked_even_for_empty_values(value: object) -> None:
    """The address must leave the key name also when the value is None/""."""

    data = {"owner_key_jan@example.com": value, "plain": value}

    result = async_redact_data(data, set())

    assert result == {"owner_key_" + REDACTED: REDACTED, "plain": value}
    assert not any("example.com" in key for key in result)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("adm_token_jan_kowalski@example.com", "adm_token_" + REDACTED),
        ("spot_token_j_k_l@example.com", "spot_token_" + REDACTED),
        ("adm_token_issued_at_jan_k@example.com", "adm_token_issued_at_" + REDACTED),
        (
            "adm_probe_startup_left_jan_k@example.com",
            "adm_probe_startup_left_" + REDACTED,
        ),
        ("aas_best_ttl_sec_jan_k@example.com", "aas_best_ttl_sec_" + REDACTED),
        ("entry-x:adm_token_a_b@example.com", "entry-x:adm_token_" + REDACTED),
        # Unknown shape: the whole key is replaced.
        ("custom_jan_kowalski@example.com", REDACTED),
        ("jan_kowalski@example.com", REDACTED),
    ],
)
def test_email_with_underscore_is_masked_completely(key: str, expected: str) -> None:
    result = async_redact_data({key: "value", "nested": {key: None}}, set())

    assert result[expected] == REDACTED
    assert result["nested"] == {expected: REDACTED}
    for out_key in (*result, *result["nested"]):
        assert "jan" not in out_key
        assert "kowalski" not in out_key
        assert "example.com" not in out_key


# Fork change: key names match regardless of case and naming style; tuples are
# walked like lists.


@pytest.mark.parametrize(
    "key",
    ["Access-Token", "accessToken", "ACCESS_TOKEN", "access-token", "AccessToken"],
)
def test_key_match_ignores_case_and_naming_style(key: str) -> None:
    result = async_redact_data({key: "secret", "other": "keep"}, {"access_token"})

    assert result == {key: REDACTED, "other": "keep"}


def test_uppercase_entry_in_to_redact_matches_snake_case_key() -> None:
    result = async_redact_data({"email": "a@b.c", "Token": "t"}, {"EMAIL", "token"})

    assert result == {"email": REDACTED, "Token": REDACTED}


def test_tuples_are_redacted_like_lists() -> None:
    data = {"items": ({"token": "secret"}, "plain"), "top": ({"Email": "x"},)}

    result = async_redact_data(data, {"token", "email"})

    assert result == {
        "items": [{"token": REDACTED}, "plain"],
        "top": [{"Email": REDACTED}],
    }
    assert async_redact_data(({"token": "s"},), {"token"}) == [{"token": REDACTED}]
