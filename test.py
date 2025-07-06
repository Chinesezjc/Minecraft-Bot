import win32gui
import win32api
import win32con
import win32process
import time
import ctypes
import sys
import threading
import os
import msvcrt  # 仅用于Windows


# 修复的interruptible_sleep函数
def interruptible_sleep(seconds):
    """
    睡眠指定秒数，但可通过任意键强制唤醒
    
    参数:
        seconds (float): 要睡眠的秒数
    
    返回:
        float: 实际睡眠时间
    """
    # 使用事件控制线程退出
    stop_event = threading.Event()
    wake_event = threading.Event()
    actual_sleep_time = [0.0]
    
    # 定义唤醒线程函数
    def wake_thread():
        try:
            # Windows平台处理
            if sys.platform == "win32":
                start_time = time.time()
                while not stop_event.is_set():
                    # 检查按键
                    if msvcrt.kbhit():
                        msvcrt.getch()  # 读取并丢弃按键
                        wake_event.set()
                        return
                    
                    # 检查是否超时
                    if time.time() - start_time > seconds:
                        return
                    
                    # 短暂休眠减少CPU占用
                    time.sleep(0.05)
            else:
                # Linux/macOS平台处理
                import select
                rlist, _, _ = select.select([sys.stdin], [], [], seconds)
                if rlist:
                    sys.stdin.read(1)  # 读取一个字符
                    wake_event.set()
        except Exception as e:
            print(f"\n唤醒线程异常: {e}")
            wake_event.set()
    
    # 启动唤醒线程
    thread = threading.Thread(target=wake_thread)
    thread.daemon = True
    thread.start()
    
    # 记录开始时间
    start_time = time.time()
    
    # 等待直到超时或被唤醒
    wake_event.wait(seconds)
    
    # 设置停止事件
    stop_event.set()
    
    # 计算实际睡眠时间
    actual_sleep_time[0] = time.time() - start_time
    
    # 清理标准输入缓冲区
    try:
        if sys.platform == "win32":
            while msvcrt.kbhit():
                msvcrt.getch()
        else:
            import termios
            import fcntl
            # 设置非阻塞IO
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            new_settings = termios.tcgetattr(fd)
            new_settings[3] = new_settings[3] & ~termios.ICANON
            termios.tcsetattr(fd, termios.TCSANOW, new_settings)
            old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)
            
            # 清空缓冲区
            while True:
                try:
                    ch = sys.stdin.read(1)
                    if not ch:
                        break
                except:
                    break
            
            # 恢复原始设置
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)
    except Exception as e:
        print(f"清理缓冲区时出错: {e}")
    
    # 返回实际睡眠时间
    return actual_sleep_time[0]


# 定义常量
VK_T = 0x54
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_SHIFT = 0x10


# 提升进程权限以绕过UIPI限制
def enable_ui_access():
    try:
        user32 = ctypes.windll.user32
        MSGFLT_ALLOW = 1
        messages = [
            win32con.WM_KEYDOWN,
            win32con.WM_KEYUP,
            win32con.WM_CHAR,
            win32con.WM_LBUTTONDOWN,
            win32con.WM_LBUTTONUP,
            win32con.WM_MOUSEMOVE,
        ]
        for msg in messages:
            user32.ChangeWindowMessageFilter(msg, MSGFLT_ALLOW)
    except Exception as e:
        print(f"权限提升警告: {e}")


# 定义回调函数，用于处理每个窗口
def enum_windows_callback(hwnd, results):
    if win32gui.IsWindow(hwnd):
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if style & win32con.WS_VISIBLE:
            window_title = win32gui.GetWindowText(hwnd)
            results.append((hwnd, window_title))


def list_all_windows():
    results = []
    win32gui.EnumWindows(enum_windows_callback, results)
    return results


# 线程附加管理
def attach_to_window_thread(hwnd):
    """将当前线程附加到目标窗口的线程"""
    try:
        window_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        current_thread_id = win32api.GetCurrentThreadId()

        if current_thread_id != window_thread_id:
            ctypes.windll.user32.AttachThreadInput(
                current_thread_id, window_thread_id, True
            )
            return True
    except Exception as e:
        print(f"线程附加错误: {e}")
    return False


def detach_from_window_thread(hwnd):
    """从窗口线程分离"""
    try:
        window_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        current_thread_id = win32api.GetCurrentThreadId()

        if current_thread_id != window_thread_id:
            ctypes.windll.user32.AttachThreadInput(
                current_thread_id, window_thread_id, False
            )
    except Exception as e:
        print(f"线程分离错误: {e}")


# 后台输入函数
def send_background_key(hwnd, key_code, is_down=True):
    """后台发送键盘消息"""
    flags = win32con.WM_KEYDOWN if is_down else win32con.WM_KEYUP
    scan_code = win32api.MapVirtualKey(key_code, 0)

    lParam = 0x00000001 | (scan_code << 16)
    if not is_down:
        lParam |= 0xC0000000

    win32api.PostMessage(hwnd, flags, key_code, lParam)


def send_background_char(hwnd, char):
    """后台发送字符消息"""
    char_code = ord(char)
    win32api.PostMessage(hwnd, win32con.WM_CHAR, char_code, 0)


def send_background_mouse(hwnd, down=True):
    """后台发送鼠标点击消息"""
    try:
        # 获取窗口尺寸
        _, _, width, height = win32gui.GetClientRect(hwnd)
        x = width // 2
        y = height // 2

        # 创建坐标值 (x 在低16位，y 在高16位)
        lParam = win32api.MAKELONG(x, y)

        # 发送鼠标消息
        message = win32con.WM_LBUTTONDOWN if down else win32con.WM_LBUTTONUP
        wParam = win32con.MK_LBUTTON if down else 0

        # 附加线程确保消息被正确处理
        attached = attach_to_window_thread(hwnd)
        win32api.PostMessage(hwnd, message, wParam, lParam)
        if attached:
            detach_from_window_thread(hwnd)
    except Exception as e:
        print(f"鼠标操作错误: {e}")


def send_background_mouse_move(hwnd, dx=0, dy=0):
    """后台发送鼠标移动消息"""
    try:
        _, _, width, height = win32gui.GetClientRect(hwnd)
        x = width // 2 + dx
        y = height // 2 + dy

        lParam = win32api.MAKELONG(x, y)

        # 附加线程确保消息被正确处理
        attached = attach_to_window_thread(hwnd)
        win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam)
        if attached:
            detach_from_window_thread(hwnd)
    except Exception as e:
        print(f"鼠标移动错误: {e}")


# 后台命令和操作函数
def background_command(hwnd, cmd: str):
    """后台发送命令"""
    try:
        # 打开聊天框 (T键)
        send_background_key(hwnd, VK_T, True)
        time.sleep(0.1)
        send_background_key(hwnd, VK_T, False)
        time.sleep(0.3)  # 等待聊天框打开

        # 发送命令字符
        for char in cmd:
            send_background_char(hwnd, char)
            time.sleep(0.02)

        # 执行命令 (回车键)
        send_background_key(hwnd, VK_RETURN, True)
        time.sleep(0.05)
        send_background_key(hwnd, VK_RETURN, False)
        time.sleep(0.5)  # 等待命令执行

        return True
    except Exception as e:
        print(f"命令发送错误: {e}")
        return False


def background_long_click(hwnd, duration):
    """后台长按鼠标"""
    try:
        # 按下左键
        send_background_mouse(hwnd, True)

        time.sleep(duration)

        # 释放左键
        send_background_mouse(hwnd, False)
        return True
    except Exception as e:
        print(f"长按操作错误: {e}")
        return False


# 主程序
if __name__ == "__main__":
    # 提升权限
    enable_ui_access()

    # 查找Minecraft窗口
    print("搜索Minecraft窗口...")
    windows = list_all_windows()
    mc_windows = []

    for hwnd, title in windows:
        if "Minecraft" in title:
            print(f"找到Minecraft窗口: HWND={hwnd}, 标题='{title}'")
            mc_windows.append((hwnd, title))

    if not mc_windows:
        print("未找到Minecraft窗口!")
        sys.exit(1)

    # 选择窗口
    print("\n找到的Minecraft窗口:")
    for i, (hwnd, title) in enumerate(mc_windows):
        print(f"[{i}] HWND={hwnd}, 标题='{title}'")

    try:
        selection = int(input("请选择要控制的窗口序号: "))
        if selection < 0 or selection >= len(mc_windows):
            print("无效的选择!")
            sys.exit(1)
    except ValueError:
        print("请输入有效数字!")
        sys.exit(1)

    mc_hwnd, mc_title = mc_windows[selection]
    print(f"已选择窗口: HWND={mc_hwnd}, 标题='{mc_title}'")

    # 测试范围（实际使用时可以调整）
    x_range = range(349, 353)  # X坐标范围
    z_range = range(2399, 2416)  # Z坐标范围

    # 执行自动化
    try:
        for x in x_range:
            for z in z_range:
                print(f"\n传送至坐标 ({x}, {z})...")
                cmd = f"/tp Chinese_Nimazjc_ {x} 66 {z} 0 90"

                # 发送命令
                if not background_command(mc_hwnd, cmd):
                    print("命令发送失败，跳过该坐标")
                    continue

                # 使用修复的睡眠函数
                print(f"等待40秒 (按任意键可跳过)...")
                actual_sleep = interruptible_sleep(40)
                print(f"实际等待时间: {actual_sleep:.1f}秒")
                
                # print("长按鼠标左键中...")
                # if not background_long_click(mc_hwnd, 100):  # 长按10秒
                #     print("长按操作失败")

                time.sleep(1)  # 操作间隔

        print("\n自动化任务完成!")
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"发生错误: {e}")