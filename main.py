import sys
import tkinter as tk
from tkinter import ttk
from const_vars import FIRMWARE_VERSION_LIST, EEPROM_SIZE
from logger import log

from functions import serial_port_combo_postcommand, serial_port_combo_callback, clean_eeprom, write_font, \
    write_font_conf, write_tone_options, write_to_the_font

window = tk.Tk()
version = '0.1'


class TextRedirector(tk.Text):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, strs):
        self.widget.insert(tk.END, strs)
        self.widget.see(tk.END)

    def flush(self):
        pass


def main():
    window.title(f'K5/K6 小工具集 v{version}')
    window.geometry('420x380')
    label1 = tk.Label(window, text=f'K5/K6 小工具集 v{version} (BG4IST - hank9999)')
    label1.place(x=10, y=10)

    label2 = tk.Label(window, text='当前操作: 无')
    label2.place(x=10, y=30)

    serial_port_label = tk.Label(window, text='串口')
    serial_port_label.place(x=10, y=60)
    serial_port_combo = ttk.Combobox(window, values=[], width=8, state='readonly')
    serial_port_combo.place(x=40, y=60)

    eeprom_size_label = tk.Label(window, text='EEPROM')
    eeprom_size_label.place(x=125, y=60)
    eeprom_size_combo = ttk.Combobox(window, values=EEPROM_SIZE, width=8, state='readonly')
    eeprom_size_combo.place(x=185, y=60)

    firmware_label = tk.Label(window, text='固件版本')
    firmware_label.place(x=270, y=60)
    firmware_combo = ttk.Combobox(window, values=FIRMWARE_VERSION_LIST, width=8, state='readonly')
    firmware_combo.place(x=325, y=60)

    serial_port_combo['postcommand'] = lambda: serial_port_combo_postcommand(serial_port_combo)
    serial_port_combo.bind(
        '<<ComboboxSelected>>',
        lambda event: serial_port_combo_callback(event, serial_port_combo.get(), label2, eeprom_size_combo,
                                                 firmware_combo)
    )

    clean_eeprom_button = tk.Button(
        window,
        text='清空EEPROM',
        command=lambda: clean_eeprom(
            serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    clean_eeprom_button.place(x=10, y=100)

    write_font_old_button = tk.Button(
        window,
        text='写入字库',
        command=lambda: write_to_the_font(
            serial_port_combo.get(), serial_port_combo.get(), window, progress, label2,
            EEPROM_SIZE.index(eeprom_size_combo.get()), FIRMWARE_VERSION_LIST.index(firmware_combo.get())
        )
    )
    write_font_old_button.place(x=105, y=100)

    textbox = tk.Text(window, width=56, height=10)
    textbox.place(x=10, y=185)
    sys.stdout = TextRedirector(textbox)

    # 创建进度条
    progress = ttk.Progressbar(window, orient='horizontal', length=397, mode='determinate')
    # 放置进度条在窗口底部
    progress.place(x=10, y=340)

    log(f'K5/K6 小工具集 v{version} BG4IST - hank9999\n')

    window.mainloop()


if __name__ == '__main__':
    main()
