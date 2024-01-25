import dataclasses
import random
import struct
from typing import Union, List

from serial import Serial

from const_vars import FIRMWARE_VERSION_LIST, EEPROM_SIZE, FontType
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
    raw_version_text: str


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
        return SerialPortCheckResult(True, msg, firmware_version, eeprom_size, version)
    except Exception as e:
        msg = '串口连接失败！<-' + str(e)
        log(msg)
        return SerialPortCheckResult(False, msg, 2, 0, '')


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


def write_data(serial_port: Serial, start_addr: int, data: Union[bytes, List[int]],
               progress: ttk.Progressbar, window: tk.Tk, step: int = 128):
    data_len = len(data)
    total_page = data_len // 128
    addr = start_addr
    current_step = 0
    offset = 0
    while addr < start_addr + data_len:
        percent_float = (current_step / total_page) * 100
        percent = int(percent_float)
        progress['value'] = percent
        log(f'进度: {percent_float:.1f}%, addr={hex(addr)}', '')
        window.update()

        writing_data = bytes(data[:step])
        data = data[step:]
        if addr - offset * 0x10000 >= 0x10000:
            offset += 1
        serial_utils.write_extra_eeprom(serial_port, offset, addr - offset * 0x10000, writing_data)
        addr += step
        current_step += 1
    progress['value'] = 0
    window.update()


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
            write_data(serial_port, 0, b'\xff' * target_eeprom_offset, progress, window)
        progress['value'] = 0
        window.update()
    log('清空EEPROM成功！')
    status_label['text'] = '当前操作: 无'
    serial_utils.reset_radio(serial_port)
    messagebox.showinfo('提示', '清空EEPROM成功！')


def write_font(serial_port_text: str, window: tk.Tk, progress: ttk.Progressbar, status_label: tk.Label,
               eeprom_size: int, firmware_version: int, font_type: FontType, is_continue: bool = False):
    log('开始写入字库流程')
    log(f'字库版本: {font_type.value}')
    log('选择的串口: ' + serial_port_text)
    status_label['text'] = f'当前操作: 写入字库 ({font_type.value})'
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

        if font_type == FontType.GB2312_UNCOMPRESSED and eeprom_size < 2:
            msg = f'EEPROM小于256KiB，无法写入H固件字库！'
            log(msg)
            messagebox.showinfo('EEPROM大小不足', msg)
            status_label['text'] = '当前操作: 无'
            return

        addr = 0x2E00
        if font_type == FontType.GB2312_COMPRESSED:
            font_data = font.GB2312_COMPRESSED
        elif font_type == FontType.GB2312_UNCOMPRESSED:
            font_data = font.GB2312_UNCOMPRESSED
        elif font_type == FontType.LOSEHU_FONT:
            font_data = font.LOSEHU_FONT
            addr = 0x2000
        else:
            messagebox.showerror('错误', '未知字库类型！')
            status_label['text'] = '当前操作: 无'
            return
        write_data(serial_port, addr, font_data, progress, window)
        progress['value'] = 0
        window.update()
    log('写入字库成功！')
    status_label['text'] = '当前操作: 无'
    if not is_continue:
        serial_utils.reset_radio(serial_port)
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
        write_data(serial_port, 0x2480, font.FONT_CONF, progress, window)
        progress['value'] = 0
        window.update()
    log('写入字库配置成功！')
    status_label['text'] = '当前操作: 无'
    if not is_continue:
        serial_utils.reset_radio(serial_port)
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
        write_data(serial_port, 0x2C00, data, progress, window)
        progress['value'] = 0
        window.update()
    log('写入亚音参数成功！')
    status_label['text'] = '当前操作: 无'
    if not is_continue:
        serial_utils.reset_radio(serial_port)
        messagebox.showinfo('提示', '写入亚音参数成功！')


# 复位函数
def reset_radio(serial_port_text: str, status_label):
    status_label['text'] = '当前操作: 复位设备'
    log('正在复位设备')
    with serial.Serial(serial_port_text, 38400, timeout=2) as serial_port:
        serial_utils.reset_radio(serial_port)
    status_label['text'] = '当前操作: 无'


# 写入字库等信息的总函数
def auto_write_font(serial_port_text: str, window: tk.Tk, progress: ttk.Progressbar,
                    status_label: tk.Label, eeprom_size: int, firmware_version: int):
    with serial.Serial(serial_port_text, 38400, timeout=2) as serial_port:
        result = check_serial_port(serial_port, False)
        version = result.raw_version_text
        if version.startswith('LOSEHU'):
            version_code = version[-1]
            if version_code == 'H':
                font_type = FontType.GB2312_UNCOMPRESSED
            elif version_code == 'K':
                version_number = int(version[6:9])
                if version_number < 118:
                    font_type = FontType.LOSEHU_FONT
                else:
                    font_type = FontType.GB2312_COMPRESSED
        else:
            version_code = 'other'
    if version_code == 'K' or version_code == 'H':
        if version_number < 118:
            log(f'正在进行 写入{version_number}{version_code}版字库')
            write_font(serial_port_text, window, progress, status_label, eeprom_size, firmware_version, font_type)
            reset_radio(serial_port_text, status_label)
            messagebox.showinfo('提示', f'{version_number}{version_code}版本字库\n写入成功')
        else:
            log(f'正在进行 1/3: 写入{version_number}{version_code}版字库')
            write_font(serial_port_text, window, progress, status_label, eeprom_size, firmware_version, font_type, True)
            log(f'正在进行 2/3: 写入字库配置')
            write_font_conf(serial_port_text, window, progress, status_label, eeprom_size, firmware_version, True)
            log(f'正在进行 3/3: 写入亚音参数')
            write_tone_options(serial_port_text, window, progress, status_label, eeprom_size, firmware_version, True)
            reset_radio(serial_port_text, status_label)
            messagebox.showinfo('提示', f'{version_number}{version_code}版本字库\n字库配置\n亚音参数\n写入成功！')
    else:
        messagebox.showinfo('提示', f'非LOSEHU扩容固件，无法写入')