from loguru import logger
import hid
import sys
import struct

logger.remove()
logger.add(
    sys.stdout,
    format="<g>{time:YYYY:MM:DD HH:mm:ss}</g> | {message}",
    level="INFO",
    colorize=True
)

class MeterData:
    def __init__(self, OffPer, OffHour, RecmA, Ah, Wh, RecTime, RunTime, dp, dm, TempIn, TempOut, vol, cur, RecGrp, reserved):
        self.OffPer = OffPer
        self.OffHour = OffHour
        self.RecmA = RecmA
        self.Ah = Ah
        self.Wh = Wh
        self.RecTime = RecTime
        self.RunTime = RunTime
        self.dp = dp
        self.dm = dm
        self.TempIn = TempIn
        self.TempOut = TempOut
        self.vol = vol
        self.cur = cur
        self.RecGrp = RecGrp
        if not isinstance(reserved, bytes) or len(reserved) != 7:
            raise ValueError("reserved must be a bytes object of length 7")
        self.reserved = reserved

    @classmethod
    def from_bytes(cls, data):
        if len(data) != 52:
            raise ValueError("Data must be exactly 52 bytes")
        unpacked = struct.unpack('<BBHffIIffffffB7s', data)
        return cls(*unpacked)

    def to_bytes(self):
        return struct.pack('<BBHffIIffffffB7s',
                           self.OffPer,
                           self.OffHour,
                           self.RecmA,
                           self.Ah,
                           self.Wh,
                           self.RecTime,
                           self.RunTime,
                           self.dp,
                           self.dm,
                           self.TempIn,
                           self.TempOut,
                           self.vol,
                           self.cur,
                           self.RecGrp,
                           self.reserved)

class USBSPac:
    def __init__(self, command, length, buf, verify):
        self.command = command  # byte
        self.length = length    # byte
        if isinstance(buf, bytes) and len(buf) == 52:
            self.buf = buf
        else:
            raise ValueError("buf must be a bytes object of length 52")
        self.verify = verify    # byte

    @classmethod
    def from_bytes(cls, data):
        if len(data) < 55:
            raise ValueError("Data too short to parse USBSPac")
        command = data[0]
        length = data[1]
        buf = data[2:54]  # 52 bytes
        verify = data[54]
        return cls(command, length, buf, verify)

    def to_bytes(self):
        return bytes([self.command, self.length]) + self.buf + bytes([self.verify])

class USBPac:
    def __init__(self, start, head, idx1, idx2, needAck, free, pac, verify):
        self.start = start   # byte
        self.head = head     # byte
        self.idx1 = idx1     # byte
        self.idx2 = idx2     # byte
        self.needAck = needAck  # byte
        if isinstance(free, bytes) and len(free) == 3:
            self.free = free
        else:
            raise ValueError("free must be a bytes object of length 3")
        self.pac = pac       # USBSPac
        self.verify = verify # byte

    @classmethod
    def from_bytes(cls, data):
        if len(data) < 64:
            raise ValueError("Data too short to parse USBPac")
        start = data[0]
        head = data[1]
        idx1 = data[2]
        idx2 = data[3]
        needAck = data[4]
        free = data[5:8]  # 3 bytes
        pac_data = data[8:8+55]  # USBSPac is 55 bytes
        pac = USBSPac.from_bytes(pac_data)
        verify = data[8+55]
        return cls(start, head, idx1, idx2, needAck, free, pac, verify)

    def to_bytes(self):
        pac_bytes = self.pac.to_bytes()
        if len(pac_bytes) != 55:
            raise ValueError("USBSPac bytes must be 55 bytes")
        return bytes([self.start, self.head, self.idx1, self.idx2, self.needAck]) + \
               self.free + \
               pac_bytes + \
               bytes([self.verify])

def print_hex_data(data):
    hex_str = ' '.join([f'{byte:02X}' for byte in data])
    return hex_str

def read_device_data(device, read_timeout=1000):
    try:
        device.set_nonblocking(0)
        
        print('\n')

        while True:
            try:
                data = device.read(64, timeout_ms=read_timeout)

                if data:
                    # hex_data = print_hex_data(data)
                    # logger.info(f"Raw Hex Data: {hex_data}")
                    
                    data_bytes = bytes(data)
                    usb_pac = USBPac.from_bytes(data_bytes)

                    meter_data = MeterData.from_bytes(usb_pac.pac.buf)

                    print(f'Time: {meter_data.RunTime} Volt: {meter_data.vol:.4f} Current: {abs(meter_data.cur):.4f} Power: {abs(meter_data.vol * meter_data.cur):.4f}', end='\r', flush=True)
                
                    # print(usb_pac.idx1, usb_pac.idx2)

                    # print(meter_data.RecmA)

            except KeyboardInterrupt:
                logger.warning("Manually terminated")
                break
                
    except Exception as e:
        logger.error(f"An Error occurred caused {str(e)}")

def get_device_info():
    try:
        device = hid.device()
        device.open(0x0716, 0x5053)
        
        logger.success('Connected to Device(0x0716, 0x5053)')
        
        manufacturer = device.get_manufacturer_string()
        product = device.get_product_string()
        serial_number = device.get_serial_number_string()
        
        logger.info(f"Manufacturer: {manufacturer}")
        logger.info(f"Product: {product}")
        # logger.info(f"HID Serial Number: {serial_number}")

        logger.info("Start listening on Device(0x0716, 0x5053)")
        read_device_data(device)
        
        device.close()
        logger.success("Device disconnected")
    except hid.HIDException as e:
        logger.error(f"Cannot connect to device caused {str(e)}")
    except Exception as e:
        logger.error(f"An Error occurred caused {str(e)}")

if __name__ == "__main__":
    get_device_info()