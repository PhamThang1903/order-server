from __future__ import annotations
import logging
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from firebase_admin import messaging
from app.db.models.user import User
from app.db.models.order import Order

logger = logging.getLogger(__name__)


def get_target_fcm_tokens(db: Session, order: Order) -> list[str]:
    stmt = select(User.fcm_token).where(
        (User.role == "admin") | (User.id == order.customer_id),
        User.fcm_token.isnot(None),
        User.is_active == True,
    )
    return list(db.execute(stmt).scalars().all())


def get_admin_fcm_tokens(db: Session) -> list[str]:
    stmt = select(User.fcm_token).where(
        User.role == "admin",
        User.fcm_token.isnot(None),
        User.is_active == True,
    )
    return list(db.execute(stmt).scalars().all())


def notify_status_or_location_changed(
    db: Session, order: Order, new_status: str | None, new_location: str | None
) -> None:
    tokens = get_target_fcm_tokens(db, order)
    if not tokens:
        return

    if new_status and new_location:
        body = f"Đơn #{order.order_code} → {new_status.upper()} • {new_location}"
    elif new_status:
        body = f"Đơn #{order.order_code} → {new_status.upper()} • {order.tracking_provider or 'carrier'} đang vận chuyển"
    else:
        body = f"Đơn #{order.order_code} • Vị trí mới: {new_location}"

    title = "Đơn hàng cập nhật"
    if new_status == "delivered":
        title = "Đã giao thành công ✓"

    send_multicast_fcm(tokens, "STATUS_CHANGED", str(order.id), title, body)


def notify_tracking_error(db: Session, order: Order) -> None:
    tokens = get_admin_fcm_tokens(db)
    if not tokens:
        return

    body = f"Không thể theo dõi đơn #{order.order_code} sau 3 lần thử – kiểm tra URL"
    send_multicast_fcm(tokens, "TRACKING_ERROR", str(order.id), "⚠️ Lỗi theo dõi đơn hàng", body)


def notify_sync_conflict(db: Session, user_id: UUID, order: Order) -> None:
    user = db.get(User, user_id)
    if not user or not user.fcm_token:
        return

    body = f"Mâu thuẫn dữ liệu tại đơn #{order.order_code}. Bản server được ưu tiên."
    send_single_fcm(user.fcm_token, "SYNC_CONFLICT", str(order.id), "♻️ Mẫu thuẫn đồng bộ", body)


def send_multicast_fcm(tokens: list[str], type: str, order_id: str, title: str, body: str):
    message = messaging.MulticastMessage(
        tokens=tokens,
        data={"type": type, "orderId": order_id, "title": title, "body": body},
        notification=messaging.Notification(title=title, body=body),
    )
    try:
        response = messaging.send_multicast(message)
        logger.info(f"FCM Multicast sent: {response.success_count} success, {response.failure_count} failure")
    except Exception as e:
        logger.error(f"FCM Multicast failed: {e}")


def send_single_fcm(token: str, type: str, order_id: str, title: str, body: str):
    message = messaging.Message(
        token=token,
        data={"type": type, "orderId": order_id, "title": title, "body": body},
        notification=messaging.Notification(title=title, body=body),
    )
    try:
        response = messaging.send(message)
        logger.info(f"FCM Single sent: {response}")
    except Exception as e:
        logger.error(f"FCM Single failed: {e}")
