import cups
import copy


class Printers:
    __Printers_list = {}

    def __init__(self):
        self.__connection = cups.Connection()
        self.__update_printers_list()

    def __update_printers_list(self):
        self.__Printers_list = copy.deepcopy(self.__connection.getPrinters())

    def get_printers_list(self):
        return self.__Printers_list


class ChoicePrinter(Printers):
    def __init__(self, printer_name, options_for_printer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__printer_name = printer_name
        self.__options = options_for_printer
        self.__selected_printer = self.get_printers_list()[printer_name]

    def get_selected_printer(self):
        return self.__selected_printer

    def print_file(self):
        cups.Connection().printFile(self.__printer_name, '/BackEnd/trash/skannnn_index_26.07.21.pdf', 'lol',
                                    options=self.__options)


if __name__ == "__main__":
    options = {"media": "A4",
               "sides": "two-sided-long-edge",
               'n': '2'}
    # options_for_printer = {}
    obj = ChoicePrinter(printer_name='HP_Deskjet_4510_series_6A3693_', options_for_printer=options)
    obj.print_file()
