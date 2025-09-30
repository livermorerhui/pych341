# PyCh341

*注意：本库尚在开发中，API可能频繁变化*

CH341 是一个 USB 总线的转接芯片，通过 USB 总线提供异步串口、打印口、并口以及常用的 2 线和 4 线等同步串行接口。  

本库提供ch341 API的python绑定，底层API由WCH提供，详见[https://www.wch.cn/](https://www.wch.cn/)。

### 注意（20250927）（L）
解压安装后，ch341.py里的 class 名称为 Ch341

### 安装
1. 解压，然后放到项目的文件夹里（20250930）（L）
2. 终端切换到项目文件夹，执行安装（20250930）（L）
```
python setup.py install
```
Ps：安装的方法不止一种，可自行搜索
### 版本依赖
- python 3.9+

### 开发进度

**功能**
- [x] i2c
- [x] spi
- [x] gpio
- [x] 中断回调

**例程**
- [x] mpu6050例程
- [ ] ssd1306例程
- [x] at24cXX例程

**平台支持**
- [x] Windows
- [ ] Linux
