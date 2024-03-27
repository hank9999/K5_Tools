import os
import sys
import customtkinter as ctk
from tkinter import messagebox

import configparser
from const_vars import FIRMWARE_VERSION_LIST, EEPROM_SIZE, FontType, LanguageType
from logger import log
from translations import translations

from functions import (
    serial_port_combo_postcommand, 
    serial_port_combo_callback, 
    clean_eeprom, write_font, 
    write_font_conf, 
    write_tone_options, 
    auto_write_font, 
    read_calibration, 
    write_calibration, 
    read_config, 
    write_config, 
    write_pinyin_index,
    todo_function,
    backup_eeprom,
    restore_eeprom
)

window = ctk.CTk()
version = '0.6'

appdata_path = os.getenv('APPDATA') if os.getenv('APPDATA') is not None else ''
config_dir = os.path.join(appdata_path, 'K5_Tools')
config_path = os.path.join(config_dir, 'config.ini')

config = configparser.ConfigParser()
config.read(config_path)

# 检查配置文件并添加缺失的部分
if 'ConfigVersion' not in config:
    config['ConfigVersion'] = {}
if 'configversion' not in config['ConfigVersion']:
    config['ConfigVersion']['configversion'] = '0.2'
if 'Settings' not in config:
    config['Settings'] = {}
if 'theme' not in config['Settings']:
    config['Settings']['theme'] = 'darkly'
if 'language' not in config['Settings']:
    config['Settings']['language'] = LanguageType.SIMPLIFIED_CHINESE.name

config_version = config.get('ConfigVersion', 'configversion')
# style = ttk.Style(config.get('Settings', 'theme'))
language = LanguageType.find_name(config.get('Settings', 'language'))


class Tooltip(object):
    def __init__(self, widget, text='widget info'):
        self.wait_time = 500  # milliseconds
        self.wrap_length = 280  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
        self.widget.bind('<ButtonPress>', self.leave)
        self.widget.bind('<ButtonRelease>', self.enter)
        self.tid = None
        self.tw = None

    def enter(self, _):
        self.schedule()

    def leave(self, _):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.tid = self.widget.after(self.wait_time, self.showtip)

    def unschedule(self):
        tid = self.tid
        self.tid = None
        if tid:
            self.widget.after_cancel(tid)

    def showtip(self):
        x, y, cx, cy = self.widget.bbox('insert')
        x += self.widget.winfo_rootx() + 30
        y += self.widget.winfo_rooty() + 30
        self.tw = ctk.CTkToplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry('+%d+%d' % (x, y))
        label = ctk.CTkLabel(
            self.tw,
            text=self.text,
            justify='left',
            wraplength=self.wrap_length,
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class TextRedirector:
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, strs):
        self.widget.insert(ctk.END, strs)
        self.widget.see(ctk.END)

    def flush(self):
        pass


def make_readonly(_):
    return 'break'


def on_closing():
    config['Settings']['language'] = language.name
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    window.destroy()


def change_theme(_, theme_combo: ctk.CTkComboBox):
    t = theme_combo.get()
    # style.theme_use(t)
    theme_combo.selection_clear()


def change_language(_, language_combo: ctk.CTkComboBox):
    global language
    language = LanguageType.find_value(language_combo.get())
    if language == LanguageType.SIMPLIFIED_CHINESE:
        log('语言设置已更改为"简体中文"\n请在当前操作完成后手动重启此程序以应用更改')
        messagebox.showinfo(
            '提示',
            '语言设置已更改为"简体中文"\n请在当前操作完成后手动重启此程序以应用更改'
        )
    else:
        log('Language setting has been changed to "English"\nPlease manually restart this program after the current operation is completed to apply the changes')
        messagebox.showinfo(
            'Prompt',
            'Language setting has been changed to "English"\nPlease manually restart this program after the current operation is completed to apply the changes'
        )


def main():
    window.title(f"{translations[language]['tool_name']} v{version}")
    # window.geometry('428x370')
    window.resizable(False, False)
    window.protocol('WM_DELETE_WINDOW', on_closing)

    # 第一行
    frame1 = ctk.CTkFrame(window)
    frame1.grid(row=0, column=0, sticky='we', padx=10, pady=2)

    label1 = ctk.CTkLabel(frame1, text=f"{translations[language]['tool_name']} v{version} (BG4IST - hank9999)")
    label1.pack(side='left')

    theme_combo = ctk.CTkComboBox(frame1, width=100, state='readonly', values=[''])
    theme_combo.pack(side='right', padx=(1, 3), pady=2)
    theme_combo.bind(
        '<<ComboboxSelected>>',
        lambda event: change_theme(
            event, theme_combo
        )
    )

    theme_label = ctk.CTkLabel(frame1, text=translations[language]['theme_label_text'])
    theme_label.pack(side='right')

    # 第二行
    frame2 = ctk.CTkFrame(window)
    frame2.grid(row=1, column=0, sticky='we', padx=10, pady=2)

    label2 = ctk.CTkLabel(frame2, text=translations[language]['now_state_none_text'])
    label2.pack(side='left')

    language_combo = ctk.CTkComboBox(frame2, width=100, state='readonly', values=LanguageType.value_list())
    language_combo.set(language.value)
    language_combo.pack(side='right', padx=(1, 3), pady=2)
    language_combo.bind(
        '<<ComboboxSelected>>',
        lambda event: change_language(
            event, language_combo
        )
    )

    language_label = ctk.CTkLabel(frame2, text='Language')
    language_label.pack(side='right')

    # 第三行
    frame3 = ctk.CTkFrame(window)
    frame3.grid(row=2, column=0, sticky='we', padx=10, pady=2)

    serial_port_label = ctk.CTkLabel(frame3, text=translations[language]['serial_port_text'])
    serial_port_label.pack(side='left')

    serial_port_combo = ctk.CTkComboBox(frame3, width=100, state='readonly')
    serial_port_combo_postcommand(serial_port_combo)
    serial_port_combo.configure(
        command=lambda event: serial_port_combo_callback(
            event, serial_port_combo.get(), label2, eeprom_size_combo, firmware_combo
        )
    )
    serial_port_combo.pack(side='left', padx=(1, 3), pady=2)

    eeprom_size_label = ctk.CTkLabel(frame3, text='EEPROM')
    eeprom_size_label.pack(side='left')

    eeprom_size_combo = ctk.CTkComboBox(frame3, values=EEPROM_SIZE, width=100, state='readonly')
    eeprom_size_combo.pack(side='left', padx=(1, 3))

    firmware_label = ctk.CTkLabel(frame3, text=translations[language]['firmware_label_text'])
    firmware_label.pack(side='left')

    firmware_combo = ctk.CTkComboBox(frame3, values=FIRMWARE_VERSION_LIST, width=100, state='readonly')
    firmware_combo.pack(side='left', padx=(1, 3))

    # 第四行
    frame4 = ctk.CTkFrame(window)
    frame4.grid(row=3, column=0, sticky='we', padx=10, pady=(15, 2))

    clean_eeprom_button = ctk.CTkButton(
        frame4,
        text=translations[language]['clean_eeprom_button_text'],
        width=14,
        command=lambda: clean_eeprom(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    clean_eeprom_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    auto_write_font_button = ctk.CTkButton(
        frame4,
        text=translations[language]['auto_write_font_button_text'],
        width=14,
        command=lambda: auto_write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    auto_write_font_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    read_calibration_button = ctk.CTkButton(
        frame4,
        text=translations[language]['read_calibration_button_text'],
        width=14,
        command=lambda: read_calibration(
            serial_port_combo.get(), window, progress, label2
        )
    )
    read_calibration_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_calibration_button = ctk.CTkButton(
        frame4,
        text=translations[language]['write_calibration_button_text'],
        width=14,
        command=lambda: write_calibration(
            serial_port_combo.get(), window, progress, label2
        )
    )
    write_calibration_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    # 第五行
    frame5 = ctk.CTkFrame(window)
    frame5.grid(row=4, column=0, sticky='we', padx=10, pady=2)

    read_config_button = ctk.CTkButton(
        frame5,
        text=translations[language]['read_config_button_text'],
        width=14,
        command=lambda: read_config(
            serial_port_combo.get(), window, progress, label2
        )
    )
    read_config_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_config_button = ctk.CTkButton(
        frame5,
        text=translations[language]['write_config_button_text'],
        width=14,
        command=lambda: write_config(
            serial_port_combo.get(), window, progress, label2
        )
    )
    write_config_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_font_conf_button = ctk.CTkButton(
        frame5,
        text=translations[language]['write_font_conf_button_text'],
        width=14,
        command=lambda: write_font_conf(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_font_conf_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_tone_options_button = ctk.CTkButton(
        frame5,
        text=translations[language]['write_tone_options_button_text'],
        width=14,
        command=lambda: write_tone_options(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_tone_options_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    # 第六行
    frame6 = ctk.CTkFrame(window)
    frame6.grid(row=5, column=0, sticky='we', padx=10, pady=2)

    write_font_compressed_button = ctk.CTkButton(
        frame6,
        text=translations[language]['write_font_compressed_button_text'],
        width=14,
        command=lambda: write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()),
            FontType.GB2312_COMPRESSED
        )
    )
    write_font_compressed_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_font_uncompressed_button = ctk.CTkButton(
        frame6,
        text=translations[language]['write_font_uncompressed_button_text'],
        width=14,
        command=lambda: write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()),
            FontType.GB2312_UNCOMPRESSED
        )
    )
    write_font_uncompressed_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_font_old_button = ctk.CTkButton(
        frame6,
        text=translations[language]['write_font_old_button_text'],
        width=14,
        command=lambda: write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()),
            FontType.LOSEHU_FONT
        )
    )
    write_font_old_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    write_pinyin_old_index_button = ctk.CTkButton(
        frame6,
        text=translations[language]['write_pinyin_old_index_button_text'],
        width=14,
        command=lambda: write_pinyin_index(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_pinyin_old_index_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    # 第七行
    frame7 = ctk.CTkFrame(window)
    frame7.grid(row=6, column=0, sticky='we', padx=10, pady=(2, 15))
    write_pinyin_new_index_button = ctk.CTkButton(
        frame7,
        text=translations[language]['write_pinyin_new_index_button_text'],
        width=14,
        command=lambda: write_pinyin_index(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()), False, True
        )
    )
    write_pinyin_new_index_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    backup_eeprom_button = ctk.CTkButton(
        frame7,
        text=translations[language]['backup_eeprom_button_text'],
        width=14,
        command=lambda:backup_eeprom(
            serial_port_combo.get(), window, progress, label2,EEPROM_SIZE.index(eeprom_size_combo.get())   
        )
    )
    backup_eeprom_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')
    
    restore_eeprom_button = ctk.CTkButton(
        frame7,
        text=translations[language]['restore_eeprom_button_text'],
        width=14,
        command=lambda:restore_eeprom(
            serial_port_combo.get(), window, progress, label2,EEPROM_SIZE.index(eeprom_size_combo.get())
        )
    )
    restore_eeprom_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')
    
    todo_button = ctk.CTkButton(
        frame7,
        text=translations[language]['todo_button_text'],
        width=14,
        command=todo_function
    )
    todo_button.pack(side='left', padx=3, pady=2, expand=True, fill='x')
    
    # 第八行
    frame8 = ctk.CTkFrame(window)
    frame8.grid(row=7, column=0, sticky='we', padx=10, pady=2)

    textbox = ctk.CTkTextbox(frame8, height=240)
    textbox.bind("<Key>", make_readonly)  # 防止用户修改
    textbox.pack(side='left', padx=3, pady=2, expand=True, fill='x')
    sys.stdout = TextRedirector(textbox)

    # 第九行
    frame9 = ctk.CTkFrame(window)
    frame9.grid(row=8, column=0, sticky='we', padx=10, pady=10)

    progress = ctk.CTkProgressBar(frame9, mode='determinate')
    progress.set(0)
    progress.pack(side='left', padx=3, pady=2, expand=True, fill='x')

    # 布局结束，显示首行日志
    log(f'K5/K6 小工具集 v{version} BG4IST - hank9999\n')
    log('所有操作均有一定的风险，请确保您已备份校准等文件！！！\n')

    # 在此统一设置tooltip
    Tooltip(language_combo, translations[language]['language_combo_tooltip_text'])
    Tooltip(eeprom_size_combo, translations[language]['eeprom_size_combo_tooltip_text'])
    Tooltip(firmware_combo, translations[language]['firmware_combo_tooltip_text'])
    Tooltip(serial_port_combo, translations[language]['serial_port_combo_tooltip_text'])
    Tooltip(clean_eeprom_button, translations[language]['clean_eeprom_button_tooltip_text'])
    Tooltip(auto_write_font_button, translations[language]['auto_write_font_button_tooltip_text'])
    Tooltip(read_calibration_button, translations[language]['read_calibration_button_tooltip_text'])
    Tooltip(write_calibration_button, translations[language]['write_calibration_button_tooltip_text'])
    Tooltip(read_config_button, translations[language]['read_config_button_tooltip_text'])
    Tooltip(write_config_button, translations[language]['write_config_button_tooltip_text'])
    Tooltip(write_font_conf_button, translations[language]['write_font_conf_button_tooltip_text'])
    Tooltip(write_tone_options_button, translations[language]['write_tone_options_button_tooltip_text'])
    Tooltip(write_font_compressed_button, translations[language]['write_font_compressed_button_tooltip_text'])
    Tooltip(write_font_uncompressed_button, translations[language]['write_font_uncompressed_button_tooltip_text'])
    Tooltip(write_font_old_button, translations[language]['write_font_old_button_tooltip_text'])
    Tooltip(write_pinyin_old_index_button, translations[language]['write_pinyin_old_index_button_tooltip_text'])
    Tooltip(write_pinyin_new_index_button, translations[language]['write_pinyin_new_index_button_tooltip_text'])
    Tooltip(backup_eeprom_button, translations[language]['backup_eeprom_button_tooltip_text'])
    Tooltip(restore_eeprom_button, translations[language]['restore_eeprom_button_tooltip_text'])
    Tooltip(todo_button, translations[language]['todo_button_tooltip_text'])

    window.mainloop()


if __name__ == '__main__':
    main()
