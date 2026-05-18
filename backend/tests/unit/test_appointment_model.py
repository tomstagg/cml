from app.models.appointment import Appointment


def test_appointment_has_preferred_callback_window_column():
    col = Appointment.__table__.c.preferred_callback_window
    assert col.nullable is True
    assert str(col.type) == "VARCHAR(16)"
