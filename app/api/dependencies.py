# app/api/dependencies.py

from fastapi import Header, HTTPException
from typing import Optional
from app.utils.config import get_settings
from app.services.health import HealthChecker  # Add this import

async def get_current_tenant(
    x_tenant_id: Optional[str] = Header(None)
) -> str:
    """Get current tenant ID from request header."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID header is required"
        )
    return x_tenant_id

async def get_health_checker() -> HealthChecker:
    """
    Dependency for getting health checker instance.
    
    Returns:
        HealthChecker: Instance of health checker service
    """
    return HealthChecker()