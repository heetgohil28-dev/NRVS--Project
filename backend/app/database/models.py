from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, JSON, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base
import enum


def utcnow():
    return datetime.now(timezone.utc)


class ScanStatus(str, enum.Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"


class SeverityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "informational"
    NONE     = "none"


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50), unique=True, nullable=False, index=True)
    email           = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20), default="analyst", nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime(timezone=True), default=utcnow)
    last_login      = Column(DateTime(timezone=True), nullable=True)

    scans   = relationship("ScanJob", back_populates="owner")
    reports = relationship("Report",  back_populates="owner")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id           = Column(Integer, primary_key=True, index=True)
    owner_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    targets      = Column(JSON, nullable=False)
    scan_profile = Column(String(50), default="standard")
    status       = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    progress     = Column(Integer, default=0)
    started_at   = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    raw_xml      = Column(Text, nullable=True)
    options      = Column(JSON, nullable=True)
    created_at   = Column(DateTime(timezone=True), default=utcnow)

    owner   = relationship("User",       back_populates="scans")
    hosts   = relationship("HostResult", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("Report",     back_populates="scan")


class HostResult(Base):
    __tablename__ = "host_results"

    id              = Column(Integer, primary_key=True, index=True)
    scan_id         = Column(Integer, ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    ip_address      = Column(String(45), nullable=False, index=True)
    hostname        = Column(String(255), nullable=True)
    mac_address     = Column(String(17),  nullable=True)
    vendor          = Column(String(100), nullable=True)
    os_name         = Column(String(200), nullable=True)
    os_accuracy     = Column(Integer, nullable=True)
    os_family       = Column(String(100), nullable=True)
    host_state      = Column(String(10), default="up")
    risk_score      = Column(Float, default=0.0)
    security_grade  = Column(String(2), nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    created_at      = Column(DateTime(timezone=True), default=utcnow)

    scan            = relationship("ScanJob",       back_populates="hosts")
    ports           = relationship("PortResult",    back_populates="host", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="host", cascade="all, delete-orphan")


class PortResult(Base):
    __tablename__ = "port_results"

    id                 = Column(Integer, primary_key=True, index=True)
    host_id            = Column(Integer, ForeignKey("host_results.id", ondelete="CASCADE"), nullable=False)
    port_number        = Column(Integer, nullable=False)
    protocol           = Column(String(10), default="tcp")
    state              = Column(String(20), nullable=False)
    service_name       = Column(String(100), nullable=True)
    service_version    = Column(String(200), nullable=True)
    service_product    = Column(String(200), nullable=True)
    service_extra_info = Column(String(500), nullable=True)
    cpe                = Column(String(500), nullable=True)
    banner             = Column(Text, nullable=True)
    script_output      = Column(JSON, nullable=True)

    host = relationship("HostResult", back_populates="ports")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id               = Column(Integer, primary_key=True, index=True)
    host_id          = Column(Integer, ForeignKey("host_results.id", ondelete="CASCADE"), nullable=False)
    cve_id           = Column(String(20), nullable=False, index=True)
    cvss_v3_score    = Column(Float, nullable=True)
    cvss_v2_score    = Column(Float, nullable=True)
    cvss_vector      = Column(String(200), nullable=True)
    severity         = Column(SAEnum(SeverityLevel), nullable=True)
    description      = Column(Text, nullable=True)
    published_date   = Column(DateTime(timezone=True), nullable=True)
    references       = Column(JSON, nullable=True)
    affected_cpe     = Column(JSON, nullable=True)
    mitre_tactics    = Column(JSON, nullable=True)
    mitre_techniques = Column(JSON, nullable=True)
    exploit_available  = Column(Boolean, default=False)
    exploit_details    = Column(JSON, nullable=True)
    recommendation     = Column(Text, nullable=True)
    patch_available    = Column(Boolean, nullable=True)
    created_at         = Column(DateTime(timezone=True), default=utcnow)

    host = relationship("HostResult", back_populates="vulnerabilities")


class Report(Base):
    __tablename__ = "reports"

    id                = Column(Integer, primary_key=True, index=True)
    scan_id           = Column(Integer, ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    owner_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_type       = Column(String(10), nullable=False)
    file_path         = Column(String(500), nullable=True)
    file_size         = Column(Integer, nullable=True)
    executive_summary = Column(Text, nullable=True)
    total_hosts       = Column(Integer, default=0)
    total_vulns       = Column(Integer, default=0)
    critical_count    = Column(Integer, default=0)
    high_count        = Column(Integer, default=0)
    medium_count      = Column(Integer, default=0)
    low_count         = Column(Integer, default=0)
    created_at        = Column(DateTime(timezone=True), default=utcnow)

    scan  = relationship("ScanJob", back_populates="reports")
    owner = relationship("User",    back_populates="reports")


class Asset(Base):
    __tablename__ = "assets"

    id              = Column(Integer, primary_key=True, index=True)
    ip_address      = Column(String(45), unique=True, nullable=False, index=True)
    hostname        = Column(String(255), nullable=True)
    asset_type      = Column(String(50),  nullable=True)
    os_name         = Column(String(200), nullable=True)
    owner_team      = Column(String(100), nullable=True)
    criticality     = Column(String(20),  default="medium")
    tags            = Column(JSON, nullable=True)
    first_seen      = Column(DateTime(timezone=True), default=utcnow)
    last_seen       = Column(DateTime(timezone=True), default=utcnow)
    last_risk_score = Column(Float, default=0.0)
    notes           = Column(Text, nullable=True)
