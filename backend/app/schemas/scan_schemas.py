from pydantic import BaseModel, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime


ALLOWED_PROFILES = {"quick", "standard", "deep", "stealth", "vuln", "udp"}


class ScanRequest(BaseModel):
    targets: List[str]
    profile: Optional[str] = "standard"

    @field_validator("targets")
    @classmethod
    def validate_targets_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Targets list cannot be empty")
        if len(v) > 10:
            raise ValueError("Maximum 10 targets per scan")
        return [t.strip() for t in v if t.strip()]

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        if v not in ALLOWED_PROFILES:
            raise ValueError(f"Profile must be one of: {', '.join(sorted(ALLOWED_PROFILES))}")
        return v


class ScanResponse(BaseModel):
    scan_id: int
    status: str
    targets: List[str]
    profile: str
    message: str


class PortOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    port_number: int
    protocol: str
    state: str
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    service_product: Optional[str] = None
    cpe: Optional[str] = None


class HostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ip_address: str
    hostname: Optional[str] = None
    os_name: Optional[str] = None
    risk_score: float
    security_grade: Optional[str] = None
    ports: List[PortOut] = []


class ScanResultOut(BaseModel):
    scan_id: int
    total_hosts: int
    hosts: List[HostOut]


class ScanStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: int
    status: str
    progress: int
    targets: List[str]
    profile: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
