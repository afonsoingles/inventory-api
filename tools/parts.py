from utils.database import Database
from models.part import Part, PartAuditLogEntry, PartAuditLogAction
from errors.parts import *
from pydantic import SecretStr
import uuid
import bcrypt
import datetime

class PartTools:
    def __init__(self) -> None:
        self.db = Database()
        pass
    
    
    def create_part(self, user_id, name, sku, category_id, stock, lot_id, is_draf=False, description=None) -> Part:
        
        exists_sku_redis = self.db.redis.get(f"parts.lookup.sku:{sku}")
        if exists_sku_redis:
            raise SkuAlreadyRegistered
        
        exists_mongo = self.db.mongo.parts.find_one({"sku": sku})
        if exists_mongo:
            raise SkuAlreadyRegistered


        part_created_audit_log_entry = PartAuditLogEntry(
            action=PartAuditLogAction.CREATED if not is_draf else PartAuditLogAction.CREATED_AS_DRAFT,
            user_id=user_id,
            message="Created this part." if not is_draf else "Created this part as draft."
        )
        
        part = Part(
            name=name,
            sku=sku,
            category=category_id,
            stock_in_use=0,
            stock_available=stock,
            stock_ordered=0,
            lots=[lot_id],
            draft=is_draf,
            description=description,
            audit_log=[part_created_audit_log_entry]
        )

        part_dict = part.model_dump()
        part_dict["_id"] = part.id  

        self.db.mongo.parts.insert_one(part_dict)

        self.db.redis.set(f"parts.part:{part.id}", part.model_dump_json(), ex=10800)
        self.db.redis.set(f"parts.lookup.sku:{part.sku}", str(part.id), ex=10800)

        return Part.model_validate(part_dict)

    def get_all_parts(self) -> list[Part]: # DEMO / TEMPORARY. DO NOT USE WIDELY.
        parts = []
        for part in self.db.mongo.parts.find():
            parts.append(Part.model_validate(part))
        return parts
    
    
    def get_part_by_id(self, id) -> Part:

        redis_part = self.db.redis.get(f"parts.part:{id}")
        if redis_part:
            return Part.model_validate_json(redis_part)
        
        raw = self.db.mongo.parts.find_one({"id": id})

        if not raw:
            raise PartNotFound
        
        part = Part.model_validate(raw)

        self.db.redis.set(f"parts.part:{id}", part.model_dump_json(), ex=10800)
        self.db.redis.set(f"parts.lookup.sku:{part.sku}", id, ex=10800)
        return part

    def get_part_by_sku(self, sku) -> Part:
        
        redis_id = self.db.redis.get(f"parts.lookup.sku:{sku}")
        if redis_id:
            return self.get_part_by_id(redis_id)
        
        raw = self.db.mongo.parts.find_one({"sku": sku})
        if not raw:
            raise PartNotFound
        
        part = Part.model_validate(raw)

        self.db.redis.set(f"parts.part:{str(part)}", part.model_dump_json(), ex=10800)
        self.db.redis.set(f"parts.lookup.sku:{sku}", str(part.id), ex=10800)

      
        return part