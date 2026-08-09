"""Local Monero address format validation.

This is basic format validation only — base58 charset, length, and prefix
character — not full base58-checksum verification like real wallet software
performs. It catches typos and wrong-coin addresses; it does not prove an
address is spendable or correctly checksummed. MacMine Lab never asks for,
stores, or transmits a seed phrase or private/spend key — only this public
address, which is all pool mining ever needs.
"""

from __future__ import annotations

from dataclasses import dataclass

# Monero (and Bitcoin-style) base58 alphabet — excludes 0, O, I, l to avoid
# visual ambiguity.
BASE58_ALPHABET = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

STANDARD_OR_SUBADDRESS_LENGTH = 95
INTEGRATED_LENGTH = 106


@dataclass
class AddressValidation:
    valid: bool
    kind: str | None  # "standard" | "subaddress" | "integrated" | None
    reason: str | None


def validate_monero_address(address: str) -> AddressValidation:
    address = address.strip()

    if not address:
        return AddressValidation(False, None, "Address is empty.")

    bad_chars = sorted(set(c for c in address if c not in BASE58_ALPHABET))
    if bad_chars:
        return AddressValidation(
            False,
            None,
            f"Contains characters not in Monero's base58 alphabet: {''.join(bad_chars)}",
        )

    if len(address) == STANDARD_OR_SUBADDRESS_LENGTH:
        if address[0] == "4":
            return AddressValidation(True, "standard", None)
        if address[0] == "8":
            return AddressValidation(True, "subaddress", None)
        return AddressValidation(
            False,
            None,
            "A 95-character address must start with '4' (standard) or '8' (subaddress); "
            f"this one starts with '{address[0]}'.",
        )

    if len(address) == INTEGRATED_LENGTH:
        if address[0] == "4":
            return AddressValidation(True, "integrated", None)
        return AddressValidation(
            False, None, f"A 106-character integrated address must start with '4', not '{address[0]}'."
        )

    return AddressValidation(
        False,
        None,
        f"Unexpected length {len(address)} — Monero standard/subaddresses are "
        f"{STANDARD_OR_SUBADDRESS_LENGTH} characters, integrated addresses are {INTEGRATED_LENGTH}.",
    )
