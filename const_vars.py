from enum import Enum

FIRMWARE_VERSION_LIST = ['萝狮虎', '萝狮虎扩容', '其他']
EEPROM_SIZE = ['8KiB (原厂)', '128KiB (1M)', '256KiB (2M)', '384KiB (3M)', '512KiB (4M)']
LANGUAGE_LIST = ['zh-CN', 'en-US']

class FontType(Enum):
    GB2312_COMPRESSED = '压缩GB2312'
    GB2312_UNCOMPRESSED = '未压缩GB2312'
    LOSEHU_FONT = '萝狮虎字库'
