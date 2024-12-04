from enum import Enum

FIRMWARE_VERSION_LIST = ['萝狮虎', '萝狮虎扩容', '其他']
EEPROM_SIZE = ['8KiB (原厂)', '128KiB (1Mbit)', '256KiB (2Mbit)', '384KiB (3Mbit)', '512KiB (4Mbit)']


class FontType(Enum):
    GB2312_COMPRESSED = '压缩GB2312'
    GB2312_UNCOMPRESSED = '未压缩GB2312'
    LOSEHU_FONT = '萝狮虎字库'


class LanguageType(Enum):
    SIMPLIFIED_CHINESE = '简体中文'
    ENGLISH = 'English'

    @staticmethod
    def find_value(value: str) -> 'LanguageType':
        for item in LanguageType:
            if item.value == value:
                return item
        return LanguageType.SIMPLIFIED_CHINESE

    @staticmethod
    def find_name(name: str) -> 'LanguageType':
        for item in LanguageType:
            if item.name == name:
                return item
        return LanguageType.SIMPLIFIED_CHINESE

    @staticmethod
    def value_list():
        return list(map(lambda i: i.value, LanguageType))
