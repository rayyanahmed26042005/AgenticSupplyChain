"""
Supply Chain Data Schemas.
Defines expected data structures for products, suppliers, shipments, etc.
"""

from typing import Dict, List, Any


SUPPLY_CHAIN_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "products": {
        "required_columns": ["product_id", "product_name", "category"],
        "optional_columns": ["price", "cost", "weight", "sku"],
        "column_types": {
            "product_id": "str",
            "product_name": "str",
            "category": "str",
            "price": "float",
            "cost": "float",
        },
    },
    "suppliers": {
        "required_columns": ["supplier_id", "supplier_name"],
        "optional_columns": [
            "location",
            "lead_time",
            "defect_rate",
            "reliability_score",
            "contact_email",
        ],
        "column_types": {
            "supplier_id": "str",
            "supplier_name": "str",
            "lead_time": "int",
            "defect_rate": "float",
            "reliability_score": "float",
        },
    },
    "inventory": {
        "required_columns": ["product_id", "stock_levels"],
        "optional_columns": [
            "warehouse_id",
            "reorder_point",
            "safety_stock",
            "last_updated",
        ],
        "column_types": {
            "product_id": "str",
            "stock_levels": "int",
            "reorder_point": "int",
            "safety_stock": "int",
        },
    },
    "shipments": {
        "required_columns": ["shipment_id", "product_id", "quantity"],
        "optional_columns": [
            "origin",
            "destination",
            "ship_date",
            "delivery_date",
            "carrier",
            "status",
        ],
        "column_types": {
            "shipment_id": "str",
            "product_id": "str",
            "quantity": "int",
        },
    },
    "orders": {
        "required_columns": ["order_id", "product_id", "quantity", "order_date"],
        "optional_columns": ["customer_id", "status", "total_amount", "priority"],
        "column_types": {
            "order_id": "str",
            "product_id": "str",
            "quantity": "int",
            "total_amount": "float",
        },
    },
}


def get_schema(dataset_type: str) -> Dict[str, Any]:
    """Get schema for a dataset type."""
    return SUPPLY_CHAIN_SCHEMAS.get(dataset_type, {})


def list_schemas() -> List[str]:
    """List available schema names."""
    return list(SUPPLY_CHAIN_SCHEMAS.keys())
