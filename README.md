# 剪贴板二维码识别工具

读取剪贴板里的二维码图片，识别出其中的链接，并自动用 Chrome 打开。

支持：截图（`Win+Shift+S`）、复制图片、复制图片文件、文本链接等多种剪贴板内容。

## 功能

- 读取剪贴板第一个内容（图片位图 / 图片文件 / 文本链接）
- 识别其中的二维码，得到地址
- 自动用 Chrome 打开链接（找不到 Chrome 时回退默认浏览器）
- 识别失败弹窗提示，成功时无任何窗口
- 打包成单个 exe，换电脑零配置，双击即用

## 快速使用（exe 版）

1. 复制二维码：按 `Win+Shift+S` 框选截图，或在图片上右键 → 复制图片
2. 双击 `qr_scanner.exe`
3. Chrome 自动打开识别出的链接

> 识别失败会弹出「二维码识别」提示框；成功时直接打开 Chrome，不显示任何窗口。

## 使用（脚本版）

需要 Python 3.8+ 和以下依赖：

```bash
pip install opencv-python pillow pywin32
```

国内网络可加清华镜像：

```bash
pip install opencv-python pillow pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

用法：

```bash
python qr.py              # 读剪贴板识别
python qr.py 图片路径      # 指定图片文件
python qr.py --open       # 识别后用 Chrome 打开
python qr.py --debug      # 排查剪贴板内容
```

也可以直接把图片文件拖到 `scan_qr.bat` 上。

## 打包成 exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name qr_scanner qr.py
```

产物在 `dist/qr_scanner.exe`。

## 换电脑

- **exe 版**：直接拷贝 `qr_scanner.exe`，目标电脑只需 Windows 64 位（最好装 Chrome）。
- **脚本版**：装 Python + 上面三个依赖。

## 依赖说明

| 依赖 | 作用 |
|------|------|
| opencv-python | 二维码识别（`cv2.QRCodeDetector`） |
| pillow | 读取剪贴板图片 |
| pywin32 | Windows 剪贴板读取 |

## 目录结构

```
qr-scanner/
├── qr_scanner.exe   打包后的可执行文件（不提交，见 .gitignore）
├── qr.py            主程序源码
├── scan_qr.bat      脚本版双击入口
├── .gitignore
└── README.md        本文件
```
