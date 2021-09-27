from aiogram.utils.callback_data import CallbackData

object_choice_call_back_data = CallbackData('object_choice', 'object_polling', 'object_name')
pagination_choice_call_back_data = CallbackData('pagination_choice', 'call_back', 'number')
method_choice_call_back_data = CallbackData('method_choice', 'method_name')
cancel_choice_call_back_data = CallbackData('method_choice', 'method_name')
number_choice_call_back_data = CallbackData('method_choice', 'text', 'number', 'mean')
