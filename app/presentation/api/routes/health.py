from fastapi import APIRouter, Depends, status

from app.application.use_cases.check_health import CheckHealthUseCase
from app.infrastructure.dependencies import get_check_health_use_case
from app.presentation.api.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(
    use_case: CheckHealthUseCase = Depends(get_check_health_use_case),
) -> HealthResponse:
    result = await use_case.execute()
    return HealthResponse.model_validate(result)
