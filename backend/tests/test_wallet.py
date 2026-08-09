"""Tests for local Monero address format validation.

Test addresses here are synthetically constructed to have the right
shape (length + base58 charset + prefix) — this module only validates
format, so nothing here needs to be a real, spendable address.
"""

from macmine_lab.wallet import validate_monero_address

# Base58 body padding, deliberately excluding 0/O/I/l.
_PAD = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" * 3


def _standard(prefix: str) -> str:
    return prefix + _PAD[: 95 - 1]


def _integrated(prefix: str) -> str:
    return prefix + _PAD[: 106 - 1]


def test_valid_standard_address():
    result = validate_monero_address(_standard("4"))
    assert result.valid is True
    assert result.kind == "standard"
    assert result.reason is None


def test_valid_subaddress():
    result = validate_monero_address(_standard("8"))
    assert result.valid is True
    assert result.kind == "subaddress"


def test_valid_integrated_address():
    result = validate_monero_address(_integrated("4"))
    assert result.valid is True
    assert result.kind == "integrated"


def test_empty_address_invalid():
    result = validate_monero_address("")
    assert result.valid is False
    assert "empty" in result.reason.lower()


def test_whitespace_only_invalid():
    result = validate_monero_address("   ")
    assert result.valid is False


def test_wrong_prefix_at_standard_length_invalid():
    result = validate_monero_address(_standard("9"))
    assert result.valid is False
    assert "4" in result.reason and "8" in result.reason


def test_wrong_prefix_at_integrated_length_invalid():
    result = validate_monero_address(_integrated("8"))
    assert result.valid is False


def test_wrong_length_invalid():
    result = validate_monero_address("4" + _PAD[:20])
    assert result.valid is False
    assert "length" in result.reason.lower()


def test_non_base58_characters_rejected():
    # '0', 'O', 'I', 'l' are excluded from Monero's base58 alphabet.
    bad = "4" + "0" * 94
    result = validate_monero_address(bad)
    assert result.valid is False
    assert "base58" in result.reason.lower()


def test_strips_surrounding_whitespace():
    result = validate_monero_address(f"  {_standard('4')}  ")
    assert result.valid is True


def test_never_flags_placeholder_as_valid():
    # The literal placeholder MacMine Lab shows before setup — must never
    # accidentally validate as a real address.
    result = validate_monero_address("YOUR_XMR_WALLET_ADDRESS")
    assert result.valid is False
