from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class CriticalityLevel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class AssetUpdate(BaseModel):
    asset_type:  Optional[str]              = None
    owner_team:  Optional[str]              = None
    criticality: Optional[CriticalityLevel] = None
    tags:        Optional[List[str]]        = None
    notes:       Optional[str]              = None
