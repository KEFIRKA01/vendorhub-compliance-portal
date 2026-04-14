from __future__ import annotations

from typing import Any

from .domain import SupplierCard, SupplierStore, approval_path, completeness, escalation_reason, required_documents, risk_score

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    FastAPI = None
    BaseModel = object


class SupplierPayload(BaseModel):
    supplier_id: str
    name: str
    category: str
    countries: list[str]
    documents: list[str] = []
    flags: list[str] = []


class AssignPayload(BaseModel):
    owner: str


store = SupplierStore()
app = FastAPI(title="VendorHub Compliance Portal") if FastAPI else None


if app:
    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}


    @app.get("/summary")
    def summary() -> dict[str, int]:
        return store.summary()


    @app.get("/suppliers")
    def list_suppliers() -> list[dict[str, Any]]:
        return [
            {
                "supplier_id": card.supplier_id,
                "name": card.name,
                "risk_score": risk_score(card),
                "required_documents": required_documents(card),
                "completeness": completeness(card),
                "approval_path": approval_path(card),
                "escalation_reason": escalation_reason(card),
            }
            for card in store.all_cards()
        ]


    @app.post("/suppliers")
    def create_supplier(payload: SupplierPayload) -> dict[str, str]:
        store.add(SupplierCard(**payload.model_dump()))
        return {"supplier_id": payload.supplier_id}


    @app.post("/suppliers/{supplier_id}/assign")
    def assign_supplier(supplier_id: str, payload: AssignPayload) -> dict[str, str]:
        store.assign(supplier_id, payload.owner)
        return {"supplier_id": supplier_id, "assigned_to": payload.owner}
