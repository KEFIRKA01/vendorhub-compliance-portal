from datetime import datetime, timedelta, timezone

from app.domain import SupplierCard, SupplierStore, approval_path, completeness, escalation_reason, required_documents, risk_score


def test_required_documents_expand_for_international_white_label() -> None:
    card = SupplierCard(
        supplier_id="sup-1",
        name="Brand OEM",
        category="manufacturing",
        countries=["ru", "ae"],
        flags=["white_label"],
    )
    docs = required_documents(card)
    assert "intl_compliance.pdf" in docs
    assert "brand_guidelines.pdf" in docs


def test_risk_score_and_approval_path_for_sensitive_payment_supplier() -> None:
    card = SupplierCard(
        supplier_id="sup-2",
        name="Global Pay",
        category="payment",
        countries=["ru", "ae"],
        flags=["sensitive_access"],
    )
    assert risk_score(card) >= 65
    assert {"manager", "legal", "security"} <= set(approval_path(card))


def test_escalation_and_summary() -> None:
    stale = datetime.now(timezone.utc) - timedelta(hours=72)
    card = SupplierCard(
        supplier_id="sup-3",
        name="No Owner",
        category="security",
        countries=["ru", "kz"],
        updated_at=stale,
        created_at=stale,
    )
    store = SupplierStore()
    store.add(card)
    assert escalation_reason(card) is not None
    assert completeness(card) == 0
    assert store.summary()["needs_escalation"] == 1
