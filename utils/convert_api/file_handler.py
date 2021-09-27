import os
from settings import DOCUMENT_DIR, IMAGE_DIR
from loader import dp
from .editor import Editor
from utils.db_api.db_editor import DataBaseEditor


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
    file_info = await dp.bot.get_file(file_contact)
    downloaded_file = await dp.bot.download_file(file_info.file_path)
    src = os.path.join(os.path.abspath(root_dir),
                       ''.join([str(message.from_user.id), '_', file_name]))
    return downloaded_file, src


async def get_image(message):
    file_contact = message.photo[len(message.photo) - 2].file_id
    file_name = await dp.bot.get_file(file_contact)
    file_info = file_name
    file_name = file_name.file_path.split('/')[-1]
    root_dir = IMAGE_DIR
    downloaded_file = await dp.bot.download_file(file_info.file_path)
    src = os.path.join(os.path.abspath(root_dir),
                       ''.join([str(message.from_user.id), '_', file_name]))
    return downloaded_file, src


async def clear_data_base(user_id):
    data_base = DataBaseEditor()
    data_base.delete_user_rows(user_id)
    data_base.close_connection()
    del data_base
