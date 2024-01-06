import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports

import serial_utils

window = tk.Tk()


def get_all_serial_port():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def serial_port_combo_postcommand(combo: ttk.Combobox):
    combo['values'] = get_all_serial_port()


def serial_port_combo_callback(event, serial_port: str):
    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        try:
            version = serial_utils.sayhello(serial_port)
            extra_eeprom = version.endswith('K')
            messagebox.showinfo("提示", "串口连接成功！\n版本号：" + version + "\nEEPROM大小：" + ("已扩容 256KiB+" if extra_eeprom else "8KiB"))
        except Exception as e:
            messagebox.showerror("错误", str(e))
            return


def clean_eeprom(serial_port: str, progress: ttk.Progressbar):
    if len(serial_port) == 0:
        messagebox.showerror("错误", "没有选择串口！")
        return

    if not messagebox.askokcancel("警告", "该操作会清空EEPROM内所有数据(包括设置、信道、校准等)\n确定要清空EEPROM吗？"):
        return

    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        try:
            version = serial_utils.sayhello(serial_port)
            extra_eeprom = version.endswith('K')
            messagebox.showinfo("提示", "串口连接成功！\n版本号：" + version + "\nEEPROM大小：" + ("已扩容 256KiB+" if extra_eeprom else "8KiB"))
        except Exception as e:
            messagebox.showerror("错误", "串口连接失败！" + str(e))
            return

        if not extra_eeprom:
            messagebox.showinfo("未扩容固件", "未使用萝师虎扩容固件, 部分扇区可能无法被清除")
            for i in range(0, 64):
                serial_utils.write_eeprom(serial_port, b"\xff" * 128, i * 128)
                progress['value'] = int((i + 1) / 64 * 100)
                window.update()
        else:
            total_steps = 4 * 64
            current_step = 0
            for offset in range(0, 4):
                for n in range(0, 64):
                    current_step += 1
                    serial_utils.write_extra_mem(serial_port, offset, n * 128, b"\xff" * 128)
                    progress['value'] = int((current_step / total_steps) * 100)
                    window.update()
    progress['value'] = 0
    window.update()
    messagebox.showinfo("提示", "清空EEPROM成功！")


def main():
    window.title("K5/K6 小工具集")

    serial_port_label = tk.Label(window, text="串口")
    serial_port_label.grid(row=0, column=0, padx=(10, 0), pady=10, sticky='w')
    serial_port_combo = ttk.Combobox(window, values=[], width=8)
    serial_port_combo['postcommand'] = lambda: serial_port_combo_postcommand(serial_port_combo)
    serial_port_combo.bind("<<ComboboxSelected>>", lambda event: serial_port_combo_callback(event, serial_port_combo.get()))
    serial_port_combo.grid(row=0, column=1, padx=(0, 10), pady=10, sticky='w')

    button = tk.Button(window, text="清空EEPROM", command=lambda: clean_eeprom(serial_port_combo.get(), progress))
    button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='w')

    # 创建进度条
    progress = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")
    # 放置进度条在窗口底部
    progress.grid(row=3, column=0, columnspan=30, padx=10, pady=10, sticky='ew')

    window.mainloop()


if __name__ == '__main__':
    main()
