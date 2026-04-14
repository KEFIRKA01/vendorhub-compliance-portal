from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class SupplierCard:
    supplier_id: str
    name: str
    category: str
    countries: List[str]
    documents: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    status: str = "new"
    assigned_to: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


def required_documents(card: SupplierCard) -> List[str]:
    docs = {"profile.pdf", "tax_id.pdf"}
    if card.category in {"payment", "logistics"}:
        docs.add("sla.pdf")
    if len(card.countries) > 1:
        docs.add("intl_compliance.pdf")
    if "white_label" in card.flags:
        docs.add("brand_guidelines.pdf")
    return sorted(docs)


def risk_score(card: SupplierCard) -> int:
    score = 20
    if card.category in {"payment", "security"}:
        score += 30
    if len(card.countries) > 1:
        score += 15
    if "white_label" in card.flags:
        score += 10
    if "sensitive_access" in card.flags:
        score += 20
    return min(score, 100)


def approval_path(card: SupplierCard) -> List[str]:
    path = ["manager"]
    if risk_score(card) >= 50:
        path.append("legal")
    if card.category in {"payment", "security"}:
        path.append("security")
    if "white_label" in card.flags:
        path.append("owner")
    return path


def completeness(card: SupplierCard) -> int:
    needed = set(required_documents(card))
    if not needed:
        return 100
    return round((len(needed.intersection(card.documents)) / len(needed)) * 100)


def escalation_reason(card: SupplierCard, now: datetime | None = None) -> str | None:
    current_time = now or utc_now()
    if risk_score(card) >= 70 and not card.assigned_to:
        return "Высокий риск без владельца карточки"
    if card.status in {"new", "in_review"} and current_time - card.updated_at > timedelta(hours=48):
        return "Карточка поставщика зависла больше 48 часов"
    return None


class SupplierStore:
    def __init__(self) -> None:
        self._cards: Dict[str, SupplierCard] = {}

    def add(self, card: SupplierCard) -> None:
        self._cards[card.supplier_id] = card

    def get(self, supplier_id: str) -> SupplierCard:
        return self._cards[supplier_id]

    def assign(self, supplier_id: str, owner: str) -> None:
        card = self._cards[supplier_id]
        card.assigned_to = owner
        card.updated_at = utc_now()

    def all_cards(self) -> List[SupplierCard]:
        return sorted(self._cards.values(), key=lambda card: (risk_score(card), card.updated_at), reverse=True)

    def summary(self) -> Dict[str, int]:
        cards = list(self._cards.values())
        return {
            "total": len(cards),
            "high_risk": len([card for card in cards if risk_score(card) >= 70]),
            "needs_escalation": len([card for card in cards if escalation_reason(card)]),
        }
