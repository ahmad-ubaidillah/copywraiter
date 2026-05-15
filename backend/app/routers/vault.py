from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VaultItem
from app.schemas import VaultItemCreate, VaultItemRead, VaultItemUpdate

router = APIRouter(prefix="/vault", tags=["Vault"])


@router.get("/", response_model=list[VaultItemRead])
async def list_vault_items(
    user_id: uuid.UUID = Query(...),
    category: str | None = None,
    is_favorite: bool | None = None,
    tag: str | None = Query(None, description="Filter by tag"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """List vault items for a user, with optional filters."""
    query = db.query(VaultItem).filter(VaultItem.user_id == user_id)

    if category is not None:
        query = query.filter(VaultItem.category == category)
    if is_favorite is not None:
        query = query.filter(VaultItem.is_favorite == is_favorite)
    if tag is not None:
        query = query.filter(VaultItem.tags.contains([tag]))

    items = query.order_by(VaultItem.updated_at.desc()).offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}", response_model=VaultItemRead)
async def get_vault_item(item_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    """Get a single vault item by ID."""
    item = db.query(VaultItem).filter(VaultItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault item not found")
    return item


@router.post("/", response_model=VaultItemRead, status_code=status.HTTP_201_CREATED)
async def create_vault_item(
    payload: VaultItemCreate,
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new vault item."""
    item = VaultItem(user_id=user_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=VaultItemRead)
async def update_vault_item(
    item_id: uuid.UUID,
    payload: VaultItemUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing vault item."""
    item = db.query(VaultItem).filter(VaultItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault item not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault_item(item_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a vault item."""
    item = db.query(VaultItem).filter(VaultItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault item not found")

    db.delete(item)
    db.commit()
