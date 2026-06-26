from pydantic import BaseModel
from typing import Optional, List
from app.api.assets import CriticalityLevel


class AssetUpdate(BaseModel):
    asset_type:  Optional[str]              = None
    owner_team:  Optional[str]              = None
    criticality: Optional[CriticalityLevel] = None
    tags:        Optional[List[str]]        = None
    notes:       Optional[str]              = None
