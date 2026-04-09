from __future__ import annotations
from uuid import UUID
from app.schemas.tracking import TrackingResult

# Status mapping for GHN
# GHN spec: https://api.ghn.vn/home/docs/detail?id=83
GHN_STATUS_MAP = {
    "ready_to_pick": "processing",
    "picking": "processing",
    "picked": "processing",
    "storing": "shipped",
    "transporting": "shipped",
    "delivering": "shipped",
    "delivered": "delivered",
    "delivery_fail": "shipped",
    "returning": "returned",
    "returned": "returned",
    "cancel": "cancelled"
}

def parse(data: dict, order_id: UUID) -> TrackingResult:
    # Example expected GHN data structure:
    # { "code": 200, "data": { "status": "delivering", "log": [{ "status": "...", "updated_date": "..." }] } }
    
    order_data = data.get("data", {})
    ghn_status = order_data.get("status")
    internal_status = GHN_STATUS_MAP.get(ghn_status)
    
    # Extract current location from latest log if possible
    logs = order_data.get("log", [])
    current_location = None
    if logs:
        # Assuming last log is newest
        current_location = logs[-1].get("address") or logs[-1].get("status")
        
    return TrackingResult(
        order_id=order_id,
        is_changed=True, # Tracking service will check if this is actually different from DB
        new_status=internal_status,
        new_location=current_location,
        shipper_phone=None, # GHN doesn't always provide this in public tracking info
        raw_data=data
    )
