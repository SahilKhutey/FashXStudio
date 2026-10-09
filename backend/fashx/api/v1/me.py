from fastapi import APIRouter, Depends
from pydantic import BaseModel

from fashx.security.deps import Principal, get_principal

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    user_id: str
    roles: list[str]


@router.get("/me", response_model=MeResponse)
async def get_me(principal: Principal = Depends(get_principal)) -> MeResponse:
    return MeResponse(
        user_id=principal.user_id,
        roles=sorted(principal.roles),
    )
