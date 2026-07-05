from utils.database import Database
from models.user import User, SafeUser
from errors.user import EmailAlreadyRegisteredError, UserNotFoundError
from pydantic import SecretStr
import uuid
import bcrypt
import datetime

class UserTools:
    def __init__(self) -> None:
        self.db = Database()
        pass
    
    def _hash_password(self, password) -> str:
        salt = bcrypt.gensalt(rounds=12)
        result = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        return result
    
    def verify_password_hash(self, password, hashed) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    
    def create_user(self, name, email, password) -> EmailAlreadyRegisteredError | User:
        
        exists_redis = self.db.redis.get(f"users.lookup.email:{email}")
        if exists_redis:
            raise EmailAlreadyRegisteredError
        
        exists_mongo = self.db.mongo.users.find_one({"email": email})
        if exists_mongo:
            raise EmailAlreadyRegisteredError
        
        hashed_password = self._hash_password(password)

        user = User(
            name=name,
            email=email,
            password=SecretStr(hashed_password),
        )

        user_dict = user.model_dump()
        user_dict["_id"] = user.id  # MongoDB requires _id for some reason. It should not be used in the code.

        self.db.mongo.users.insert_one(user_dict)

        self.db.redis.set(f"users.user:{user.id}", user.model_dump_json(), ex=10800)
        self.db.redis.set(f"users.lookup.email:{email}", str(user.id), ex=10800)

        return User.model_validate(user_dict)

    def get_user_by_id(self, id) -> User:

        redis_user = self.db.redis.get(f"users.user:{id}")
        if redis_user:
            return User.model_validate_json(redis_user)
        
        raw = self.db.mongo.users.find_one({"id": id})

        if not raw:
            raise UserNotFoundError
        
        user = User.model_validate(raw)

        self.db.redis.set(f"users.user:{id}", user.model_dump_json(), ex=10800)
        self.db.redis.set(f"users.lookup.email:{user.email}", id, ex=10800)
        return user

    def get_user_by_email(self, email) -> User:
        
        redis_id = self.db.redis.get(f"users.lookup.email:{email}")
        if redis_id:
            return self.get_user_by_id(redis_id)
        
        raw = self.db.mongo.users.find_one({"email": email})
        if not raw:
            raise UserNotFoundError
        
        user = User.model_validate(raw)

        self.db.redis.set(f"users.user:{user.id}", user.model_dump_json(), ex=10800)
        self.db.redis.set(f"users.lookup.email:{email}", user.id, ex=10800)

      
        return user









    def update_user(self, id, data):
        user = self._get_user_model(id)

        if user is None:
            return "not_found"
        
        user_dict = user.model_dump()
        for key in data:
            if key not in ["suspended", "permissions", "admin", "superadmin", "password", "email", "created_at", "updated_at", "id"]:
                user_dict[key] = data[key]
            else:
                return "protected_field"
        
        user_dict["updated_at"] = datetime.datetime.now(datetime.timezone.utc)

        user = User.model_validate(user_dict)
        updated_dict = user.model_dump()

        self.db.mongo.users.update_one({"id": id}, {"$set": updated_dict})
        self.db.redis.set(f"users.user:{id}", user.model_dump_json(), ex=10800)
        self.db.redis.set(f"users.lookup.email:{user.email}", id, ex=10800)
        return "user_updated"