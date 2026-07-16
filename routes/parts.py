from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from tools.parts import PartTools
from models.user import SafeUser
from errors.parts import *
from models.permissions import Parts
from decorators.auth import require_auth
from decorators.valid_json import valid_json


part_tools = PartTools()
router = APIRouter()


@router.post("/v1/parts")
@require_auth(permissions=[Parts.CREATE])
@valid_json(["name", "sku", "category_id", "stock", "lot_id", "is_draft"])
async def create_part(request: Request) -> JSONResponse:
    try:
        stock = int(request.state.json["stock"])
    except ValueError:
        raise StockMustBeInteger

    description = request.state.json.get("description", None)
    part = part_tools.create_part(
        user_id=request.state.user.id,
        name=request.state.json["name"],
        sku=request.state.json["sku"],
        category_id=request.state.json["category_id"],
        stock=stock,
        lot_id=request.state.json["lot_id"],
        is_draf=request.state.json["is_draft"],
        description=description
    )
    return JSONResponse({"success": True, "message": "Part created successfully", "part": part.model_dump(mode="json") }, 201)

@router.get("/v1/parts")
@require_auth(permissions=[Parts.READ])
async def get_parts(request: Request) -> JSONResponse:
    parts = part_tools.get_all_parts()
    return JSONResponse({"success": True, "message": "Parts retrieved successfully", "parts": [part.model_dump(mode="json") for part in parts]}, 200)