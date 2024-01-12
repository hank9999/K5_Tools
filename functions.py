import dataclasses
import os
import sys
import serial_utils
import serial.tools.list_ports
from logger import log
import tkinter as tk
from tkinter import messagebox, ttk
if sys.version_info < (3, 10):
    import importlib_resources
else:
    import importlib.resources as importlib_resources


@dataclasses.dataclass
class SerialPortCheckResult:
    status: bool
    message: str
    extra_eeprom: bool


def get_all_serial_port():
    ports = serial.tools.list_ports.comports()
    ports = [port.device for port in ports]
    log('可用串口：' + str(ports))
    return ports


def serial_port_combo_postcommand(combo: ttk.Combobox):
    combo['values'] = get_all_serial_port()


def check_serial_port(serial_port: serial.Serial) -> SerialPortCheckResult:
    try:
        version = serial_utils.sayhello(serial_port)
        extra_eeprom = version.endswith('K')
        msg = '串口连接成功！\n版本号：' + version + '\nEEPROM大小：' + ('已扩容 128KiB+' if extra_eeprom else '8KiB')
        log(msg)
        return SerialPortCheckResult(True, msg, extra_eeprom)
    except Exception as e:
        msg = '串口连接失败！<-' + str(e)
        log(msg)
        return SerialPortCheckResult(False, msg, False)


def serial_port_combo_callback(event, serial_port: str):
    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        try:
            version = serial_utils.sayhello(serial_port)
            extra_eeprom = version.endswith('K')
            msg = '串口连接成功！\n版本号：' + version + '\nEEPROM大小：' + ('已扩容 128KiB+' if extra_eeprom else '8KiB')
            log(msg)
            messagebox.showinfo('提示', msg)
        except Exception as e:
            log('串口连接失败！<-' + str(e))
            messagebox.showerror('错误', '串口连接失败！<-' + str(e))
            return
        serial_check = check_serial_port(serial_port)
        if serial_check.status:
            messagebox.showinfo('提示', serial_check.message)
        else:
            messagebox.showerror('错误', serial_check.message)


def clean_eeprom(serial_port: str, window: tk.Tk, progress: ttk.Progressbar):
    log('开始清空EEPROM流程')
    log('选择的串口: ' + serial_port)
    if len(serial_port) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        return

    if not messagebox.askokcancel('警告', '该操作会清空EEPROM内所有数据(包括设置、信道、校准等)\n确定要清空EEPROM吗？'):
        return

    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port)
        if not serial_check.status:
            messagebox.showerror('错误', serial_check.message)
            return

        if not serial_check.extra_eeprom:
            log('非萝狮虎(losehu) 扩容固件，部分扇区可能无法被清除')
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
                    log('进度: ' + str(present) + '%' + ', ' + 'offset=' + hex(offset) + ', ' + 'extra=' + hex(
                        n * 128))
                    window.update()
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('清空EEPROM成功！')
    messagebox.showinfo('提示', '清空EEPROM成功！')


def write_font(serial_port: str, window: tk.Tk, progress: ttk.Progressbar):
    log('开始写入字库流程')
    log('选择的串口: ' + serial_port)
    if len(serial_port) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        return

    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port)
        if not serial_check.status:
            messagebox.showerror('错误', serial_check.message)
            return

        if not serial_check.extra_eeprom:
            log('非萝狮虎(losehu) 扩容固件，无法写入字库！')
            messagebox.showerror('未扩容固件', '未使用 萝狮虎(losehu) 扩容固件，无法写入字库！')
            return
        else:
            resource_dir = str(importlib_resources.files('resources'))
            if resource_dir.startswith('MultiplexedPath'):
                resource_dir = resource_dir[17:-2]
            font_file = str(os.path.join(resource_dir, 'font.bin'))
            with open(font_file, 'rb') as f:
                data = f.read()
            if len(data) != 0x1C320:
                log('字库文件大小错误！')
                messagebox.showerror('错误', '字库文件大小错误！')
                return
            total_page = 0x1C320 // 128
            addr = 0x2000
            current_step = 0
            while addr < 0x1C320:
                write_data = data[:128]
                data = data[128:]
                if addr < 0x10000:
                    serial_utils.write_extra_mem(serial_port, 0x0, addr, write_data)
                else:
                    serial_utils.write_extra_mem(serial_port, 0x1, addr - 0x10000, write_data)
                addr += 128
                current_step += 1
                present = int((current_step / total_page) * 100)
                progress['value'] = present
                log('进度: ' + str(present) + '%' + ', ' + 'addr=' + hex(addr))
                window.update()
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('写入字库成功！')
    messagebox.showinfo('提示', '写入字库成功！')
