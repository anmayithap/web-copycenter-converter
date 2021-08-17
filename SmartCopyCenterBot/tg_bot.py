import os.path

from aiogram import Bot, Dispatcher, executor, types
from config import API_TOKEN, PAYMENTS_PROVIDER_TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from states import reques_city, locat, text_from_user, print_settings, feedback
from aiogram.dispatcher.storage import FSMContext
from keyboards import city_select_keyboard, point_select_keyboard, list_buttoncreate_keyboard, upload_select_keyboard, \
    printparam_select_keyboard, print_set_keyboard, pay_keyboard, fdbck_menu_keyboard, menu_keyboard, \
    id_select_keyboard, list_buttoncreate_fav_id_keyboard
from aiogram.types.message import ContentType
from geolocation_city_search import geoloc_city_search
from BackEnd.database_editor import DataBaseEditor
from BackEnd.editor import IMAGE_DIR, DOCUMENT_DIR, Editor, FileTypeIsNotExists
import re
from nearest_location_searcher import nearest_point_searcher

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
streetpattern = "created_streetbtb_call_\d*."
favidpattern = "created_faividbtn_call_\d*"


@dp.message_handler(commands=['start'])
async def user_location(message: types.Message):
    await bot.send_message(message.chat.id, "Отлично ✌\nВыбери свой город для начала работы",
                           reply_markup=city_select_keyboard())


@dp.callback_query_handler(lambda call: True, state="*")
async def callback_processing(callback_query: types.CallbackQuery, state: FSMContext):
    # обработка текстового ввода города
    if callback_query.data == 'cityselect_text_type':
        await bot.send_message(callback_query.from_user.id, "Введите город")
        await reques_city.city.set()
    # обработка города по геолокации
    elif callback_query.data == 'cityselect_location_type':
        await bot.send_message(callback_query.from_user.id, "Передайте свою местоположение")
        await locat.reqlocation.set()
    elif callback_query.data == 'pointselect_address_type':
        await bot.send_message(callback_query.from_user.id,
                               "Напишите название улицы, на которой стоит принтер\n Например: Карла Маркса")
        await locat.street.set()
    elif re.search(streetpattern, callback_query.data) is not None:
        async with state.proxy() as data:
            city = data['city']
            street = data['street']
        house_num = callback_query.data.replace("created_streetbtb_call_", "")
        location = (city, street, house_num)
        db = DataBaseEditor()
        printer_id = db.get_printer_by_location(location=location)  # Пашок не полнял нахуя это надо то?
        db.close_connection()
        del db
        async with state.proxy() as data:
            data["printer_id"] = printer_id
        await bot.send_message(callback_query.from_user.id, "Загрузите файл", reply_markup=upload_select_keyboard())
    elif callback_query.data == 'pointselect_id_type':
        await bot.send_message(callback_query.from_user.id, "Введите ID принтера указанный на аппарате")
        await locat.printer_id_location.set()
    elif callback_query.data == 'pointselect_favorite_type':
        user_id = callback_query.from_user.id
        db = DataBaseEditor()
        user_fav_list = db.get_favorite_printers_by_users(user_id)
        db.close_connection()
        del db
        if user_fav_list is None:
            await bot.send_message(callback_query.from_user.id,
                                   "Ваш список избранного пуст, выберите другой способ поиска принтера",
                                   reply_markup=point_select_keyboard())
        else:
            await bot.send_message(callback_query.from_user.id, "ID принтеров находящихся в вашем списке избранных",
                                   reply_markup=list_buttoncreate_fav_id_keyboard(user_fav_list))
    elif re.search(favidpattern, callback_query.data) is not None:
        prin_id = callback_query.data.replace("created_faividbtn_call_", "")
        db = DataBaseEditor()
        printer_info = db.get_printer_info_by_id(printer_id=prin_id)
        street = printer_info['street']
        house = printer_info['house']
        printer_mark = printer_info['printer_mark']
        await state.update_data(printer_id_location=prin_id)
        async with state.proxy() as data:
            data["printer_id"] = prin_id
        await bot.send_message(callback_query.from_user.id, "Точка по заданному ID",
                               reply_markup=id_select_keyboard(street, house, printer_mark))
    elif callback_query.data == 'pointselect_nearest_type':
        await bot.send_message(callback_query.from_user.id, "Передайте свое местоположение")
        await locat.tmp_location.set()
    elif callback_query.data == "choose_upload_type":
        await bot.send_message(callback_query.from_user.id,
                               ("Загрузи или перешли файл, который ты желаешь распечатать\n\n"
                                "Поддерживаемые форматы (PDF,DOC,DOCX, XLS, XLSX, PPT, PPTX, PNG, "
                                "JPG, JPEG, BMP, EPS, GIF, TXT, RTF, HTML)"))
        await text_from_user.user_text.set()
    elif callback_query.data == "printparam_set_type":
        async with state.proxy() as data:
            printer_id = data["printer_id"]
        db = DataBaseEditor()
        double_side = db.get_double_side_by_printer_id(printer_id)
        db.close_connection()
        del db
        async with state.proxy() as data:
            data["double_side"] = double_side
        if not double_side:
            await bot.send_message(callback_query.from_user.id, "Выберете параметры, которые вы хотите изменить\n"
                                                                "\n*Возможность двухсторонней печати недоступна на данном принтере\n"
                                                                "Стандартные параметры:\n"
                                                                "Количество копий: 1\n"
                                                                "Двухсторонняя печать: Нет\n"
                                                                "Отдельные страницы: Весь файл",
                                   reply_markup=print_set_keyboard(double_side))
        else:
            await bot.send_message(callback_query.from_user.id, "Выберете параметры, которые вы хотите изменить\n"
                                                                "Стандартные параметры:\n"
                                                                "Количество копий: 1\n"
                                                                "Двухсторонняя печать: Нет\n"
                                                                "Отдельные страницы: Весь файл",
                                   reply_markup=print_set_keyboard(double_side))
    elif callback_query.data == "printsettings_count_type":
        await bot.send_message(callback_query.from_user.id, "Введите количество копий")
        await print_settings.copycount.set()
    elif callback_query.data == "printsetting_doubleside_type":
        await bot.send_message(callback_query.from_user.id, "Введите 'Да' для включения двусторонней печати")
        await print_settings.doubleside.set()
    elif callback_query.data == "printsetting_needpages_type":
        await bot.send_message(callback_query.from_user.id, "Введите страницы, которые вы хотите распечатать")
        await print_settings.needpages.set()
    elif callback_query.data == "printparam_select_type" or callback_query.data == "printsetting_ready_type":
        async with state.proxy() as data:
            try:
                copycount = data[
                    "copycount"]  # параметр для передачи количества копий, если не указывается пользователем
                # ставится дефолтное значение
            except:
                copycount = 1
            try:
                needpages = data["needpages"]  # параметр для передачи нужных страниц,
                # если не указывается пользователем ставится дефолтное значение
            except:
                needpages = "Все"
            try:
                double_side_choose = data[
                    "double_side_choose"]  # параметр для отображения, выбрал чел двустронную печать или нет,
                # если не указывается пользователем
                # ставится дефолтное значение
            except:
                double_side_choose = "Нет"
        user_id = callback_query.from_user.id

        await bot.send_message(user_id, f"Ваш заказ:\n\n"
                                                            f"Количество страниц: {0}\n"
                                                            f"Двусторонняя печать: {double_side_choose}\n"
                                                            f"Количество копий: {copycount}\n"
                                                            f"Выбранные страницы: {needpages}\n\n"
                                                            "Цена - x рублей")
        # кнопка для оплаты
        price = 50000  # цена пока просто фо фан стоит, но после подсчета, в нее запихнем полученное значение, дальше оно само все сделает
        PRICE = types.LabeledPrice(label="Оплатить", amount=price)
        await bot.send_invoice(
            callback_query.from_user.id,
            title="Оплатить",
            description="Оплата услуг",
            provider_token=PAYMENTS_PROVIDER_TOKEN,
            currency='rub',
            is_flexible=False,  # True если конечная цена зависит от способа доставки
            prices=[PRICE],
            start_parameter='time-machine-example',
            payload='some-invoice-payload-for-our-internal-use'  # идентификация инвойса
        )
    elif callback_query.data == 'feedback_btn':
        await bot.send_message(callback_query.from_user.id, "Пожалуйста, напишите свой отзыв")
        await feedback.userfeedback.set()
    elif callback_query.data == 'menu_btn':
        await bot.send_message(callback_query.from_user.id, "Переход в основное меню", reply_markup=menu_keyboard())
    elif callback_query.data == "id_input_type":
        await bot.send_message(callback_query.from_user.id, "Загрузите файл", reply_markup=upload_select_keyboard())


@dp.message_handler(state=reques_city.city)
async def city_handler(message: types.Message, state: FSMContext):
    city = message.text
    db = DataBaseEditor()
    citysearch = db.check_city_isinstance(city)
    db.close_connection()
    del db
    if citysearch is None:
        await bot.send_message(message.from_user.id, "Упс\nВ данном городе сервис PrintDocCloud не работает, проверьте "
                                                     "еще раз введенный город или посмотрите на карте наши точки",
                               reply_markup=city_select_keyboard())
        await state.finish()
    else:
        await state.update_data(city=city)
        await reques_city.next()
        async with state.proxy() as data:
            data['city'] = city
        await bot.send_message(message.from_user.id, "Выберите принтер для печати удобным вам способом",
                               reply_markup=point_select_keyboard())


# Обработка города через геолокацию
@dp.message_handler(content_types=["location"], state=locat.reqlocation)
async def city_handler(message: types.Message, state: FSMContext):
    city = geoloc_city_search(message.location.latitude, message.location.longitude)
    db = DataBaseEditor()
    citysearch = db.check_city_isinstance(city)
    db.close_connection()
    del db
    await message.answer(f"Ваш город: {city}")
    if citysearch is None:
        await message.answer("Упс\nВ данном городе сервис PrintDocCloud не работает,"
                             "включите передачу геолокации на телефоне и попробуйте снова")
        await locat.reqlocation.set()
    else:
        await state.update_data(city=city)
        await state.finish()
        async with state.proxy() as data:
            data['city'] = city
        await bot.send_message(message.from_user.id, "Выберите принтер для печати удобным вам способом",
                               reply_markup=point_select_keyboard())


# Выбор точки по адресу
@dp.message_handler(state=locat.street)
async def street_handler(message: types.Message, state: FSMContext):
    street = message.text
    city = str()
    async with state.proxy() as data:
        city = data['city']
    db = DataBaseEditor()
    house_list = db.get_all_houses_of_street(street=street, city=city)
    db.close_connection()
    del db
    if house_list is None:
        await bot.send_message(message.from_user.id, "К сожалению на данной улице отсутствуют доступные принтеры, "
                                                     "пожалуйста, воспользуйтесь функцией поиска принтеров по "
                                                     "местоположению "
                                                     "для поиска ближайших к вам точек, или используйте другой "
                                                     "удобный метод "
                                                     "поиска принтера.", reply_markup=point_select_keyboard())
        await state.finish()
        async with state.proxy() as data:
            data['city'] = city
    else:
        await state.update_data(street=street)
        await locat.next()
        async with state.proxy() as data:
            data['street'] = street
        await message.answer(f"Локации находящиеся по этой улице:", reply_markup=list_buttoncreate_keyboard(house_list))


# Выбор точки по геолокации
@dp.message_handler(content_types=["location"], state=locat.tmp_location)
async def street_handler(message: types.Message, state: FSMContext):
    min_delta = 0.01
    user_locat = [message.location.latitude, message.location.longitude]
    db = DataBaseEditor()
    coordinates_of_printers = db.get_all_coords_of_printers_location()
    nearest_coord = 0
    for row_index in range(len(coordinates_of_printers)):
        delta = nearest_point_searcher(user_locat, coordinates_of_printers[row_index])
        if delta > min_delta:
            min_delta = delta
            nearest_coord = coordinates_of_printers[row_index]
    selected_printer = db.get_printer_info_by_coords(nearest_coord)
    db.close_connection()
    del db
    street = selected_printer['street']
    house = selected_printer['house']
    printer_mark = selected_printer['printer_mark']
    printer_id = selected_printer['printer_id']
    await state.update_data(tmp_location=printer_id)
    await state.finish()
    async with state.proxy() as data:
        data["printer_id"] = printer_id
    await bot.send_message(message.from_user.id, "Ближайшая точка к вашей локации: ",
                           reply_markup=id_select_keyboard(street, house, printer_mark))


@dp.message_handler(state=text_from_user.user_text, content_types=["document", "photo"])
async def user_test_handler(message: types.Message, state: FSMContext):
    usr_text = message.document  # Переменная юзается для того, чтобы хранить путь файла, если не нужен, лучше просто оставь, ибо я не уверен, как оно будет работать
    try:
        if message.document is None:
            downloaded_file, src = await get_image(message)
            mode = IMAGE_DIR
        else:
            document_types = ['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT',
                              'PPTX', 'TXT', 'RTF', 'HTML']
            current_type = message.document.file_name.split('.')[-1].upper()
            if current_type not in document_types:
                raise FileTypeIsNotExists(current_type, document_types)
            downloaded_file, src = await get_document(message)
            mode = DOCUMENT_DIR
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file.getvalue())
        converting_files_in_dirs(mode)
        await state.update_data(user_text=usr_text)
        await state.finish()
        await bot.send_message(message.from_user.id,
                               "Давай настроим параметры на печати, или сразу отправляй документ на печать",
                               reply_markup=printparam_select_keyboard())
    except FileTypeIsNotExists as e:
        await bot.send_message(message.from_user.id, "К сожалению я не могу принять ваш файл."
                                                     "Попробуйте загрузить другой файл, или попробуйте заново."
                                                     "Ошибка обработки файла: \n{}".format(e))
        await text_from_user.user_text.set()


@dp.message_handler(state=print_settings.copycount)
async def user_test_handler(message: types.Message, state: FSMContext):
    copycount = message.text
    await state.update_data(copycount=copycount)
    async with state.proxy() as data:
        double_side = data["double_side"]
        data["copycount"] = copycount
    await bot.send_message(message.from_user.id,
                           "Выбери другие параметры для изменения или 'Готово', если установил все необходимые "
                           "параметры",
                           reply_markup=print_set_keyboard(double_side))


@dp.message_handler(state=print_settings.doubleside)
async def user_test_handler(message: types.Message, state: FSMContext):
    answer = message.text
    await state.update_data(doubleside=answer)
    if answer.lower() == "да":
        double_side_choose = "Да"
    else:
        double_side_choose = "Нет"
    async with state.proxy() as data:
        data["double_side_choose"] = double_side_choose
        double_side = data["double_side"]
    await bot.send_message(message.from_user.id,
                           "Выбери другие параметры для изменения или 'Готово', если установил все необходимые "
                           "параметры",
                           reply_markup=print_set_keyboard(double_side))


@dp.message_handler(state=print_settings.needpages)
async def user_test_handler(message: types.Message, state: FSMContext):
    needpages = [message.text]
    await state.update_data(needpages=needpages)
    async with state.proxy() as data:
        double_side = data["double_side"]
        data["needpages"] = needpages
    await bot.send_message(message.from_user.id,
                           "Выбери другие параметры для изменения или 'Готово', если установил все необходимые "
                           "параметры",
                           reply_markup=print_set_keyboard(double_side))


@dp.message_handler(state=feedback.userfeedback)
async def user_test_handler(message: types.Message, state: FSMContext):
    fdbck = message.text
    feedback_to_send = {
        "user_id": message.from_user.id,
        "user_name": message.from_user.first_name,
        "user_feedback": fdbck
    }
    await state.update_data(feedback=fdbck)
    await state.finish()
    await bot.send_message(299723780, "#Отзыв")
    await bot.forward_message(299723780, message.from_user.id, message.message_id)
    await bot.send_message(message.from_user.id, "Большое спасибо за отзыв!\nПереводим Вас в меню",
                           reply_markup=menu_keyboard())


@dp.message_handler(state=locat.printer_id_location)
async def user_input_printer_id_handler(message: types.Message, state: FSMContext):
    printer_id = message.text
    db = DataBaseEditor()
    printer_id_check = db.check_printer_is_exists(int(printer_id))
    if printer_id_check is None:
        await bot.send_message(message.from_user.id,
                               "Принтера с таким ID нет, выберите другой метод выбора принтера,",
                               reply_markup=point_select_keyboard())
        await state.finish()
        db.close_connection()
        del db
    else:
        printer_info_by_id = db.get_printer_info_by_id(int(printer_id))
        street = printer_info_by_id['street']
        house = printer_info_by_id['house']
        printer_mark = printer_info_by_id['printer_mark']
        db.close_connection()
        del db
        await state.update_data(printer_id_location=printer_id)
        await bot.send_message(message.from_user.id, "Точка по заданному ID",
                               reply_markup=id_select_keyboard(street, house, printer_mark))


@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    print('successful_payment:')
    pay_details = message.successful_payment.to_python()
    for key, val in pay_details.items():
        print(f'{key} = {val}')
    await bot.send_message(message.chat.id, "Оплата прошла успешно\n"
                                            "Спасибо, что воспользовались нашили услугами\n"
                                            "Мы были бы признательны за ваш отзыв или вы можете перейте в главное меню",
                           reply_markup=fdbck_menu_keyboard())


def update_files_list(mode):
    files = os.listdir(mode)
    return [os.path.join(mode, f) for f in files]


def converting_files_in_dirs(mode):
    files = update_files_list(mode)
    files2pdf = Editor(page_format='A4', files_path_list=files)
    files2pdf.converting()
    files = update_files_list(mode)
    [os.unlink(file) for file in files if file.split('.')[-1] != 'pdf']


async def get_document(message):
    file_contact = message.document.file_id
    file_name = message.document.file_name
    root_dir = DOCUMENT_DIR
    file_info = await bot.get_file(file_contact)
    downloaded_file = await bot.download_file(file_info.file_path)
    src = os.path.join(os.path.abspath(root_dir),
                       ''.join([str(message.from_user.id), '_', file_name]))
    return downloaded_file, src


async def get_image(message):
    file_contact = message.photo[len(message.photo) - 2].file_id
    file_name = await bot.get_file(file_contact)
    file_info = file_name
    file_name = file_name.file_path.split('/')[-1]
    root_dir = IMAGE_DIR
    downloaded_file = await bot.download_file(file_info.file_path)
    src = os.path.join(os.path.abspath(root_dir),
                       ''.join([str(message.from_user.id), '_', file_name]))
    return downloaded_file, src


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
