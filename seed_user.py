import argparse
import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from pydantic import SecretStr

from models.user import User
from tools.users import UserTools
from utils.database import Database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed a user into MongoDB and Redis.")
    parser.add_argument("--name", default=os.environ.get("SEED_USER_NAME", "Seed User"))
    parser.add_argument("--email", default=os.environ.get("SEED_USER_EMAIL", "seed@example.com"))
    parser.add_argument("--password", default=os.environ.get("SEED_USER_PASSWORD", "password123"))
    parser.add_argument("--admin", action="store_true", default=os.environ.get("SEED_USER_ADMIN", "false").lower() == "true")
    parser.add_argument("--superadmin", action="store_true", default=os.environ.get("SEED_USER_SUPERADMIN", "false").lower() == "true")
    return parser.parse_args()


def build_user(args: argparse.Namespace, user_tools: UserTools) -> User:
    hashed_password = user_tools._hash_password(args.password)

    return User(
        name=args.name,
        email=args.email,
        password=SecretStr(hashed_password),
        admin=args.admin,
        superadmin=args.superadmin,
    )


def seed_user() -> User:
    load_dotenv()
    args = parse_args()

    user_tools = UserTools()
    db = Database()
    user = build_user(args, user_tools)
    password_hash = user.password.get_secret_value()
    user_dict = user.model_dump()
    user_dict["password"] = password_hash
    user_dict["_id"] = user.id

    existing_user = db.mongo.users.find_one({"email": user.email})

    if existing_user:
        user_dict["_id"] = existing_user.get("_id", user.id)
        db.mongo.users.update_one({"email": user.email}, {"$set": user_dict})
        action = "updated"
    else:
        db.mongo.users.insert_one(user_dict)
        action = "inserted"

    cache_user = dict(user_dict)
    cache_user.pop("_id", None)
    db.redis.set(f"users.user:{user.id}", json.dumps(cache_user, default=str), ex=10800)
    db.redis.set(f"users.lookup.email:{user.email}", str(user.id), ex=10800)

    print(f"User {action}: {user.email}")
    return user


if __name__ == "__main__":
    seed_user()