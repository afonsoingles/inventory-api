
from pydantic import BaseModel, AwareDatetime, Field, PlainSerializer, ConfigDict, field_serializer
import datetime
from typing_extensions import Annotated
from enum import Enum
from typing import Optional
import uuid


class PartAuditLogAction(str, Enum):
    CREATED = "created"
    CREATED_AS_DRAFT = "created_as_draft"

class PartAuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore", revalidate_instances="always")

    action: PartAuditLogAction
    user_id: uuid.UUID
    message: Optional[str] = None
    timestamp: Annotated[AwareDatetime, PlainSerializer(lambda v: v.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), return_type=str)] = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class Part(BaseModel):
    # Note: add supplier_id and order_reference in a future update
    model_config = ConfigDict(extra="ignore", revalidate_instances="always")

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    sku: str
    cover_image_file_id: Optional[uuid.UUID] = None
    manufacturer: Optional[uuid.UUID] = None
    mpn: Optional[str] = None
    description: Optional[str] = None
    draft: bool
    category: uuid.UUID
    stock_in_use: int = Field(default=0)
    stock_available: int = Field(default=0)
    stock_ordered: int = Field(default=0)
    lots: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    datasheet_file_id: Optional[uuid.UUID] = None
    audit_log: list[PartAuditLogEntry] = Field(default_factory=list)
    created_at: Annotated[AwareDatetime, PlainSerializer(lambda v: v.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), return_type=str)] = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: Annotated[AwareDatetime, PlainSerializer(lambda v: v.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), return_type=str)] = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
