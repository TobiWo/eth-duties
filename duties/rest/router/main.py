"""FastAPI router module
"""

from fastapi import APIRouter
from rest.router.duties.any import any_duties_router
from rest.router.duties.raw import raw_duties_router
from rest.router.validator import validator_router

router = APIRouter(prefix="")

router.include_router(raw_duties_router)
router.include_router(any_duties_router)
router.include_router(validator_router)
