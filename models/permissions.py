from typing import Literal, Union, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid

class AdminPermissions(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

class UserPermissions(Enum):
    READ = "read"
    UPDATE = "update"

class GuestPermissions(Enum):
    READ = "read"
