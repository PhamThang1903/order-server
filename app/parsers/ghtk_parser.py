from __future__ import annotations
from uuid import UUID
from app.schemas.tracking import TrackingResult

# Status mapping for GHTK
# GHTK spec: https://docs.ghtk.vn/?id=43
GHTK_STATUS_MAP = {
    "ready_to_pick": "processing",
    "picking": "processing",
    "picked": "processing",
    "transporting": "shipped",
    "delivering": "shipped",
    "delivered": "delivered",
    "delivery_fail": "shipped",
    "returning": "returned",
    "returned": "returned",
    "cancel": "cancelled"
}

def parse(data: dict, order_id: UUID) -> TrackingResult:
    # GHTK response format:
    # { "success": true, "order": { "status": "...", "status_id": ..., "log": [{ "status": "...", "updated": "..." }] } }
    
    order_data = data.get("order", {})
    ghtk_status = order_data.get("status")
    internal_status = GHTK_STATUS_MAP.get(ghtk_status)
    
    # Extract current location
    logs = order_data.get("log", [])
    current_location = None
    if logs:
        # Assuming last log is newest
        current_location = logs[-1].get("status")
        
    return TrackingResult(
        order_id=order_id,
        is_changed=True,
        new_status=internal_status,
        new_location=current_location,
        shipper_phone=None,
        raw_data=data
    )
