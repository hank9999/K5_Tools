import sys
import tkinter as tk
from tkinter import ttk
from logger import log

from functions import serial_port_combo_postcommand, serial_port_combo_callback, clean_eeprom, write_font

window = tk.Tk()


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
    window.title('K5/K6 小工具集')
    label = tk.Label(window, text='K5/K6 小工具集 BG4IST - hank9999')
    label.grid(row=0, column=0, columnspan=26, padx=10, pady=10, sticky='w')

    serial_port_label = tk.Label(window, text='串口')
    serial_port_label.grid(row=1, column=0, padx=(10, 0), pady=10, sticky='w')
    serial_port_combo = ttk.Combobox(window, values=[], width=8)
    serial_port_combo['postcommand'] = lambda: serial_port_combo_postcommand(serial_port_combo)
    serial_port_combo.bind(
        '<<ComboboxSelected>>',
        lambda event: serial_port_combo_callback(event, serial_port_combo.get())
    )
    serial_port_combo.grid(row=1, column=1, padx=(0, 10), pady=10, sticky='w')

    clean_eeprom_button = tk.Button(
        window,
        text='清空EEPROM',
        command=lambda: clean_eeprom(serial_port_combo.get(), window, progress)
    )
    clean_eeprom_button.grid(row=2, column=0, columnspan=2, padx=(10, 60), pady=10, sticky='w')

    write_font_button = tk.Button(
        window,
        text='写入字库',
        command=lambda: write_font(serial_port_combo.get(), window, progress)
    )
    write_font_button.grid(row=2, column=1, padx=(60, 10), pady=10, sticky='w')

    textbox = tk.Text(window, width=40, height=10)
    textbox.grid(row=3, column=0, columnspan=26, padx=10, pady=10, sticky='w')
    sys.stdout = TextRedirector(textbox)

    # 创建进度条
    progress = ttk.Progressbar(window, orient='horizontal', length=260, mode='determinate')
    # 放置进度条在窗口底部
    progress.grid(row=4, column=0, columnspan=26, padx=10, pady=10, sticky='ew')

    log('K5/K6 小工具集 BG4IST - hank9999\n')

    window.mainloop()


if __name__ == '__main__':
    main()
