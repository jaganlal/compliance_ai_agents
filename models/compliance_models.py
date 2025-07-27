"""
Data models for compliance monitoring system
"""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ComplianceStatus(Enum):
    """Compliance status enumeration."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL_COMPLIANCE = "partial_compliance"
    UNKNOWN = "unknown"

class AgentMessage(BaseModel):
    """Message structure for agent-to-agent communication."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    sender_id: str
    recipient_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = Field(default=1, ge=1, le=5)
    expires_at: Optional[datetime] = None

class ComplianceWorkflow(BaseModel):
    """Compliance monitoring workflow model."""
    workflow_id: str
    store_id: Optional[str] = None
    date: date
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
  
    class Config:
        use_enum_values = True

class ComplianceViolation(BaseModel):
    """Compliance violation model."""
    violation_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    store_id: str
    violation_type: str
    severity: str  # low, medium, high, critical
    description: str
    detected_at: datetime
    image_url: Optional[str] = None
    planogram_reference: Optional[str] = None
    contract_reference: Optional[str] = None
  
class ComplianceReport(BaseModel):
    """Compliance report model."""
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    store_id: Optional[str] = None
    date: date
    compliance_score: float = Field(ge=0.0, le=100.0)
    status: ComplianceStatus
    violations: List[ComplianceViolation] = []
    recommendations: List[str] = []
    generated_at: datetime
  
    class Config:
        use_enum_values = True

class StoreImage(BaseModel):
    """Store image model."""
    image_id: str = Field(default_factory=lambda: str(uuid4()))
    store_id: str
    image_url: str
    captured_at: datetime
    section: Optional[str] = None  # e.g., "beverage_aisle", "checkout"
    processed: bool = False
    analysis_result: Optional[Dict[str, Any]] = None

class Contract(BaseModel):
    """Contract model."""
    contract_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    store_id: Optional[str] = None
    effective_date: date
    expiry_date: Optional[date] = None
    content: str
    compliance_rules: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

class Planogram(BaseModel):
    """Planogram model."""
    planogram_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    store_id: Optional[str] = None
    section: str
    layout_data: Dict[str, Any]
    effective_date: date
    version: str = "1.0"
    created_at: datetime
    updated_at: datetime