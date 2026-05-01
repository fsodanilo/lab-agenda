from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application.errors import AppointmentNotFoundError
from app.application.use_cases.create_appointment import (
    CreateAppointmentCommand,
    CreateAppointmentUseCase,
)
from app.application.use_cases.delete_appointment import DeleteAppointmentUseCase
from app.application.use_cases.get_appointment import GetAppointmentUseCase
from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.application.use_cases.update_appointment import (
    UpdateAppointmentCommand,
    UpdateAppointmentUseCase,
)
from app.infrastructure.dependencies import (
    get_create_appointment_use_case,
    get_delete_appointment_use_case,
    get_get_appointment_use_case,
    get_list_appointments_use_case,
    get_update_appointment_use_case,
)
from app.presentation.api.schemas.appointment import (
    AppointmentResponse,
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _raise_not_found_http_error(error: AppointmentNotFoundError) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Appointment {error.appointment_id} not found",
    ) from error


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: CreateAppointmentRequest,
    use_case: CreateAppointmentUseCase = Depends(get_create_appointment_use_case),
) -> AppointmentResponse:
    result = await use_case.execute(
        CreateAppointmentCommand(
            user_id=payload.user_id,
            datetime=payload.datetime,
            status=payload.status,
            notes=payload.notes,
        )
    )
    return AppointmentResponse.model_validate(result)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    use_case: GetAppointmentUseCase = Depends(get_get_appointment_use_case),
) -> AppointmentResponse:
    try:
        result = await use_case.execute(appointment_id)
    except AppointmentNotFoundError as error:
        _raise_not_found_http_error(error)
    return AppointmentResponse.model_validate(result)


@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(
    user_id: str | None = Query(default=None),
    use_case: ListAppointmentsUseCase = Depends(get_list_appointments_use_case),
) -> list[AppointmentResponse]:
    result = await use_case.execute(user_id=user_id)
    return [AppointmentResponse.model_validate(item) for item in result]


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    payload: UpdateAppointmentRequest,
    use_case: UpdateAppointmentUseCase = Depends(get_update_appointment_use_case),
) -> AppointmentResponse:
    try:
        result = await use_case.execute(
            UpdateAppointmentCommand(
                appointment_id=appointment_id,
                user_id=payload.user_id,
                datetime=payload.datetime,
                status=payload.status,
                notes=payload.notes,
            )
        )
    except AppointmentNotFoundError as error:
        _raise_not_found_http_error(error)
    return AppointmentResponse.model_validate(result)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    use_case: DeleteAppointmentUseCase = Depends(get_delete_appointment_use_case),
) -> Response:
    try:
        await use_case.execute(appointment_id)
    except AppointmentNotFoundError as error:
        _raise_not_found_http_error(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)