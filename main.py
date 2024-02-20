import os
import sys
import tkinter as tk
import ttkbootstrap as ttk
import configparser
from const_vars import FIRMWARE_VERSION_LIST, EEPROM_SIZE, FontType
from logger import log

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
    todo_function
)

window = ttk.Window()
version = '0.4'

appdata_path = os.getenv('APPDATA') if os.getenv('APPDATA') is not None else ''
config_dir = os.path.join(appdata_path, 'K5_Tools')
config_path = os.path.join(config_dir, 'config.ini')

config = configparser.ConfigParser()
if not config.read(config_path):
    config['Settings'] = {'theme': ''}

style = ttk.Style(config.get('Settings', 'theme'))


class Tooltip(object):
    def __init__(self, widget, text='widget info'):
        self.wait_time = 500  # milliseconds
        self.wrap_length = 180  # pixels
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
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry('+%d+%d' % (x, y))
        label = tk.Label(
            self.tw,
            text=self.text,
            justify='left',
            background='#ffffff',
            relief='solid',
            borderwidth=1,
            wraplength=self.wrap_length,
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class TextRedirector(tk.Text):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, strs):
        self.widget.insert(tk.END, strs)
        self.widget.see(tk.END)

    def flush(self):
        pass


def make_readonly(_):
    return 'break'


def on_closing():
    config['Settings'] = {'theme': style.theme.name}
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    window.destroy()


def change_theme(_, theme_combo: ttk.Combobox):
    t = theme_combo.get()
    style.theme_use(t)
    theme_combo.selection_clear()


def main():
    window.title(f'K5/K6 小工具集 v{version}')
    # window.geometry('428x370')
    window.resizable(False, False)
    window.protocol('WM_DELETE_WINDOW', on_closing)

    # 第一行
    frame1 = tk.Frame(window, padx=4, pady=2)
    frame1.grid(row=0, column=0, sticky='we')
    label1 = tk.Label(frame1, text=f'K5/K6 小工具集 v{version} (BG4IST - hank9999)')
    label1.pack(side='left')

    theme_combo = ttk.Combobox(
        frame1,
        width=10,
        state='readonly',
        values=style.theme_names(),
    )
    theme_combo.current(style.theme_names().index(style.theme.name))
    theme_combo.pack(side='right', padx=(1, 3), pady=(5, 2))

    theme_combo.bind('<<ComboboxSelected>>', lambda event: change_theme(event, theme_combo))
    theme_label = tk.Label(frame1, text='主题')
    theme_label.pack(side='right')

    # 第二行
    frame2 = tk.Frame(window, padx=4, pady=2)
    frame2.grid(row=1, column=0, sticky='we')
    label2 = tk.Label(frame2, text='当前操作: 无')
    label2.pack(side='left')

    # 第三行
    frame3 = tk.Frame(window, padx=4, pady=2)
    frame3.grid(row=2, column=0, sticky='we')
    serial_port_label = tk.Label(frame3, text='串口')
    serial_port_label.pack(side='left')
    serial_port_combo = ttk.Combobox(frame3, values=[], width=10, state='readonly')
    serial_port_combo.pack(side='left', padx=1, pady=2)
    serial_port_combo['postcommand'] = lambda: serial_port_combo_postcommand(
        serial_port_combo
    )
    serial_port_combo.bind(
        '<<ComboboxSelected>>',
        lambda event: serial_port_combo_callback(
            event, serial_port_combo.get(), label2, eeprom_size_combo, firmware_combo
        ),
    )
    eeprom_size_label = tk.Label(frame3, text='EEPROM')
    eeprom_size_label.pack(side='left')
    eeprom_size_combo = ttk.Combobox(
        frame3, values=EEPROM_SIZE, width=10, state='readonly'
    )
    eeprom_size_combo.pack(side='left', padx=1, pady=2)
    firmware_label = tk.Label(frame3, text='固件版本')
    firmware_label.pack(side='left')
    firmware_combo = ttk.Combobox(
        frame3, values=FIRMWARE_VERSION_LIST, width=10, state='readonly'
    )
    firmware_combo.pack(side='left', padx=1, pady=2)

    # 第四行
    frame4 = tk.Frame(window, padx=10, pady=2)
    frame4.grid(row=3, column=0, sticky='w')

    clean_eeprom_button = tk.Button(
        frame4,
        text='清空EEPROM',
        width=14,
        command=lambda: clean_eeprom(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    clean_eeprom_button.pack(side='left', padx=3, pady=(15, 2))

    auto_write_font_button = tk.Button(
        frame4,
        text='自动写入字库',
        width=14,
        command=lambda: auto_write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    auto_write_font_button.pack(side='left', padx=3, pady=(15, 2))

    read_calibration_button = tk.Button(
        frame4,
        text='读取校准参数',
        width=14,
        command=lambda: read_calibration(
            serial_port_combo.get(), window, progress, label2
        )
    )
    read_calibration_button.pack(side='left', padx=3, pady=(15, 2))

    write_calibration_button = tk.Button(
        frame4,
        text='写入校准参数',
        width=14,
        command=lambda: write_calibration(
            serial_port_combo.get(), window, progress, label2
        )
    )
    write_calibration_button.pack(side='left', padx=3, pady=(15, 2))
    # 第五行
    frame5 = tk.Frame(window, padx=10, pady=2)
    frame5.grid(row=4, column=0, sticky='w')

    read_config_button = tk.Button(
        frame5,
        text='读取配置参数',
        width=14,
        command=lambda: read_config(
            serial_port_combo.get(), window, progress, label2
        )
    )
    read_config_button.pack(side='left', padx=3, pady=2)

    write_config_button = tk.Button(
        frame5,
        text='写入配置参数',
        width=14,
        command=lambda: write_config(
            serial_port_combo.get(), window, progress, label2
        )
    )
    write_config_button.pack(side='left', padx=3, pady=2)

    write_font_conf_button = tk.Button(
        frame5,
        text='写入字库配置',
        width=14,
        command=lambda: write_font_conf(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_font_conf_button.pack(side='left', padx=3, pady=2)

    write_tone_options_button = tk.Button(
        frame5,
        text='写入亚音参数',
        width=14,
        command=lambda: write_tone_options(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_tone_options_button.pack(side='left', padx=3, pady=2)

    # 第六行
    frame6 = tk.Frame(window, padx=10, pady=2)
    frame6.grid(row=5, column=0, sticky='w')

    write_font_compressed_button = tk.Button(
        frame6,
        text='写入压缩字库',
        width=14,
        command=lambda: write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()),
            FontType.GB2312_COMPRESSED
        )
    )
    write_font_compressed_button.pack(side='left', padx=3, pady=2)

    write_font_uncompressed_button = tk.Button(
        frame6,
        text='写入全量字库',
        width=14,
        command=lambda: write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()),
            FontType.GB2312_UNCOMPRESSED
        )
    )
    write_font_uncompressed_button.pack(side='left', padx=3, pady=2)

    write_font_old_button = tk.Button(
        frame6,
        text='写入字库 (旧)',
        width=14,
        command=lambda: write_font(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()),
            FontType.LOSEHU_FONT
        )
    )
    write_font_old_button.pack(side='left', padx=3, pady=2)

    write_pinyin_old_index_button = tk.Button(
        frame6,
        text='写入拼音表（旧）',
        width=14,
        command=lambda: write_pinyin_index(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_pinyin_old_index_button.pack(side='left', padx=3, pady=2)

    # 第七行
    frame7 = tk.Frame(window, padx=10, pady=2)
    frame7.grid(row=6, column=0, sticky='w')
    write_pinyin_new_index_button = tk.Button(
        frame7,
        text='写入拼音表（新）',
        width=14,
        command=lambda: write_pinyin_index(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get()), True
        )
    )
    write_pinyin_new_index_button.pack(side='left', padx=3, pady=(2, 15))

    todo_button = tk.Button(
        frame7,
        text='敬请期待',
        width=14,
        command=todo_function
    )
    todo_button.pack(side='left', padx=3, pady=(2, 15))
    
    todo_button = tk.Button(
        frame7,
        text='敬请期待',
        width=14,
        command=todo_function
    )
    todo_button.pack(side='left', padx=3, pady=(2, 15))
    
    todo_button = tk.Button(
        frame7,
        text='敬请期待',
        width=14,
        command=todo_function
    )
    todo_button.pack(side='left', padx=3, pady=(2, 15))
    # 第八行
    frame8 = tk.Frame(window, padx=10, pady=2)
    frame8.grid(row=7, column=0, sticky='w')
    textbox = tk.Text(frame8, width=60, height=15)
    textbox.bind("<Key>", make_readonly)  # 防止用户修改
    textbox.pack(side='left', padx=2, pady=2)
    sys.stdout = TextRedirector(textbox)

    # 第九行
    frame9 = tk.Frame(window, padx=10, pady=2)
    frame9.grid(row=8, column=0, sticky='w')
    progress = ttk.Progressbar(frame9, orient='horizontal', length=434, mode='determinate')
    progress.pack(side='left', padx=2, pady=(2, 10))

    # 布局结束，显示首行日志
    log(f'K5/K6 小工具集 v{version} BG4IST - hank9999\n')
    log('所有操作均有一定的风险，请确保您已备份校准等文件！！！\n')

    # 在此统一设置tooltip
    Tooltip(serial_port_combo, "点击选择K5/K6所在串口")
    Tooltip(eeprom_size_combo, "EEPROM芯片容量，若自动检测正确则无需修改")
    Tooltip(firmware_combo, "固件版本，若自动检测正确则无需修改")
    Tooltip(clean_eeprom_button, "清除EEPROM中的所有数据")
    Tooltip(auto_write_font_button, "自动写入机器固件所需字库等文件，如不清楚点那个按钮的情况下，点这个总没错")
    Tooltip(read_calibration_button, "校准文件包含硬件参数校准信息，必须备份！建议终身保留以备恢复")
    Tooltip(write_calibration_button, "校准文件只在更换芯片或清除EEPROM数据后写一次即可")
    Tooltip(read_config_button, "配置文件包含了菜单设置信息、开机字符和信道信息等，如无特别需要可不备份，不同固件的菜单设置可能不通用")
    Tooltip(write_config_button, "配置文件如无特别需要，可以不写")
    Tooltip(write_font_conf_button, "写入字库配置，如果不使用自动写入，请在执行完字库写入后点击")
    Tooltip(write_tone_options_button, "写入亚音参数，如果不使用自动写入，请在执行完字库写入后点击")
    Tooltip(write_font_compressed_button, "压缩GB2312字库，萝狮虎118K、123H版本及后续版本使用")
    Tooltip(write_font_uncompressed_button, "全量GB2312字库，用于萝狮虎118H版本，后续未使用")
    Tooltip(write_font_old_button, "萝狮虎117版本及之前版本使用，旧字库")
    Tooltip(write_pinyin_old_index_button, "123版本拼音索引，如果不使用自动写入，请在执行完字库写入后点击")
    Tooltip(write_pinyin_new_index_button, "124及以上版本拼音索引，如果不使用自动写入，请在执行完字库写入后点击")
    window.mainloop()


if __name__ == '__main__':
    main()
