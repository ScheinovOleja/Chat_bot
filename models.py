from pony.orm import Database, Required, Json
from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя внутри сценария."""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """Заявки на регистрацию."""
    name = Required(str)
    departure_city = Required(str)
    destination_city = Required(str)
    departure_date = Required(str)
    num_flight = Required(str)
    num_seats = Required(str)
    comment = Required(str)
    phone_number = Required(str)


db.generate_mapping(create_tables=True)
