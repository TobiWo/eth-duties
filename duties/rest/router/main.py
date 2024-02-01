"""FastAPI router module
"""

from fastapi import APIRouter

from duties.rest.router.duties.any import any_duties_router
from duties.rest.router.duties.raw import raw_duties_router
from duties.rest.router.validator import validator_router

router = APIRouter(prefix="")

router.include_router(raw_duties_router)
router.include_router(any_duties_router)
router.include_router(validator_router)
router.include_router(validator_router)
