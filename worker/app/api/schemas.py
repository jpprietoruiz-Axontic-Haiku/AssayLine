from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import SpecProfile

router = APIRouter(tags=["schemas"])


@router.get("/schemas")
def list_schemas(db: Session = Depends(get_db)) -> dict[str, list[dict]]:
    """Known report types and their spec'd fields, derived from spec_profiles.

    Lets the dashboard render the right columns/edit controls per report type
    without hardcoding field lists on the frontend.
    """
    profiles = db.query(SpecProfile).order_by(SpecProfile.report_type, SpecProfile.field).all()
    schemas: dict[str, list[dict]] = {}
    for profile in profiles:
        schemas.setdefault(profile.report_type, []).append(
            {
                "field": profile.field,
                "min": float(profile.min_value) if profile.min_value is not None else None,
                "max": float(profile.max_value) if profile.max_value is not None else None,
                "unit": profile.unit,
            }
        )
    return schemas
