import dataclasses
import random
import struct

from const_vars import FIRMWARE_VERSION_LIST, EEPROM_SIZE
import serial_utils
import serial.tools.list_ports
from logger import log
import tkinter as tk
from tkinter import messagebox, ttk
from resources import tone, font

@dataclasses.dataclass
class SerialPortCheckResult:
    status: bool
    message: str
    firmware_version: int
    eeprom_size: int


def get_all_serial_port():
    ports = serial.tools.list_ports.comports()
    ports = [port.device for port in ports]
    log('可用串口: ' + str(ports))
    return ports


def serial_port_combo_postcommand(combo: ttk.Combobox):
    combo['values'] = get_all_serial_port()


def check_eeprom_writeable(serial_port: serial.Serial, offset: int, extra: int) -> bool:
    # 读取原始数据
    read_data = serial_utils.read_extra_eeprom(serial_port, offset, extra, 8)
    # 写入随机数据
    random_bytes = bytes([random.randint(0, 255) for _ in range(8)])
    serial_utils.write_extra_eeprom(serial_port, offset, extra, random_bytes)
    # 读取写入的数据
    read_write_data = serial_utils.read_extra_eeprom(serial_port, offset, extra, 8)
    # 恢复原始数据
    serial_utils.write_extra_eeprom(serial_port, offset, extra, read_data)

    return read_write_data == random_bytes


def check_serial_port(serial_port: serial.Serial,
                      auto_detect: bool = True) -> SerialPortCheckResult:
    try:
        version = serial_utils.sayhello(serial_port)
        eeprom_size = 0
        if auto_detect:
            if version.startswith('LOSEHU'):
                firmware_version = 0
                if version.endswith('K') or version.endswith('H'):
                    firmware_version = 1
            else:
                firmware_version = 2

            if firmware_version == 1:
                # 检查EEPROM大小
                for i in range(1, 5):
                    # 128 KiB offset 0x1, 256 KiB offset 0x3, 384 KiB offset 0x5, 512 KiB offset 0x7
                    # 1 -> 0x1, 2 -> 0x3, 3 -> 0x5, 4 -> 0x7 符合 2n-1
                    if check_eeprom_writeable(serial_port, 2 * i - 1, 0x8000):
                        eeprom_size = i
                    else:
                        break
            msg = f'串口连接成功！\n版本号: {version}\n自动检测结果如下:\n固件版本: {FIRMWARE_VERSION_LIST[firmware_version]}\n'
            if firmware_version != 1:
                msg += f'非{FIRMWARE_VERSION_LIST[1]}固件无法自动检测EEPROM大小\n'
            else:
                msg += f'EEPROM大小: {EEPROM_SIZE[eeprom_size]}'
            log(msg)
        else:
            msg = f'串口连接成功！\n版本号: {version}\n'
            log(msg)
            firmware_version = 2
            eeprom_size = 0
        return SerialPortCheckResult(True, msg, firmware_version, eeprom_size)
    except Exception as e:
        msg = '串口连接失败！<-' + str(e)
        log(msg)
        return SerialPortCheckResult(False, msg, 2, 0)


def serial_port_combo_callback(_, serial_port: str, status_label: tk.Label, eeprom_size_combo: ttk.Combobox,
                               firmware_combo: ttk.Combobox):
    status_label['text'] = '当前操作: 检查串口连接'
    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port)
        if serial_check.status:
            messagebox.showinfo('提示', serial_check.message)
        else:
            messagebox.showerror('错误', serial_check.message)
        firmware_combo.set(FIRMWARE_VERSION_LIST[serial_check.firmware_version])
        eeprom_size_combo.set(EEPROM_SIZE[serial_check.eeprom_size])
    status_label['text'] = '当前操作: 无'


def clean_eeprom(serial_port: str, window: tk.Tk, progress: ttk.Progressbar, status_label: tk.Label, eeprom_size: int,
                 firmware_version: int):
    log('开始清空EEPROM流程')
    log('选择的串口: ' + serial_port)
    status_label['text'] = '当前操作: 清空EEPROM'
    if len(serial_port) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        status_label['text'] = '当前操作: 无'
        return

    if not messagebox.askokcancel('警告', '该操作会清空EEPROM内所有数据(包括设置、信道、校准等)\n确定要清空EEPROM吗？'):
        return

    with serial.Serial(serial_port, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port, False)
        if not serial_check.status:
            messagebox.showerror('错误', serial_check.message)
            status_label['text'] = '当前操作: 无'
            return

        log(f'选择固件版本: {FIRMWARE_VERSION_LIST[firmware_version]} EEPROM大小: {EEPROM_SIZE[eeprom_size]}')

        if firmware_version != 1:
            msg = f'非{FIRMWARE_VERSION_LIST[1]}固件，部分扇区可能无法被清除 (仅清除前8KiB原厂大小数据)'
            log(msg)
            messagebox.showinfo('未扩容固件', msg)
            for i in range(0, 64):
                percent_float = (i + 1) / 64 * 100
                percent = int(percent_float)
                progress['value'] = percent
                log(f'进度: {percent_float:.1f}%, offset={hex(i * 128)}', '')
                window.update()

                serial_utils.write_eeprom(serial_port, i * 128, b'\xff' * 128)
        else:
            target_eeprom_offset = 0x2000
            if eeprom_size > 0:
                target_eeprom_offset = 0x20000 * eeprom_size
            total_steps = target_eeprom_offset // 128
            current_step = 0
            addr = 0x0
            offset = 0x0
            while addr < target_eeprom_offset:
                percent_float = (current_step / total_steps) * 100
                percent = int(percent_float)
                progress['value'] = percent
                log(f'进度: {percent_float:.1f}%, addr={hex(addr)}', '')
                window.update()

                if addr - offset * 0x10000 >= 0x10000:
                    offset += 1
                serial_utils.write_extra_eeprom(serial_port, offset, addr - offset * 0x10000, b'\xff' * 128)
                addr += 128
                current_step += 1
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('清空EEPROM成功！')
    status_label['text'] = '当前操作: 无'
    messagebox.showinfo('提示', '清空EEPROM成功！')


def write_font(serial_port_text: str, window: tk.Tk, progress: ttk.Progressbar, status_label: tk.Label,
               eeprom_size: int, firmware_version: int, compress: bool = False):
    log('开始写入字库流程')
    font_version = 'H' if not compress else 'K'
    log(f'字库版本: {font_version}')
    log('选择的串口: ' + serial_port_text)
    status_label['text'] = f'当前操作: 写入字库 ({font_version})'
    if len(serial_port_text) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        status_label['text'] = '当前操作: 无'
        return

    with serial.Serial(serial_port_text, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port, False)
        if not serial_check.status:
            messagebox.showerror('错误', serial_check.message)
            status_label['text'] = '当前操作: 无'
            return

        log(f'选择固件版本: {FIRMWARE_VERSION_LIST[firmware_version]} EEPROM大小: {EEPROM_SIZE[eeprom_size]}')

        if firmware_version != 1:
            msg = f'非{FIRMWARE_VERSION_LIST[1]}固件，无法写入字库！'
            log(msg)
            messagebox.showinfo('未扩容固件', msg)
            status_label['text'] = '当前操作: 无'
            return

        if eeprom_size < 1:
            msg = f'EEPROM小于128KiB，无法写入字库！'
            log(msg)
            messagebox.showinfo('EEPROM大小不足', msg)
            status_label['text'] = '当前操作: 无'
            return

        if not compress and eeprom_size < 2:
            msg = f'EEPROM小于256KiB，无法写入H固件字库！'
            log(msg)
            messagebox.showinfo('EEPROM大小不足', msg)
            status_label['text'] = '当前操作: 无'
            return

        if compress:
            font_data = font.GB2312_COMPRESSED
        else:
            font_data = font.GB2312_UNCOMPRESSED
        font_len = len(font_data)
        total_page = font_len // 128
        addr = 0x2E00
        current_step = 0
        offset = 0
        while addr < 0x2E00 + font_len:
            percent_float = (current_step / total_page) * 100
            percent = int(percent_float)
            progress['value'] = percent
            log(f'进度: {percent_float:.1f}%, addr={hex(addr)}', '')
            window.update()

            write_data = bytes(font_data[:128])
            font_data = font_data[128:]
            if addr - offset * 0x10000 >= 0x10000:
                offset += 1
            serial_utils.write_extra_eeprom(serial_port, offset, addr - offset * 0x10000, write_data)
            addr += 128
            current_step += 1
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('写入字库成功！')
    status_label['text'] = '当前操作: 无'
    write_font_conf(serial_port_text, window, progress, status_label, eeprom_size, firmware_version, True)
    write_tone_options(serial_port_text, window, progress, status_label, eeprom_size, firmware_version, True)
    messagebox.showinfo('提示', '写入字库成功！')


def write_font_conf(serial_port_text: str, window: tk.Tk, progress: ttk.Progressbar, status_label: tk.Label,
                    eeprom_size: int, firmware_version: int, is_continue: bool = False):
    log('开始写入字库配置')
    log('选择的串口: ' + serial_port_text)
    status_label['text'] = f'当前操作: 写入字库配置'
    if len(serial_port_text) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        status_label['text'] = '当前操作: 无'
        return

    with serial.Serial(serial_port_text, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port, False)
        if not serial_check.status:
            messagebox.showerror('错误', serial_check.message)
            status_label['text'] = '当前操作: 无'
            return

        log(f'选择固件版本: {FIRMWARE_VERSION_LIST[firmware_version]} EEPROM大小: {EEPROM_SIZE[eeprom_size]}')

        if firmware_version != 1:
            msg = f'非{FIRMWARE_VERSION_LIST[1]}固件，无法写入字库配置！'
            log(msg)
            messagebox.showinfo('未扩容固件', msg)
            status_label['text'] = '当前操作: 无'
            return

        if eeprom_size < 1:
            msg = f'EEPROM小于128KiB，无法写入字库配置！'
            log(msg)
            messagebox.showinfo('EEPROM大小不足', msg)
            status_label['text'] = '当前操作: 无'
            return
        font_data = font.FONT_CONF
        font_len = len(font_data)
        total_page = font_len // 128
        addr = 0x2480
        current_step = 0
        offset = 0
        while addr < 0x2480 + font_len:
            percent_float = (current_step / total_page) * 100
            percent = int(percent_float)
            progress['value'] = percent
            log(f'进度: {percent_float:.1f}%, addr={hex(addr)}', '')
            window.update()

            write_data = bytes(font_data[:128])
            font_data = font_data[128:]
            if addr - offset * 0x10000 >= 0x10000:
                offset += 1
            serial_utils.write_extra_eeprom(serial_port, offset, addr - offset * 0x10000, write_data)
            addr += 128
            current_step += 1
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('写入字库配置成功！')
    status_label['text'] = '当前操作: 无'
    if not is_continue:
        messagebox.showinfo('提示', '写入字库配置成功！')


def write_tone_options(serial_port_text: str, window: tk.Tk, progress: ttk.Progressbar, status_label: tk.Label,
                       eeprom_size: int, firmware_version: int, is_continue: bool = False):
    log('开始写入亚音参数')
    log('选择的串口: ' + serial_port_text)
    status_label['text'] = f'当前操作: 写入亚音参数'
    if len(serial_port_text) == 0:
        log('没有选择串口！')
        messagebox.showerror('错误', '没有选择串口！')
        status_label['text'] = '当前操作: 无'
        return

    with serial.Serial(serial_port_text, 38400, timeout=2) as serial_port:
        serial_check = check_serial_port(serial_port, False)
        if not serial_check.status:
            messagebox.showerror('错误', serial_check.message)
            status_label['text'] = '当前操作: 无'
            return

        log(f'选择固件版本: {FIRMWARE_VERSION_LIST[firmware_version]} EEPROM大小: {EEPROM_SIZE[eeprom_size]}')

        if firmware_version != 1:
            msg = f'非{FIRMWARE_VERSION_LIST[1]}固件，无法写入亚音参数！'
            log(msg)
            messagebox.showinfo('未扩容固件', msg)
            status_label['text'] = '当前操作: 无'
            return

        if eeprom_size < 1:
            msg = f'EEPROM小于128KiB，无法写入亚音参数！'
            log(msg)
            messagebox.showinfo('EEPROM大小不足', msg)
            status_label['text'] = '当前操作: 无'
            return
        data = b''
        for tone_data in tone.CTCSS_OPTIONS + tone.DCS_OPTIONS:
            data += struct.pack('<H', tone_data)
        data_len = len(data)
        total_page = data_len // 128
        addr = 0x2C00
        current_step = 0
        offset = 0
        while addr < 0x2C00 + data_len:
            percent_float = (current_step / total_page) * 100
            percent = int(percent_float)
            progress['value'] = percent
            log(f'进度: {percent_float:.1f}%, addr={hex(addr)}', '')
            window.update()

            write_data = data[:128]
            data = data[128:]
            if addr - offset * 0x10000 >= 0x10000:
                offset += 1
            serial_utils.write_extra_eeprom(serial_port, offset, addr - offset * 0x10000, write_data)
            addr += 128
            current_step += 1
        progress['value'] = 0
        window.update()
        serial_utils.reset_radio(serial_port)
    log('写入亚音参数成功！')
    status_label['text'] = '当前操作: 无'
    if not is_continue:
        messagebox.showinfo('提示', '写入亚音参数成功！')
