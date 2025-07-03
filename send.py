import win32gui
import win32api
import win32con
import winsound
import time
import math


# 定义回调函数，用于处理每个窗口
def enum_windows_callback(hwnd, results):
    if win32gui.IsWindow(hwnd):  # 确保是有效窗口
        # 获取窗口样式，检查是否可见
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if style & win32con.WS_VISIBLE:  # 检查窗口样式是否包含可见标志
            window_title = win32gui.GetWindowText(hwnd)  # 获取窗口标题
            results.append((hwnd, window_title))  # 添加到结果列表


def list_all_windows():
    results = []
    win32gui.EnumWindows(enum_windows_callback, results)  # 遍历所有窗口
    return results


found = False
mc = None
L = []
if __name__ == "__main__":
    windows = list_all_windows()
    for hwnd, title in windows:
        print(f"HWND: {hwnd}, Title: '{title}'")
        if "Minecraft" in title:
            L.append([hwnd, title])
            found = True


def clickdown(button: int):
    print("clickdown: %s" % button)
    win32api.PostMessage(
        mc,
        win32con.WM_KEYDOWN,
        button,
        0x00000001 | win32api.MapVirtualKey(button, 0) << 16,
    )


def clickup(button: int):
    print("clickup: %s" % button)
    win32api.PostMessage(
        mc,
        win32con.WM_KEYUP,
        button,
        0xC0000001 | win32api.MapVirtualKey(button, 0) << 16,
    )


def send_char(char: str):
    """直接发送字符消息"""
    char_code = ord(char)
    win32api.PostMessage(mc, win32con.WM_CHAR, char_code, 0)


def click(str: str):
    print("click: %s" % str)
    if isinstance(str, int):
        clickdown(str)
        time.sleep(0.1)
        clickup(str)
        return
    for i in str:
        clickdown(ord(i))
        time.sleep(0.1)
        clickup(ord(i))


def mousemove(x: int, y: int):
    lx, ly, rx, ry = win32gui.GetClientRect(mc)
    print(lx, ly, rx, ry)
    x = (rx - lx + 1) // 2
    y = (ry - ly + 1) // 2
    print("mousemove: (%d, %d)" % (x, y))
    win32api.PostMessage(mc, win32con.WM_MOUSEMOVE, 0, y << 16 | x)


def leftclickdown():
    _, _, width, height = win32gui.GetClientRect(mc)
    x = width // 2
    y = height // 2
    print("leftclickdown: (%d, %d)" % (x, y))

    # 正确的参数格式：
    # wParam: 按键状态 (通常为0)
    # lParam: 坐标 (x 在低16位，y 在高16位)
    lParam = win32api.MAKELONG(x, y)
    win32api.PostMessage(mc, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)


def leftclickup():
    _, _, width, height = win32gui.GetClientRect(mc)
    x = width // 2
    y = height // 2
    print("leftclickup: (%d, %d)" % (x, y))

    lParam = win32api.MAKELONG(x, y)
    win32api.PostMessage(mc, win32con.WM_LBUTTONUP, 0, lParam)


# 在 command 函数中使用
def command(cmd: str):
    click("T")
    time.sleep(0.1)  # 等待聊天框打开

    for char in cmd:
        send_char(char)

    click(win32con.VK_RETURN)


if found:
    print("founded")
    for i in range(len(L)):
        print(f"tid {i} | HWND {L[i][0]} | Title {L[i][1]}")
    tid = int(input("Choose your minecraft tid:"))
    assert 0 <= tid < len(L), "tid didn't in range"
    mc = L[tid][0]
    for x in range(336, 352):
        for z in range(2400, 2415):
            command("/tp @p %d 66 %d 0 90" % (x, z))
            time.sleep(1)
            leftclickdown()
            leftclickup()
            leftclickdown()
            time.sleep(100)
            leftclickup()
            time.sleep(1)
    # # 模拟按下 W 键
    # # click(191)
    # # click("WARP GARDEN")
    # # click(win32con.VK_RETURN)
    # # time.sleep(5)
    # click("1")
    # time.sleep(5)
    # clickdown(ord("W"))
    # leftclickdown()
    # for i in range(7):
    #     clickdown(ord("A"))
    #     time.sleep(97.5)
    #     clickup(ord("A"))
    #     time.sleep(1.2)
    #     clickdown(ord("D"))
    #     time.sleep(97.5)
    #     clickup(ord("D"))
    #     time.sleep(1.2)
    # clickdown(ord("A"))
    # time.sleep(97.5)
    # clickup(ord("A"))
    # leftclickup()
    # clickup(ord("W"))
    # for i in range(60):
    #     winsound.Beep(int(math.pow(2, i / 12) * 60), 250)
else:
    print("窗口未找到！")
