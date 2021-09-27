from dadata import Dadata
from data.config import DA_TOKEN


class GeoLocationData:
    def __init__(self, **location):
        self.__city = location['city']
        self.__street = location['street']
        self.__house = location['house']
        self.__settlement_type = location['settlement_type']
        self.__settlement = location['settlement']
        self.__check_location()

    def get_generals_properties(self):
        return self.__general_property, self.__general_street, self.__general_house

    def __check_location(self):
        if self.__city is None:
            first_part_general, second_part_general = '', ''
            if self.__settlement_type is not None:
                first_part_general = self.__settlement_type
            if self.__settlement is not None:
                second_part_general = self.__settlement
            self.__general_property = f'{first_part_general} {second_part_general}'
        else:
            self.__general_property = self.__city
        if self.__street is None:
            self.__general_street = 'Улица не определена'
        else:
            self.__general_street = self.__street
        if self.__house is None:
            self.__general_house = 'Дом не определен'
        else:
            self.__general_house = self.__house


dadata = Dadata(DA_TOKEN)


def geoloc_city_search(lat, lon):
    result = dadata.geolocate(name="address", lat=lat, lon=lon)
    for kek in result:
        tmp = kek.get('data')
        geolocation = GeoLocationData(city=tmp['city'], street=tmp['street'], house=tmp['house'],
                                      settlement_type=tmp['settlement_type'], settlement=tmp['settlement'])
    return geolocation.get_generals_properties()
