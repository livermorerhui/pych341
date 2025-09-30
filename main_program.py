# main_program.py
import time
from ch341 import Ch341
from ch341_spi import SoftwareSPI, SPI_MODE

class AD9833:
    """
    使用 SoftwareSPI 库来精确控制 AD9833。
    版本 2: 重构了状态管理，确保模式切换的正确性。
    """
    # 控制寄存器位定义
    _AD_B28      = 13
    _AD_FSELECT  = 11
    _AD_PSELECT  = 10
    _AD_RESET    = 8
    _AD_SLEEP1   = 7
    _AD_SLEEP12  = 6
    _AD_OPBITEN  = 5
    _AD_DIV2     = 3
    _AD_MODE     = 1
    
    # 频率和相位寄存器选择位
    _AD_FREQ0    = 14
    _AD_FREQ1    = 15
    
    # 波形模式的比特位掩码
    MODE_BITS_OFF      = (1 << _AD_SLEEP1) | (1 << _AD_SLEEP12)
    MODE_BITS_TRIANGLE = (1 << _AD_MODE)
    MODE_BITS_SQUARE2  = (1 << _AD_OPBITEN)
    MODE_BITS_SQUARE1  = (1 << _AD_OPBITEN) | (1 << _AD_DIV2)
    MODE_BITS_SINE     = 0

    # 用于清除所有模式位的掩码
    _MODE_CLEAR_MASK = ~ (MODE_BITS_OFF | MODE_BITS_TRIANGLE | MODE_BITS_SQUARE2 | MODE_BITS_SQUARE1)
    
    CHAN_0 = 0
    CHAN_1 = 1
    CS_PIN = 0

    def __init__(self, ch341_device: Ch341, mclk_hz: int = 25000000):
        self._mclk = mclk_hz
        self._reg_ctl = 0
        self._AD_2POW28 = 1 << 28
        self.spi = SoftwareSPI(
            ch341_device=ch341_device, sck_pin=3, mosi_pin=5,
            cs_pin=self.CS_PIN, mode=SPI_MODE.MODE2
        )

    def _spi_send(self, data: int):
        self.spi.transfer16(data)
        time.sleep(0.00001)

    def reset(self):
        self._reg_ctl |= (1 << self._AD_RESET)
        self._spi_send(self._reg_ctl)
        time.sleep(0.01)
        self._reg_ctl &= ~(1 << self._AD_RESET)
        self._spi_send(self._reg_ctl)
        print("AD9833 已复位。")

    def begin(self):
        self._reg_ctl = (1 << self._AD_B28)
        self._spi_send(self._reg_ctl)
        self.reset()
        print("AD9833 初始化完成。")

    def set_mode(self, mode_bits: int):
        self._reg_ctl &= self._MODE_CLEAR_MASK
        self._reg_ctl |= mode_bits
        self._spi_send(self._reg_ctl)

    def _calc_freq_reg(self, freq_hz: float) -> int:
        return int((freq_hz * self._AD_2POW28 / self._mclk))

    def set_frequency(self, channel: int, freq_hz: float):
        if channel not in [self.CHAN_0, self.CHAN_1]:
            raise ValueError("通道必须是 0 或 1。")
            
        freq_reg_val = self._calc_freq_reg(freq_hz)
        addr_mask = (1 << self._AD_FREQ0) if channel == self.CHAN_0 else (1 << self._AD_FREQ1)
            
        lsb_word = addr_mask | (freq_reg_val & 0x3FFF)
        msb_word = addr_mask | ((freq_reg_val >> 14) & 0x3FFF)
        
        self._spi_send(self._reg_ctl)
        self._spi_send(lsb_word)
        self._spi_send(msb_word)

    def set_active_frequency(self, channel: int):
        if channel == self.CHAN_0:
            self._reg_ctl &= ~(1 << self._AD_FSELECT)
        else:
            self._reg_ctl |= (1 << self._AD_FSELECT)
        self._spi_send(self._reg_ctl)

# --- 交互式界面 (v3 - 支持缩写) ---
def interactive_mode():
    ch341_dev = None
    ad9833 = None
    try:
        ch341_dev = Ch341(0)
        ch341_dev.open()
        
        ad9833 = AD9833(ch341_dev)
        ad9833.begin()
        
        current_freq = 1000.0
        current_mode_name = 'SINE'
        
        ad9833.set_frequency(AD9833.CHAN_0, current_freq)
        ad9833.set_active_frequency(AD9833.CHAN_0)
        ad9833.set_mode(AD9833.MODE_BITS_SINE)
        
        print(f"\n当前设置: {current_freq} Hz, {current_mode_name} 波形")

        # !!! 核心改动在这里 !!!
        mode_map = {
            # 完整名称
            'SINE': ('SINE', AD9833.MODE_BITS_SINE),
            'SQUARE1': ('SQUARE1', AD9833.MODE_BITS_SQUARE1),
            'SQUARE2': ('SQUARE2', AD9833.MODE_BITS_SQUARE2),
            'TRIANGLE': ('TRIANGLE', AD9833.MODE_BITS_TRIANGLE),
            'OFF': ('OFF', AD9833.MODE_BITS_OFF),
            # 缩写
            'SIN': ('SINE', AD9833.MODE_BITS_SINE),
            'SQ1': ('SQUARE1', AD9833.MODE_BITS_SQUARE1),
            'SQ2': ('SQUARE2', AD9833.MODE_BITS_SQUARE2),
            'TRI': ('TRIANGLE', AD9833.MODE_BITS_TRIANGLE),
        }

        while True:
            print("\n--- AD9833 控制菜单 ---")
            print("1. 设置频率 (Hz)")
            print("2. 设置波形")
            print("q. 退出")
            
            choice = input("请输入您的选择: ").strip().lower()

            if choice == '1':
                try:
                    freq_str = input("请输入频率 (Hz): ")
                    current_freq = float(freq_str)
                    if current_freq < 0:
                        print("错误: 频率不能为负数。")
                        continue
                    ad9833.set_frequency(AD9833.CHAN_0, current_freq)
                    print(f"频率已设置为: {current_freq} Hz")
                except ValueError:
                    print("错误: 请输入有效的数字。")

            elif choice == '2':
                print("可选波形: SINE(sin), SQUARE1(sq1), SQUARE2(sq2), TRIANGLE(tri), OFF")
                mode_str = input("请输入波形名称或缩写: ").strip().upper()

                if mode_str in mode_map:
                    # 从 map 中获取完整名称和命令
                    current_mode_name, current_mode_cmd = mode_map[mode_str]
                    ad9833.set_mode(current_mode_cmd)
                    print(f"波形已设置为: {current_mode_name}")
                else:
                    print(f"错误: 无效的波形名称 '{mode_str}'。")

            elif choice == 'q':
                break
            else:
                print("错误: 无效的选择。")

    except KeyboardInterrupt:
        print("\n程序被中断。")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if ad9833:
            print("\n正在关闭 AD9833 输出...")
            ad9833.set_mode(AD9833.MODE_BITS_OFF)
        if ch341_dev:
            ch341_dev.close()
            print("CH341 设备已关闭。")

if __name__ == '__main__':
    interactive_mode()
