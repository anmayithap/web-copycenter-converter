from .converter import ImageConverter, OfficeConverter, html2pdf, txt2pdf, save_pdf


class EditorError(BaseException):
    pass


class FileTypeIsNotExists(EditorError):
    def __init__(self, file_type, file_types_list):
        self.file_type = file_type
        self.file_types_list = file_types_list

    def __str__(self):
        return f"!!! Данный тип файла {self.file_type} не входит в список допустимых {self.file_types_list} !!!"


class Editor:
    __distributor = {
        'png': ImageConverter,
        'jpg': ImageConverter,
        'jpeg': ImageConverter,
        'doc': OfficeConverter,
        'docx': OfficeConverter,
        'xls': OfficeConverter,
        'xlsx': OfficeConverter,
        'ppt': OfficeConverter,
        'pptx': OfficeConverter,
        'bmp': ImageConverter,
        'eps': ImageConverter,
        'gif': ImageConverter,
        'txt': False,
        'rtf': OfficeConverter,
        'html': False,
        'pdf': False
    }

    def __init__(self, page_format, files_path_list):
        self.__files_path_list = files_path_list
        self.__page_format = page_format

    def __distributing(self, file_path, extension):
        if extension not in ['html', 'txt', 'pdf']:
            self.__distributor[extension](extension, self.__page_format, file_path).convert_to_pdf()
        elif extension == 'txt':
            txt2pdf(file_path, self.__page_format, exception=extension)
        elif extension == 'html':
            html2pdf(file_path, self.__page_format, exception=extension)
        elif extension == 'pdf':
            save_pdf(file_path)
        else:
            raise FileTypeIsNotExists(extension, self.__distributor.keys())

    def converting(self):
        for file_path in self.__files_path_list:
            if file_path.split('/')[-1].split('.')[-1] in self.__distributor:
                self.__distributing(file_path, extension=file_path.split('/')[-1].split('.')[-1])
