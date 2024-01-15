import struct
import serial
from logger import log


def xor_arr(data: bytes):
    tbl = [22, 108, 20, 230, 46, 145, 13, 64, 33, 53, 213, 64, 19, 3, 233, 128]
    x = b""
    r = 0
    for byte in data:
        x += bytes([byte ^ tbl[r]])
        r = (r + 1) % len(tbl)
    return x


def calculate_crc16_xmodem(data: bytes):
    poly = 0x1021
    crc = 0x0
    for byte in data:
        crc = crc ^ (byte << 8)
        for i in range(8):
            crc = crc << 1
            if crc & 0x10000:
                crc = (crc ^ poly) & 0xFFFF
    return crc & 0xFFFF


def send_command(serial_port: serial.Serial, data: bytes):
    crc = calculate_crc16_xmodem(data)
    data2 = data + struct.pack("<H", crc)

    command = struct.pack(">HBB", 0xabcd, len(data), 0) + \
              xor_arr(data2) + \
              struct.pack(">H", 0xdcba)
    try:
        result = serial_port.write(command)
    except Exception:
        raise Exception("串口写入数据失败！")
    return result


def receive_reply(serial_port: serial.Serial):
    header = serial_port.read(4)
    if len(header) != 4:
        raise Exception("数据头长度不正确！")
    if header[0] != 0xAB or header[1] != 0xCD or header[3] != 0x00:
        raise Exception("数据头响应错误！")

    cmd = serial_port.read(int(header[2]))
    if len(cmd) != int(header[2]):
        raise Exception("指令长度不正确！")

    footer = serial_port.read(4)

    if len(footer) != 4:
        raise Exception("尾部数据长度不正确！")

    if footer[2] != 0xDC or footer[3] != 0xBA:
        raise Exception("尾部数据响应错误！")

    cmd2 = xor_arr(cmd)
    return cmd2


def get_string(data: bytes, begin: int, max_len: int):
    tmp_len = min(max_len + 1, len(data))
    s = [data[i] for i in range(begin, tmp_len)]
    index = 0
    for key, val in enumerate(s):
        index = key
        if val < ord(' ') or val > ord('~'):
            break
    return ''.join(chr(x) for x in s[0:index])


def sayhello(serial_port: serial.Serial):
    log('发送hello指令')
    hello_packet = b"\x14\x05\x04\x00\x6a\x39\x57\x64"

    try:
        tries = 5
        while True:
            send_command(serial_port, hello_packet)
            o = receive_reply(serial_port)
            if o:
                break
            tries -= 1
            if tries == 0:
                raise Exception("没有收到电台应答包！")
    except Exception as e:
        raise Exception("没有收到电台应答包！<-" + str(e))
    firmware = get_string(o, 4, 16)
    return firmware


def read_eeprom(serial_port: serial.Serial, offset: int, length: int):
    read_mem = b"\x1b\x05\x08\x00" + \
        struct.pack("<HBB", offset, length, 0) + \
        b"\x6a\x39\x57\x64"
    send_command(serial_port, read_mem)
    o = receive_reply(serial_port)
    return o[8:]


def write_eeprom(serial_port, data, offset):
def write_eeprom(serial_port: serial.Serial, offset: int, data: bytes):
    dlen = len(data)
    write_mem = b"\x1d\x05" + \
                struct.pack("<BBHBB", dlen + 8, 0, offset, dlen, 1) + \
                b"\x6a\x39\x57\x64" + data

    send_command(serial_port, write_mem)
    o = receive_reply(serial_port)

    if (o[0] == 0x1e
            and
            o[4] == (offset & 0xff)
            and
            o[5] == (offset >> 8) & 0xff):
        return True
    else:
        raise Exception("写入前8KiB EEPROM响应错误！")


def write_extra_eeprom(serial_port: serial.Serial, offset: int, add: int, data: bytes):
    add = struct.pack("<H", add)
    length = len(data) + len(add)

    write_mem = b"\x38\x05\x1c\x00" + \
                struct.pack("<HBB", offset, length, 0) + \
                b"\x6a\x39\x57\x64" + \
                add + data

    send_command(serial_port, write_mem)
    o = receive_reply(serial_port)

    if (o[0] == 0x1e
            and
            o[4] == (offset & 0xff)
            and
            o[5] == (offset >> 8) & 0xff):
        return True
    else:
        raise Exception("写入扩容部分 EEPROM响应错误！")


def reset_radio(serial_port: serial.Serial):
    log('发送复位指令')
    reset_packet = b"\xdd\x05\x00\x00"
    send_command(serial_port, reset_packet)
