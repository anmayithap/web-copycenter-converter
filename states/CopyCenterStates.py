from aiogram.dispatcher.filters.state import State, StatesGroup


class CopyCenterState(StatesGroup):
    choice_methods = State()
    street = State()
    city = State()
    house = State()
    cancel = State()
    back = State()
    download = State()
    choice_print_methods = State()
    wait_edit_params = State()
    wait_pages_params = State()
    wait_double_could_params = State()
    wait_location = State()
