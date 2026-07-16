from errors.base import BaseError

class SkuAlreadyRegistered(BaseError):
    status_code = 400
    code = "sku_already_registered"
    message = "This SKU is already registered."

class StockMustBeInteger(BaseError):
    status_code = 400
    code = "stock_must_be_integer"
    message = "Stock must be an integer."

class PartNotFound(BaseError):
    status_code = 404
    code = "part_not_found"
    message = "Part not found."