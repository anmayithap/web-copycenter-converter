import datetime

import PyPDF2
from PIL import Image
from settings import ROOT_DIR
from utils.db_api.db_editor import DataBaseEditor

import img2pdf
import sys
import subprocess
import re
import os
import pdfkit
import shutil

# sudo apt-get install wkhtmltopdf !!!!!

html_template = '<!DOCTYPE html>' \
                '<html lang="ru"' \
                '<head>' \
                '<meta charset="UTF-8">' \
                '</head>' \
                '<body></body>' \
                '</html>'


def count_pages(file):
    with open(file, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        return pdf_reader.getNumPages()


class PageSizeException(BaseException):
    pass


class NotAvailableFileTypeError(PageSizeException):
    def __init__(self, current_type, available_types):
        self.current_type = current_type
        self.available_types = available_types

    def __str__(self):
        return f'!!! Not available type of file {self.current_type} !!!\n' \
               '!!! Available types: !!!\n' \
               f'!!! Images: {self.available_types["images"]} !!!\n' \
               f'!!! Documents: {self.available_types["documents"]} !!!\n' \
               '!!! Please upload the correct file !!!'


class PageSize:
    __formats_list_size = {
        'A4': ('8.3', '11.7'), 'A3': ('11.7', '16.8'), 'A2': ('16.8', '23.7')
    }

    __supported_formats = {
        'images': ['png', 'bmp', 'jpg', 'gif', 'jpeg', 'eps'],
        'documents': ['txt', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'html', 'rtf', 'pdf']
    }

    def __init__(self, exception, format_file='A4', input_path='./'):
        self.__input_path = os.path.abspath(input_path)
        if not (self.__check_for_availability(mode='images') or self.__check_for_availability(mode='documents')):
            raise NotAvailableFileTypeError(self.get_file_path().split('/')[-1], self.get_supported_formats())
        self.__mode = 'images' if exception in self.__supported_formats['images'] else 'documents'
        self.__page_format = format_file
        self.__page_size = self.__formats_list_size[format_file]
        self.__file_type = self.__set_file_type()
        self.__file_name = self.__find_file_name()
        self.__out_put_path = os.path.join(ROOT_DIR, f'{format_file}', self.get_date_suffix(),
                                           self.get_time_suffix(), self.get_file_type())

    def set_page_size(self, new_size):
        self.__page_size = new_size

    def get_file_path(self):
        return self.__input_path

    def get_page_format(self):
        return self.__page_format

    def get_supported_formats(self):
        return self.__supported_formats

    def get_page_size(self):
        return self.__page_size

    def __set_file_type(self):
        for supported_type in self.__supported_formats[self.__mode]:
            if self.get_file_path().rfind('.' + supported_type) != -1:
                return supported_type

    def get_file_name(self):
        return self.__file_name

    def get_file_type(self):
        return self.__file_type

    def get_output_path(self):
        return self.__out_put_path

    @classmethod
    def get_date_suffix(cls):
        return datetime.datetime.now().strftime('%d.%m.%y')

    @classmethod
    def get_time_suffix(cls):
        return datetime.datetime.now().strftime('%H:%M:00')

    def __check_for_availability(self, mode='documents'):
        for file_type in self.get_supported_formats()[mode]:
            if self.__input_path.find('.' + file_type):
                return True
        return False

    def __find_file_name(self):
        return self.get_file_path().split('/')[-1].replace('.' + self.__file_type, '')

    def get_output_name(self):
        return ''.join([self.get_file_name(), '_', self.get_date_suffix()])

    def insert_to_data_base(self, pages_count, out_put_path):
        user_id = self.get_file_name().split('_')[0]
        file_path = out_put_path
        user_data_base_row = DataBaseEditor()
        current_request_id = int(user_data_base_row.select_requests(user_id)[0][0])
        file_type = self.get_file_type()
        request_time = datetime.datetime.now().time().strftime("%H:%M:%S")
        request_date = datetime.datetime.now().date().strftime("%Y-%m-%d")
        values = (current_request_id, pages_count, file_path, file_type, 0, request_time, request_date,
                  '', 0, 0)
        user_data_base_row.insert_user_file(values)


class ImageConverter(PageSize):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.float_page_size = [
            img2pdf.in_to_pt(float(self.get_page_size()[0])),
            img2pdf.in_to_pt(float(self.get_page_size()[1]))
        ]
        self.__layout_function = img2pdf.get_layout_fun(self.float_page_size)
        self.image_file = Image.open(self.get_file_path())

    def __get_page_size(self):
        page_size = tuple(map(float, self.get_page_size()))
        self.set_page_size((int(page_size[0] * 200), int(page_size[1] * 200)))
        return self.get_page_size()

    def __calculate_new_image_size(self):
        target_width, target_height = self.__get_page_size()
        current_width, current_height = self.image_file.size
        scale = max((current_width / float(target_width)), (current_height / float(target_height)))
        final_image_size = [round(current_width / scale), round(current_height / scale)]
        resized_image = self.image_file.resize(size=final_image_size, resample=Image.LANCZOS)
        canvas_image = Image.new(mode='RGB', size=self.get_page_size(), color='white')
        canvas_image.paste(resized_image)
        return canvas_image

    def convert_to_pdf(self):
        canvas_image = self.__calculate_new_image_size()
        try:
            from pathlib import Path
            Path(self.get_output_path()).mkdir(parents=True,
                                               exist_ok=True)
        except FileExistsError:
            print('Directory already exists')
        canvas_image.save(
            os.path.join(self.get_output_path(), self.get_output_name() + '.pdf'), format='PDF', quality=200)
        pages_count = count_pages(os.path.join(self.get_output_path(), self.get_output_name() + '.pdf'))
        self.insert_to_data_base(pages_count, os.path.join(self.get_output_path(), self.get_output_name() + '.pdf'))


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output


class OfficeConverter(PageSize):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def __libreoffice_exec(cls):
        if sys.platform == 'darwin':
            return '/Applications/LibreOffice.app/Contents/MacOS/soffice'
        return 'libreoffice'

    def convert_to_pdf(self, timeout=None):
        output_path = os.path.join(self.get_output_path(), self.get_file_name())
        args = [self.__libreoffice_exec(), '--headless', '--convert-to', 'pdf', '--outdir', output_path,
                self.get_file_path()]
        process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        filename = re.search('-> (.*?) using filter', process.stdout.decode())
        if filename is None:
            raise LibreOfficeError(process.stdout.decode())
        else:
            result = filename.group(1)
            pages_count = count_pages(result)
            self.insert_to_data_base(pages_count, result)
            return result


def exception_files2pdf(file_path, file_format, exception):
    file = PageSize(exception=exception, format_file=file_format, input_path=file_path)
    # file.insert_to_data_base()
    try:
        from pathlib import Path
        Path(
            file.get_output_path()).mkdir(
            parents=True, exist_ok=True)
    except FileExistsError:
        print('Directory already exists')
    output_path = os.path.join(file.get_output_path(), file.get_output_name() + '.pdf')
    return file_path, output_path, file


def txt2pdf(input_path, file_format, exception, arg='-o'):
    file_path, output_path, page_size_object = exception_files2pdf(input_path, file_format, exception=exception)
    new_txt_format = ''
    with open(file_path, 'r') as txt_file:
        lines = txt_file.readlines()
        new_lines = []
        for line in lines:
            new_lines.append(line.replace('\n', '<br>'))
        new_text_template = ''.join(new_lines)
        new_txt_format = html_template.replace('<body></body>', f'<body><p>{new_text_template}</p></body>')
    html_file_path = file_path.replace('.txt', '.html')
    try:
        os.remove(file_path)
    except OSError as e:
        print("ERROR: %s - %s." % (e.filename, e.strerror))
    with open(html_file_path, 'w') as txt2html_file:
        txt2html_file.write(new_txt_format)
    result = pdfkit.from_file(html_file_path, output_path)
    pages_count = count_pages(output_path)
    page_size_object.insert_to_data_base(pages_count, output_path)
    return result


def save_pdf(input_file):
    file_path, output_path, page_size_object = exception_files2pdf(input_file, exception='pdf', file_format='A4')
    shutil.move(file_path, output_path)
    pages_count = count_pages(output_path)
    page_size_object.insert_to_data_base(pages_count, output_path)


def html2pdf(input_path, file_format, exception):
    file_path, output_path, page_size_object = exception_files2pdf(input_path, file_format, exception=exception)
    result = pdfkit.from_file(file_path, output_path)
    pages_count = count_pages(output_path)
    page_size_object.insert_to_data_base(pages_count, output_path)
    return result
