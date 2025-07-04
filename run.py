import os
from mcgui import *


def find_mc():
    # 查找Minecraft窗口
    print("搜索Minecraft窗口...")
    windows = list_all_windows()
    mc_windows = []

    for hwnd, title in windows:
        if "Minecraft*" in title:
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
    return mc_windows[selection]


# def load_log(log_file):
#     used = []


# 主程序
if __name__ == "__main__":
    # 提升权限
    enable_ui_access()

    mc_hwnd, mc_title = find_mc()
    print(f"已选择窗口: HWND={mc_hwnd}, 标题='{mc_title}'")

    pickaxeman = "Chinese_Pikaync_"

    # 测试范围（实际使用时可以调整）
    dx_range = range(336, 352)  # X坐标范围
    dz_range = range(2655, 2671)  # Z坐标范围

    x_range = range(335, 353)  # X坐标范围
    z_range = range(2654, 2672)  # Z坐标范围

    # log_dir = "log"
    # os.makedirs(log_dir, exist_ok=True)
    # log_file = os.path.join(log_dir, f"log.txt")
    # with open(log_file, "r") as f:
    #     pass

    # 执行自动化
    try:
        for x in x_range:
            for z in z_range:
                if x in dx_range and z in dz_range:
                    continue
                print(f"\n传送至坐标 ({x}, {z})...")
                cmd = f"/tp {pickaxeman} {x} 66 {z} 0 90"

                # 发送命令
                if not background_command(mc_hwnd, cmd):
                    print("命令发送失败，跳过该坐标")
                    continue

                interruptible_sleep(100)
                # print("长按鼠标左键中...")
                # if not background_long_click(mc_hwnd, 100):  # 长按10秒
                #     print("长按操作失败")

                time.sleep(1)  # 操作间隔

        print("\n自动化任务完成!")
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"发生错误: {e}")
