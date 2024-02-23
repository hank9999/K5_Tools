from const_vars import LANGUAGE_LIST

translations = {
    LANGUAGE_LIST[0]: {
        # UI
        'tool_name': 'K5/K6 小工具集 ',
        'now_state_none_text': '当前操作: 无',

        'theme_label_text': '主题',
        'serial_port_text': '串口',
        'firmware_label_text': '固件版本',

        # Buttons
        'clean_eeprom_button_text' : '清空EEPROM',
        'auto_write_font_button_text' : '自动写入字库',
        'read_calibration_button_text' : '读取校准参数',
        'write_calibration_button_text' : '写入校准参数',
        'read_config_button_text' : '读取配置参数',
        'write_config_button_text' :'写入配置参数',
        'write_font_conf_button_text' : '写入字库配置',
        'write_tone_options_button_text' :'写入亚音参数',
        'write_font_compressed_button_text' : '写入压缩字库',
        'write_font_uncompressed_button_text' : '写入全量字库',
        'write_font_old_button_text' : '写入字库 (旧)',
        'write_pinyin_old_index_button_text' : '写入拼音表（旧）',
        'write_pinyin_new_index_button_text' : '写入拼音表（新）',
        'todo_button_text' : '敬请期待',

        # Tooltip
        'eeprom_size_combo_tooltip_text': 'EEPROM芯片容量，若自动检测正确则无需修改',
        'firmware_combo_tooltip_text': '固件版本，若自动检测正确则无需修改',
        'serial_port_combo_tooltip_text': '点击选择K5/K6所在串口',
        'clean_eeprom_button_tooltip_text': '清除EEPROM中的所有数据',
        'auto_write_font_button_tooltip_text': '自动写入机器固件所需字库等文件，如不清楚点那个按钮的情况下，点这个总没错',
        'read_calibration_button_tooltip_text': '校准文件包含硬件参数校准信息，必须备份！建议终身保留以备恢复',
        'write_calibration_button_tooltip_text': '校准文件只在更换芯片或清除EEPROM数据后写一次即可',
        'read_config_button_tooltip_text': '配置文件包含了菜单设置信息、开机字符和信道信息等，如无特别需要可不备份，不同固件的菜单设置可能不通用',
        'write_config_button_tooltip_text': '配置文件如无特别需要，可以不写',
        'write_font_conf_button_tooltip_text': '写入字库配置，如果不使用自动写入，请在执行完字库写入后点击',
        'write_tone_options_button_tooltip_text': '写入亚音参数，如果不使用自动写入，请在执行完字库写入后点击',
        'write_font_compressed_button_tooltip_text': '压缩GB2312字库，萝狮虎118K、123H版本及后续版本使用',
        'write_font_uncompressed_button_tooltip_text': '全量GB2312字库，用于萝狮虎118H版本，后续未使用',
        'write_font_old_button_tooltip_text': '117版本及之前版本使用，旧字库',
        'write_pinyin_old_index_button_tooltip_text': '123版本拼音索引，如果不使用自动写入，请在执行完字库写入后点击',
        'write_pinyin_new_index_button_tooltip_text': '124及以上版本拼音索引，如果不使用自动写入，请在执行完字库写入后点击',
        'language_combo_tooltip_text':'更改语言，重启程序生效'
    },
    LANGUAGE_LIST[1]: {
        'tool_name': 'K5/K6 Tools ',
        'now_state_none_text': 'Now state: none',

        'theme_label_text': 'Theme',
        'serial_port_text': 'Serial',
        'firmware_label_text': 'Firmware',

        'clean_eeprom_button_text': 'Clear EEPROM',
        'auto_write_font_button_text': 'Auto write font',
        'read_calibration_button_text': 'Read calibration',
        'write_calibration_button_text': 'Write calibration',
        'read_config_button_text': 'Read config',
        'write_config_button_text': 'Write config',
        'write_font_conf_button_text': 'Write font config',
        'write_tone_options_button_text': 'Write tone config',
        'write_font_compressed_button_text': 'Write comp font',
        'write_font_uncompressed_button_text': 'Write full font',
        'write_font_old_button_text': 'Write old font',
        'write_pinyin_old_index_button_text': 'Write old index',
        'write_pinyin_new_index_button_text': 'Write new index',
        'todo_button_text': 'Coming soon',

        'eeprom_size_combo_tooltip_text': 'EEPROM chip capacity, no need to modify if automatically detected correctly',
        'firmware_combo_tooltip_text': 'Firmware version, no need to modify if automatically detected correctly',
        'serial_port_combo_tooltip_text': 'Click to select the port where K5/K6 is located',
        'clean_eeprom_button_tooltip_text': 'Clear ALL data in the EEPROM',
        'auto_write_font_button_tooltip_text': 'Automatically write the font library and other files required for machine firmware. If you are unsure about the button next to it, clicking this one is never wrong.',
        'read_calibration_button_tooltip_text': 'The calibration file contains hardware parameter calibration information, must be backed up! It is recommended to keep it for a lifetime for recovery.',
        'write_calibration_button_tooltip_text': 'Write the calibration file only once after replacing the chip or clearing EEPROM data.',
        'read_config_button_tooltip_text': 'The configuration file contains menu settings, boot characters, channel information, etc. It is not necessary to back up if there are no special requirements. Menu settings for different firmware may not be universal.',
        'write_config_button_tooltip_text': 'You can skip writing the configuration file if not needed.',
        'write_font_conf_button_tooltip_text': 'Write font library configuration. If not using automatic writing, click after executing font library writing.',
        'write_tone_options_button_tooltip_text': 'Write t-tone parameters. If not using automatic writing, click after executing font library writing.',
        'write_font_compressed_button_tooltip_text': 'Compressed GB2312 font library, used for losehu 118K, 123H versions, and subsequent versions.',
        'write_font_uncompressed_button_tooltip_text': 'Full GB2312 font library, used for losehu 118H version and later unused versions.',
        'write_font_old_button_tooltip_text': 'Used for losehu 117 version and earlier versions, old font library.',
        'write_pinyin_old_index_button_tooltip_text': '123 version Pinyin index. If not using automatic writing, click after executing font library writing.',
        'write_pinyin_new_index_button_tooltip_text': '124 and later versions Pinyin index. If not using automatic writing, click after executing font library writing.',
        'language_combo_tooltip_text':'Change language, take effect after restart.'
    }
}