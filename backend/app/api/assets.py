from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.database.connection import get_db
from app.database.models import Asset
from app.api.auth import get_current_user
from app.database.models import User
from app.schemas.asset import AssetUpdate, CriticalityLevel

router = APIRouter(prefix="/assets", tags=["Asset Inventory"])


@router.get("/")
def list_assets(
    criticality: Optional[CriticalityLevel] = Query(None),
    asset_type:  Optional[str]              = Query(None),
    search:      Optional[str]              = Query(None),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    q = db.query(Asset)
    if criticality:
        q = q.filter(Asset.criticality == criticality)
    if asset_type:
        q = q.filter(Asset.asset_type == asset_type)
    if search:
        q = q.filter(
            Asset.ip_address.ilike(f"%{search}%") |
            Asset.hostname.ilike(f"%{search}%")
        )
    assets = q.order_by(Asset.last_risk_score.desc()).all()
    return {
        "total": len(assets),
        "assets": [
            {
                "id":              a.id,
                "ip_address":      a.ip_address,
                "hostname":        a.hostname,
                "os_name":         a.os_name,
                "asset_type":      a.asset_type,
                "owner_team":      a.owner_team,
                "criticality":     a.criticality,
                "tags":            a.tags,
                "last_risk_score": a.last_risk_score,
                "first_seen":      a.first_seen,
                "last_seen":       a.last_seen,
            }
            for a in assets
        ]
    }


@router.get("/stats/summary")
def asset_summary(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    total     = db.query(func.count(Asset.id)).scalar()
    critical  = db.query(func.count(Asset.id)).filter(Asset.criticality == "critical").scalar()
    high      = db.query(func.count(Asset.id)).filter(Asset.criticality == "high").scalar()
    medium    = db.query(func.count(Asset.id)).filter(Asset.criticality == "medium").scalar()
    low       = db.query(func.count(Asset.id)).filter(Asset.criticality == "low").scalar()
    high_risk = db.query(func.count(Asset.id)).filter(Asset.last_risk_score >= 60).scalar()
    return {
        "total_assets":    total,
        "critical_assets": critical,
        "high_risk":       high_risk,
        "by_criticality": {
            "critical": critical,
            "high":     high,
            "medium":   medium,
            "low":      low,
        }
    }


@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/{asset_id}")
def update_asset(
    asset_id: int,
    data:         AssetUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return {"message": "Asset updated", "asset_id": asset_id}


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()
    return {"message": f"Asset {asset_id} deleted"}
