import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports

import serial_utils

window = tk.Tk()


def log(msg: str):
    print(msg)


def get_all_serial_port():
    ports = serial.tools.list_ports.comports()
    ports = [port.device for port in ports]
    log('可用串口：' + str(ports))
    return ports


def serial_port_combo_postcommand(combo: ttk.Combobox):
    combo['values'] = get_all_serial_port()


def serial_port_combo_callback(event, serial_port: str):
    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        try:
            version = serial_utils.sayhello(serial_port)
            extra_eeprom = version.endswith('K')
            msg = '串口连接成功！\n版本号：' + version + '\nEEPROM大小：' + ('已扩容 256KiB+' if extra_eeprom else '8KiB')
            log(msg)
            messagebox.showinfo('提示', msg)
        except Exception as e:
            log('串口连接失败！<-' + str(e))
            messagebox.showerror('错误', '串口连接失败！<-' + str(e))
            return


def clean_eeprom(serial_port: str, progress: ttk.Progressbar):
    log('开始清空EEPROM流程')
    log('选择的串口: ' + serial_port)
    if len(serial_port) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        return

    if not messagebox.askokcancel('警告', '该操作会清空EEPROM内所有数据(包括设置、信道、校准等)\n确定要清空EEPROM吗？'):
        return

    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        try:
            version = serial_utils.sayhello(serial_port)
            extra_eeprom = version.endswith('K')
            log('串口连接成功！\n版本号：' + version + '\nEEPROM大小：' + ('已扩容 256KiB+' if extra_eeprom else '8KiB'))
        except Exception as e:
            log('串口连接失败！<-' + str(e))
            messagebox.showerror('错误', '串口连接失败！<-' + str(e))
            return

        if not extra_eeprom:
            log('非萝狮虎(losehu) 扩容固件扩容固件，部分扇区可能无法被清除')
            messagebox.showinfo('未扩容固件', '未使用 萝狮虎(losehu) 扩容固件, 部分扇区可能无法被清除')
            for i in range(0, 64):
                serial_utils.write_eeprom(serial_port, b'\xff' * 128, i * 128)
                present = int((i + 1) / 64 * 100)
                progress['value'] = present
                log('进度: ' + str(present) + '%' + ', ' + 'offset=' + hex(i * 128))
                window.update()
        else:
            total_steps = 512 * 2
            current_step = 0
            for offset in range(0, 2):
                for n in range(0, 512):
                    current_step += 1
                    serial_utils.write_extra_mem(serial_port, offset, n * 128, b'\xff' * 128)
                    present = int((current_step / total_steps) * 100)
                    progress['value'] = present
                    log('进度: ' + str(present) + '%' + ', ' + 'offset=' + hex(offset) + ', ' + 'add_offset=' + hex(n * 128))
                    window.update()
                    window.update()
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('清空EEPROM成功！')
    messagebox.showinfo('提示', '清空EEPROM成功！')

def main():
    window.title('K5/K6 小工具集')
    tk.Label(window, text='K5/K6 小工具集 BG4IST - hank9999').grid(row=0, column=0, columnspan=26, padx=10, pady=10, sticky='w')
    log('K5/K6 小工具集 BG4IST - hank9999\n')

    serial_port_label = tk.Label(window, text='串口')
    serial_port_label.grid(row=1, column=0, padx=(10, 0), pady=10, sticky='w')
    serial_port_combo = ttk.Combobox(window, values=[], width=8)
    serial_port_combo['postcommand'] = lambda: serial_port_combo_postcommand(serial_port_combo)
    serial_port_combo.bind('<<ComboboxSelected>>', lambda event: serial_port_combo_callback(event, serial_port_combo.get()))
    serial_port_combo.grid(row=1, column=1, padx=(0, 10), pady=10, sticky='w')

    button = tk.Button(window, text='清空EEPROM', command=lambda: clean_eeprom(serial_port_combo.get(), progress))
    button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='w')

    # 创建进度条
    progress = ttk.Progressbar(window, orient='horizontal', length=260, mode='determinate')
    # 放置进度条在窗口底部
    progress.grid(row=3, column=0, columnspan=26, padx=10, pady=10, sticky='ew')

    window.mainloop()


if __name__ == '__main__':
    main()
