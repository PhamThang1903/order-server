from __future__ import annotations
from uuid import UUID
from app.schemas.tracking import TrackingResult

# Status mapping for J&T Express
# J&T spec: https://jtexpress.vn/tracking/detail?id=...
JNT_STATUS_MAP = {
    "PICKED_UP": "processing",
    "DEPARTED": "shipped",
    "ARRIVED": "shipped",
    "DELIVERING": "shipped",
    "DELIVERED": "delivered",
    "UNDELIVERED": "shipped",
    "RETURNED": "returned",
    "CANCELLED": "cancelled"
}

def parse(data: dict, order_id: UUID) -> TrackingResult:
    # J&T API response format:
    # { "status": "200", "data": { "billCode": "...", "statusName": "...", "details": [{ "status": "...", "time": "..." }] } }
    
    order_data = data.get("data", {})
    jnt_status = order_data.get("statusName")
    internal_status = JNT_STATUS_MAP.get(jnt_status)
    
    # Extract current location
    details = order_data.get("details", [])
    current_location = None
    if details:
        # Assuming last detail is newest
        current_location = details[-1].get("scanType") or details[-1].get("status")
        
    return TrackingResult(
        order_id=order_id,
        is_changed=True,
        new_status=internal_status,
        new_location=current_location,
        shipper_phone=None,
        raw_data=data
    )
