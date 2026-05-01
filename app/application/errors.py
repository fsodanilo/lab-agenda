class AppointmentNotFoundError(Exception):
    def __init__(self, appointment_id: str) -> None:
        super().__init__(f"appointment_not_found:{appointment_id}")
        self.appointment_id = appointment_id
