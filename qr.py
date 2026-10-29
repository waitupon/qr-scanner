#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板二维码识别工具
====================
读取剪贴板里的第一个内容（图片 / 图片文件 / 文本链接），识别其中的二维码，
打印出二维码指向的地址。

用法:
    python qr.py                 # 读剪贴板
    python qr.py 图片路径         # 直接指定图片文件
    python qr.py --open          # 识别到链接后用 Chrome 打开
    python qr.py --debug         # 打印剪贴板内容信息（排查用）
    或直接把图片文件拖到 scan_qr.bat 上

打包成 exe（--noconsole）时：双击直接识别剪贴板并用 Chrome 打开，
失败时弹消息框提示，无黑窗口。

依赖: opencv-python, pillow, pywin32
"""

import ctypes
import os
import subprocess
import sys
import webbrowser

import cv2
import numpy as np
from PIL import Image, ImageGrab

FROZEN = getattr(sys, "frozen", False)  # 是否为 PyInstaller 打包的 exe


def _console():
    return sys.stdout is not None


def emit(msg):
    """信息输出：有控制台就打印，无控制台(exe)静默。"""
    if _console():
        try:
            print(msg)
        except Exception:
            pass


def alert(msg):
    """提示：有控制台打印，无控制台(exe)弹消息框。"""
    if _console():
        try:
            print(msg)
        except Exception:
            pass
    else:
        try:
            ctypes.windll.user32.MessageBoxW(0, str(msg), "二维码识别", 0x30)
        except Exception:
            pass


# 统一控制台 UTF-8（仅控制台模式）
if _console() and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def pil_to_bgr(img):
    if img.mode not in ("RGB", "RGBA"):
        target = "RGBA" if img.mode in ("LA", "PA") else "RGB"
        try:
            img = img.convert(target)
        except Exception:
            img = img.convert("RGB")
    arr = np.asarray(img)
    if arr.ndim == 2:
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    if arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def decode_qr(bgr):
    """识别图片中的二维码，返回解码文本；失败返回 None。"""
    if bgr is None or bgr.size == 0:
        return None
    d = cv2.QRCodeDetector()
    for scale in (1, 2, 3):
        img = bgr if scale == 1 else cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        data, _, _ = d.detectAndDecode(img)
        if data:
            return data.strip()
    try:
        ok, decoded, _, _ = d.detectAndDecodeMulti(bgr)
        if ok and decoded:
            return str(decoded[0]).strip()
    except Exception:
        pass
    return None


def decode_file(path):
    if not os.path.isfile(path):
        return None
    bgr = cv2.imread(path)
    return decode_qr(bgr)


def open_in_chrome(url):
    """用 Chrome 打开链接。成功返回 True。"""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                subprocess.Popen([p, url])
                return True
            except Exception:
                pass
    return False


def read_clipboard(debug=False):
    """读取剪贴板。返回 (kind, payload)。
    kind: 'image' 图片 | 'file' 文件路径(第一个) | 'text' 文本 | 'none' 空
    """
    # 1) PIL：图片位图 / 文件列表
    item = None
    try:
        item = ImageGrab.grabclipboard()
    except Exception as e:
        if debug:
            emit(f"[debug] grabclipboard 异常: {e}")
    if isinstance(item, Image.Image):
        if debug:
            emit(f"[debug] PIL 读到图片: mode={item.mode} size={item.size}")
        return "image", item
    if isinstance(item, (list, tuple)) and item:
        if debug:
            emit(f"[debug] PIL 读到文件列表: {item}")
        return "file", str(item[0])

    # 2) win32clipboard：文件列表 / 文本（PIL 读不到的格式）
    try:
        import win32clipboard
        import win32con
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                if files:
                    if debug:
                        emit(f"[debug] win32 读到文件列表: {files}")
                    return "file", str(files[0])
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                if text and str(text).strip():
                    if debug:
                        emit(f"[debug] win32 读到文本: {str(text)[:200]}")
                    return "text", str(text).strip()
            if debug:
                fmt = 0
                names = []
                while True:
                    fmt = win32clipboard.EnumClipboardFormats(fmt)
                    if fmt == 0:
                        break
                    names.append(str(fmt))
                emit(f"[debug] 剪贴板可用格式编号: {names}")
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        if debug:
            emit(f"[debug] win32clipboard 异常: {e}")

    return "none", None


def extract_address(text):
    """从文本里提取地址：文件路径→读图；qrserver 链接→解 data 参数；否则当地址返回。"""
    t = text.strip().strip('"').strip()
    if not t:
        return None
    if os.path.isfile(t):
        return decode_file(t)
    if "data=" in t:
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            qs = parse_qs(urlparse(t).query)
            if qs.get("data"):
                return unquote(qs["data"][0])
        except Exception:
            pass
    return t


def main():
    debug = "--debug" in sys.argv and _console()
    open_url = "--open" in sys.argv or FROZEN
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    data = None
    if args:
        data = decode_file(args[0])
        if not data:
            alert(f"[错误] 无法从文件识别二维码: {args[0]}")
            return 1
    else:
        kind, payload = read_clipboard(debug)
        if kind == "none":
            alert(
                "[错误] 剪贴板里没有可用的图片。\n\n"
                "请先做下面任一步，再运行：\n"
                "  1. 按 Win+Shift+S 框选二维码截图\n"
                "  2. 或在图片上右键 → 复制图片\n"
                "  3. 或直接把图片文件拖到本程序上"
            )
            return 1
        if kind == "image":
            data = decode_qr(pil_to_bgr(payload))
        elif kind == "file":
            data = decode_file(payload)
        else:  # text
            data = extract_address(payload)
        if not data:
            alert("[错误] 剪贴板里的内容未识别到二维码。")
            return 1

    emit("识别结果:")
    emit(data)
    if open_url and data.lower().startswith(("http://", "https://")):
        if open_in_chrome(data):
            emit("(已在 Chrome 打开)")
        else:
            try:
                webbrowser.open(data)
                emit("(已在默认浏览器打开)")
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
