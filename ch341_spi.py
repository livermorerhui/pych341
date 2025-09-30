# ch341_spi.py
import time
from ch341 import Ch341

class SPI_MODE:
    MODE0 = 0  # CPOL=0, CPHA=0
    MODE1 = 1  # CPOL=0, CPHA=1
    MODE2 = 2  # CPOL=1, CPHA=0
    MODE3 = 3  # CPOL=1, CPHA=1

class SoftwareSPI:
    """
    一个使用 pych341 的 GPIO 功能在软件层面实现 SPI 通信的类。
    这允许我们精确控制 SPI 模式 (CPOL/CPHA)，以兼容任何 SPI 设备。
    """
    def __init__(self, ch341_device: Ch341, sck_pin: int, mosi_pin: int, cs_pin: int, mode: int = SPI_MODE.MODE0, bit_order_msb: bool = True):
        self.dev = ch341_device
        self.sck = sck_pin
        self.mosi = mosi_pin
        self.cs = cs_pin
        self.bit_order_msb = bit_order_msb  # <-- 修正了此处的变量名

        # 根据 SPI 模式设置时钟极性 (CPOL) 和相位 (CPHA)
        self.cpol = 1 if mode in [SPI_MODE.MODE2, SPI_MODE.MODE3] else 0
        self.cpha = 1 if mode in [SPI_MODE.MODE1, SPI_MODE.MODE3] else 0

        # 初始化引脚
        self.dev.set_io_rw(io=self.sck, rw=1)   # SCK as output
        self.dev.set_io_rw(io=self.mosi, rw=1) # MOSI as output
        self.dev.set_io_rw(io=self.cs, rw=1)   # CS as output

        # 设置引脚的初始电平
        self.dev.io_write(self.cs, 1) # CS 默认为高电平（未选中）
        self.dev.io_write(self.sck, self.cpol) # SCK 默认为空闲电平

    def transfer16(self, data: int):
        """
        通过软件模拟 SPI 发送一个 16 位的数据。
        """
        # 1. 片选使能 (CS 拉低)
        self.dev.io_write(self.cs, 0)

        # 循环 16 次，发送每一位
        for i in range(16):
            # 确定要发送的位
            if self.bit_order_msb:
                bit = (data >> (15 - i)) & 1
            else:
                bit = (data >> i) & 1

            # 根据 CPHA (时钟相位) 决定何时设置数据和触发时钟
            if self.cpha == 0:
                # CPHA=0: 数据在时钟的第一个边沿被采样
                # 先设置数据线
                self.dev.io_write(self.mosi, bit)
                # 然后触发时钟边沿
                self.dev.io_write(self.sck, 1 - self.cpol) # 触发采样边沿
                self.dev.io_write(self.sck, self.cpol)     # 恢复到空闲电平
            else:
                # CPHA=1: 数据在时钟的第二个边沿被采样
                # 先触发时钟边沿
                self.dev.io_write(self.sck, 1 - self.cpol) # 触发第一个边沿
                # 然后设置数据线
                self.dev.io_write(self.mosi, bit)
                # 触发采样边沿
                self.dev.io_write(self.sck, self.cpol)     # 恢复到空闲电平

        # 2. 片选禁止 (CS 拉高)
        self.dev.io_write(self.cs, 1)
