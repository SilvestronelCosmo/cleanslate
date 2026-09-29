"""CleanSlate core data models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ServiceCategory(str, Enum):
    ACCOUNT = "account"
    SUBSCRIPTION = "subscription"
    NEWSLETTER = "newsletter"
    BREACH = "breach"


class DeletionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    IMPOSSIBLE = "impossible"
    UNKNOWN = "unknown"


class ServiceEntry(BaseModel):
    name: str
    domain: str
    category: ServiceCategory
    found_via: str  # "osint", "inbox_welcome", "inbox_receipt", "inbox_unsubscribe", "breach"
    difficulty: DeletionDifficulty = DeletionDifficulty.UNKNOWN
    delete_url: Optional[str] = None
    dpo_email: Optional[str] = None
    notes: Optional[str] = None
    unsubscribe_url: Optional[str] = None
    unsubscribe_mailto: Optional[str] = None
    unsubscribe_post: bool = False  # True if RFC 8058 one-click HTTP POST is available
    last_activity: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ScanSummary(BaseModel):
    target_email: str
    total_services: int = 0
    accounts_count: int = 0
    subscriptions_count: int = 0
    newsletters_count: int = 0
    breaches_count: int = 0
    unverified: List[str] = Field(default_factory=list)
    services: List[ServiceEntry] = Field(default_factory=list)


class UnsubscribeResult(BaseModel):
    success: bool
    service: str
    method: str  # "rfc8058_post", "mailto", "link"
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class GDPRRequestPayload(BaseModel):
    user_name: str
    user_email: str
    service_name: str
    dpo_email: Optional[str] = None
    language: str = "it"  # "it" or "en"
