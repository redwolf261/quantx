"""AI Explainer API route."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.schemas import ExplainRequest, ExplainResponse
from app.engines.explainer import ExplainerEngine

router = APIRouter()

_explainer = ExplainerEngine()


@router.post("", response_model=ExplainResponse)
async def explain(
    body: ExplainRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await _explainer.explain(
        context_type=body.context_type,
        structured_data=body.structured_data,
        goal_name=body.goal_name,
        user_name=body.user_name or current_user.full_name,
    )
    return ExplainResponse(**result)
