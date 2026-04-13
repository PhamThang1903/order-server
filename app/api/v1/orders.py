from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user, require_admin
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse
from app.services import order_service, storage_service
from app.db.models.user import User

router = APIRouter()


@router.post("/{order_id}/image", response_model=OrderResponse)
def upload_order_attached_image(
    order_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = db.get(order_service.Order, order_id)
    if not order or order.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    image_url = storage_service.upload_order_image(file, str(order_id))

    order.attached_image_url = image_url
    order.updated_at = datetime.now(timezone.utc)
    order.updated_by = current_user.id

    db.commit()
    db.refresh(order)

    order_resp = OrderResponse.model_validate(order)
    return order_service.apply_customer_mask(order_resp, current_user.role)


@router.get("/", response_model=OrderListResponse)
def list_orders(
    platform_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders, total = order_service.get_orders(
        db, current_user, platform_id, status_filter, from_date, to_date, search, page, limit
    )

    masked_orders = [
        order_service.apply_customer_mask(OrderResponse.model_validate(o), current_user.role)
        for o in orders
    ]
    return OrderListResponse(items=masked_orders, total=total, page=page, limit=limit)


@router.post("/", response_model=OrderResponse)
def create_new_order(
    order_in: OrderCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = order_service.create_order(db, order_in, current_user.id)
    return OrderResponse.model_validate(order)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(order_service.Order, order_id)
    if not order or order.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "customer" and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_resp = OrderResponse.model_validate(order)
    return order_service.apply_customer_mask(order_resp, current_user.role)


@router.patch("/{order_id}", response_model=OrderResponse)
def update_existing_order(
    order_id: UUID,
    order_in: OrderUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = order_service.update_order(db, order_id, order_in, current_user.id)
    return OrderResponse.model_validate(order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order_service.soft_delete_order(db, order_id, current_user.id)
    return None


@router.get("/{order_id}/history")
def get_order_history(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from app.db.models.status_history import StatusHistory

    order = db.get(order_service.Order, order_id)
    if not order or order.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "customer" and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    stmt = select(StatusHistory).where(StatusHistory.order_id == order_id).order_by(StatusHistory.changed_at.desc())
    return db.execute(stmt).scalars().all()
