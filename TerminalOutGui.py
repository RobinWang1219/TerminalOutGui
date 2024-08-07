import serial
import threading
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import PhotoImage
from PIL import Image, ImageTk
import configparser
import os
from datetime import datetime

CONFIG_FILE = "settings.ini"

APP_NAME = "TerminalOutGui"
APP_VERSION = "v0.4.4"
BUILD_DATE_TIME = "2024-08-07 18:00:00"  # 手动设置构建日期和时间

AUTHOR_INFO = "HAO-HSIANG, WANG"
APP_HOME_URL = "https://www.example.com"
DONATE_URL = "https://www.paypal.com/ncp/payment/H3RW4JSG8UX68"

MIT_LICENSE = """
Copyright (C) <2024> <HAO-HSIANG, WANG>

Permission is hereby granted, free of charge, to any person 
obtaining a copy of this software and associated documentation 
files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, 
publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be 
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF 
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR 
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN 
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
OR OTHER DEALINGS IN THE SOFTWARE.
"""

APP_WIDTH = 800
APP_HEIGHT = 600

# 默认的常用波特率列表
DEFAULT_COMMON_BAUD_RATES_LIST = [
    9600, 19200, 38400, 57600, 115200, 3000000
]

# 波特率选择
DEFAULT_ALL_BAUD_RATES_LIST = [
    50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800,
    2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200,
    230400, 460800, 500000, 576000, 921600, 1000000,
    1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000
]

DEFAULT_LAST_COM_PORT_NUM = ''
DEFAULT_BUAD_RATE = 115200
DEFAULT_LOG_PATH = 'logs\{COM}_{TIME}.txt'
# 默认的读取延迟时间
DEFAULT_READ_DELAY = 0.001  # 1 毫秒
DEFAULT_SHOW_TIMESTAMP = False

# 全局变量
ser = None
read_thread = None

gConfig = configparser.ConfigParser()
gConfig['Settings'] = {
            'last_com_port': DEFAULT_LAST_COM_PORT_NUM,
            'last_baud_rate': str(DEFAULT_BUAD_RATE),
            'visible_baud_rates_list': ','.join(map(str, DEFAULT_COMMON_BAUD_RATES_LIST)),
            'log_path': DEFAULT_LOG_PATH,
            'read_delay': str(DEFAULT_READ_DELAY),
            'show_timestamp': str(DEFAULT_SHOW_TIMESTAMP)
        }

# 获取可用的COM端口
def get_com_ports():
    from serial.tools import list_ports
    return [port.device for port in list_ports.comports()]

def parse_save_path(path_template, com_port):
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y%m%d_%H%M%S")
    path = path_template.replace("{COM}", com_port).replace("{TIME}", formatted_time)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def decode_data(data):
    try:
        decoded_data = data.decode('utf-8')
    except UnicodeDecodeError:
        try:
            decoded_data = data.decode('latin-1', 'ignore')  # 使用 `latin-1` 解码，并忽略错误
        except UnicodeDecodeError:
            # 对于无法解码的字符，显示它们的十六进制表示
            decoded_data = ''.join(f'\\x{b:02x}' for b in data)
    return decoded_data

def add_timestamp_to_lines(text):
    # 获取当前时间并格式化为时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # 将文本按行分割
    lines = text.splitlines()
    # 为每一行添加时间戳
    lines_with_timestamp = [f"{timestamp} - {line}" for line in lines]
    # 重新组合成一个字符串
    return "\n".join(lines_with_timestamp)

def read_from_port(ser, text_widget, log_path, read_delay):
    save_path = parse_save_path(log_path, ser.port)
    root.title(f"{get_resource_path(save_path)} - {APP_NAME}")
    with open(save_path, 'a', encoding='utf-8') as file:  # 使用'a'模式和utf-8编码
        while ser.is_open:
            try:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    decoded_data = decode_data(data)
                    if show_time_stamp_var.get():
                        decoded_data_with_time = add_timestamp_to_lines(decoded_data)
                        text_widget.insert(tk.END, f"{decoded_data_with_time}\n")
                    else:
                        text_widget.insert(tk.END, f"Received: {decoded_data}\n")
                    text_widget.see(tk.END)
                    
                    if show_time_stamp_var.get():
                        file.write(f"{decoded_data_with_time}")  # 写入解码后的数据
                    else:
                        file.write(decoded_data)
                    
                    file.flush()
                time.sleep(read_delay)  # 自定义延迟时间
            except serial.SerialException as e:
                print(f"SerialException: {e}")
                break

def write_to_port(ser, msg, text_widget):
    try:
        ser.write(msg.encode())
        text_widget.insert(tk.END, f"Sent: {msg}\n")
        text_widget.see(tk.END)
    except serial.SerialException as e:
        print(f"SerialException: {e}")

def start_communication(port, baudrate, text_widget, log_path, read_delay):
    global ser, read_thread
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        text_widget.insert(tk.END, f"Opened {port} at {baudrate} baud rate.\n")

        read_thread = threading.Thread(target=read_from_port, args=(ser, text_widget, log_path, read_delay))
        read_thread.daemon = True
        read_thread.start()
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Failed to open serial port: {str(e)}")
        start_button.config(state=tk.NORMAL)
        menu_bar.entryconfig("Settings", state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        start_button.config(state=tk.NORMAL)
        menu_bar.entryconfig("Settings", state=tk.NORMAL)

def stop_communication():
    global ser, read_thread
    if ser:
        ser.close()
    if read_thread:
        read_thread.join()
    text_widget.insert(tk.END, "Serial communication stopped.\n")
    start_button.config(state=tk.NORMAL)
    menu_bar.entryconfig("Settings", state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def on_start():
    try:
        port = com_port_var.get()
        baudrate = int(baud_rate_var.get())
        log_path = save_path_var.get()
        read_delay = float(read_delay_var.get() or DEFAULT_READ_DELAY)
        if port == "":
            messagebox.showerror("Error", "No COM port selected.")
            return
        if log_path == "":
            messagebox.showerror("Error", "No save path specified.")
            return
        
        # 禁用 Start 和 Settings 按钮以防止重复点击
        start_button.config(state=tk.DISABLED)
        menu_bar.entryconfig("Settings", state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)

        # 保存最新的波特率选择、保存路径和读取延迟
        update_configs()
        
        start_communication(port, baudrate, text_widget, log_path, read_delay)
    except ValueError:
        messagebox.showerror("Error", "Invalid baud rate or read delay.")
        start_button.config(state=tk.NORMAL)
        menu_bar.entryconfig("Settings", state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        start_button.config(state=tk.NORMAL)
        menu_bar.entryconfig("Settings", state=tk.NORMAL)

def send_message():
    msg = input_field.get()
    if msg:
        write_to_port(ser, msg, text_widget)
        input_field.delete(0, tk.END)

def toggle_baud_rates():
    if show_all_baud_var.get():
        baud_rate_combobox['values'] = DEFAULT_ALL_BAUD_RATES_LIST
    else:
        # baud_rate_combobox['values'] = DEFAULT_COMMON_BAUD_RATES_LIST
        baud_rate_combobox['values'] = list(gConfig['Settings']['visible_baud_rates_list'].split(','))
    
    selected_baud_rate = baud_rate_var.get()
    if selected_baud_rate in baud_rate_combobox['values']:
        baud_rate_combobox.set(selected_baud_rate)
    else:
        # baud_rate_combobox.set(DEFAULT_BUAD_RATE)
        baud_rate_combobox.set(gConfig['Settings']['last_baud_rate'])

def open_settings():
    global popup
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.protocol("WM_DELETE_WINDOW", on_close)
    settings_window.resizable(False, False)
    settings_window.overrideredirect(True)

    frame = ttk.Frame(settings_window, padding="10")
    frame.grid(row=0, column=0, sticky="nsew")

    def save_and_close():        
        # 保存设置
        update_configs()
        
        settings_window.destroy()
    
    def close_settings():
        settings_window.destroy()


    # General frame
    general_frame = ttk.LabelFrame(frame, text="General Settings", padding=(5, 5))
    general_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
    
    ttk.Label(general_frame, text="Baud Rate:").grid(row=0, column=0, padx=5, pady=0, sticky="w")
    global baud_rate_combobox
    # baud_rate_combobox = ttk.Combobox(general_frame, textvariable=baud_rate_var, values=DEFAULT_COMMON_BAUD_RATES_LIST, state="readonly", width=27)
    baud_rate_combobox = ttk.Combobox(general_frame, textvariable=baud_rate_var, values=baud_rate_list_var, state="readonly", width=27)
    baud_rate_combobox.grid(row=1, column=0, padx=5, pady=0, sticky="w")

    # 复选框，选项控制显示所有波特率
    global show_all_baud_var
    show_all_baud_var = tk.BooleanVar(value=False)
    show_all_baud_cb = ttk.Checkbutton(general_frame, text="Show all baud rates", variable=show_all_baud_var, command=toggle_baud_rates)
    show_all_baud_cb.grid(row=1, column=1, padx=5, pady=0, sticky="w")

    # Advanced frame
    advanced_frame = ttk.LabelFrame(frame, text="Advanced Settings", padding=(5, 5))
    advanced_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
    
    # 保存路径输入框
    ttk.Label(advanced_frame, text="Save Path:").grid(row=2, column=0, padx=5, pady=0, sticky="w")
    save_path_entry = ttk.Entry(advanced_frame, textvariable=save_path_var, width=30)
    save_path_entry.grid(row=3, column=0, padx=5, pady=0, sticky="w")

    # 延迟时间输入框
    ttk.Label(advanced_frame, text="Read Delay (seconds):").grid(row=2, column=1, padx=5, pady=0, sticky="w")
    read_delay_entry = ttk.Entry(advanced_frame, textvariable=read_delay_var, width=10)
    read_delay_entry.grid(row=3, column=1, padx=5, pady=0, sticky="w")

    # 复选框，选项控制Log显示TimeStamp
    global show_time_stamp_var
    show_timestamp_cb = ttk.Checkbutton(advanced_frame, text="Show TimeStamp", variable=show_time_stamp_var)
    show_timestamp_cb.grid(row=4, column=0, padx=5, pady=5, sticky="w")

    # 保存并关闭按钮
    save_button = ttk.Button(frame, text="Save & Close", command=save_and_close)
    save_button.grid(row=6, column=0, padx=5, pady=10, sticky="ew")
    
    # 关闭按钮
    close_button = ttk.Button(frame, text="Close", command=close_settings)
    close_button.grid(row=6, column=1, padx=5, pady=10, sticky="ew")

    center_window(settings_window)  # 中心定位在这里初始化完成后
    popup = settings_window

def open_url(url):
    import webbrowser
    webbrowser.open_new(url)

def about_app():
    global popup
    about_window = tk.Toplevel(root)
    about_window.title("About TerminalOutGui")
    about_window.protocol("WM_DELETE_WINDOW", on_close)
    about_window.resizable(False, False)  # 锁定窗口大小
    about_window.overrideredirect(True)  # 移除窗口装饰

    frame = ttk.Frame(about_window, padding="10")
    frame.grid(row=0, column=0, sticky="nsew")
    
    # 加載圖片並調整大小
    original_image = Image.open(get_resource_path('app_icon.png'))
    resized_image = original_image.resize((80, 80))  # 調整圖片大小至80x80像素
    icon = ImageTk.PhotoImage(resized_image)
    
    # 創建 ttk.Label 小部件並顯示圖片
    label = ttk.Label(frame, image=icon)
    label.grid(row=0, column=0, rowspan=3, columnspan=1, padx=15, pady=0, sticky="w")
    
    # 保持對圖片的引用，防止被垃圾回收
    label.image = icon
    
    appInfoPadX = 110
    appInfoPadY = 0
    appInfo = ttk.Label(frame, text=f"{APP_NAME} {APP_VERSION}")
    appInfo.grid(row=0, column=0, columnspan=1, padx=appInfoPadX, pady=appInfoPadY, sticky="w")
    appInfo = ttk.Label(frame, text=f"Build time: {BUILD_DATE_TIME}")
    appInfo.grid(row=1, column=0, columnspan=1, padx=appInfoPadX, pady=appInfoPadY, sticky="w")
    appInfo = ttk.Label(frame, text=f"Author: {AUTHOR_INFO}")
    appInfo.grid(row=2, column=0, columnspan=1, padx=appInfoPadX, pady=appInfoPadY, sticky="w")
    
    appWebSite = tk.Label(frame, text=f"Home: ")
    appWebSite.grid(row=3, column=0, columnspan=1, padx=10, pady=5, sticky="w")
    appWebSite = tk.Label(frame, text=f"{APP_HOME_URL}", fg="blue", cursor="hand2")
    appWebSite.grid(row=3, column=0, columnspan=1, padx=50, pady=5, sticky="w")
    appWebSite.bind("<Button-1>", lambda e: open_url(APP_HOME_URL))  # 绑定鼠标点击事件

    # License frame
    license_frame = ttk.LabelFrame(frame, text="MIT Gereral Public License", padding=(10, 5))
    license_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
    ttk.Label(license_frame, text=f"{MIT_LICENSE}", justify="left").pack()

    button_frame = ttk.Frame(frame)
    button_frame.grid(row=5, column=0, columnspan=2, pady=10)
    
    # Donate 和 OK 按钮并排居中
    donate_button = ttk.Button(button_frame, text="Donate", command=lambda: open_url(DONATE_URL))
    donate_button.pack(side=tk.LEFT, padx=5)
    
    ok_button = ttk.Button(button_frame, text="OK", command=about_window.destroy)
    ok_button.pack(side=tk.RIGHT, padx=5)

    center_window(about_window)  # 中心定位在这里初始化完成后
    popup = about_window

def center_window(window):
    window.update_idletasks()
    x = (root.winfo_x() + (root.winfo_width() // 2)) - (window.winfo_reqwidth() // 2)
    y = (root.winfo_y() + (root.winfo_height() // 2)) - (window.winfo_reqheight() // 2)
    window.geometry(f"+{x}+{y}")

def sync_configs(source,target):
    for section in source.sections():
        if not target.has_section(section):
            target.add_section(section)
        for key, value in source.items(section):
            target.set(section, key, value)

def load_configs():
    global gConfig
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        sync_configs(config,gConfig)
        # gConfig = config
    return gConfig

def update_configs():
    global gConfig
    
    gConfig['Settings']['last_com_port']    = last_com_port
    gConfig['Settings']['last_baud_rate']   = str(baud_rate_var.get())
    # gConfig['Settings']['visible_baud_rates_list']    # manual update by user
    gConfig['Settings']['log_path']         = save_path_var.get()
    gConfig['Settings']['read_delay']       = str(read_delay_var.get())
    gConfig['Settings']['show_timestamp']   = str(show_time_stamp_var.get())
    
    with open(CONFIG_FILE, 'w') as configfile:
        gConfig.write(configfile)

def get_resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def on_window_minimize(event):
    if popup and popup.winfo_exists():
        popup.withdraw()  # 隐藏弹出窗口

def on_window_restore(event):
    if popup and popup.winfo_exists():
        popup.deiconify()  # 恢复弹出窗口显示

def on_close():
    if popup and popup.winfo_exists():
        popup.destroy()
    
def on_popup_focus(event):
    if popup and popup.winfo_exists():
        popup.deiconify()

# 创建主窗口
root = tk.Tk()
root.title(f"{APP_NAME}")
# 使用 PhotoImage 加載 PNG 文件
icon = tk.PhotoImage(file=get_resource_path('app_icon.png'))
root.iconphoto(True, icon) # 设定窗口图标
center_x = int(root.winfo_screenwidth() / 2 - APP_WIDTH / 2)
center_y = int(root.winfo_screenheight() / 2 - APP_HEIGHT / 2)
root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{center_x}+{center_y}")  # 设置默认窗口大小

# 初始化配置文件
# create_default_config()

# 全局变量
baud_rate_var = tk.StringVar()
save_path_var = tk.StringVar()
read_delay_var = tk.StringVar()
show_time_stamp_var = tk.BooleanVar()

config = load_configs()
baud_rate_var.set(config.get('Settings', 'last_baud_rate', fallback=str(DEFAULT_BUAD_RATE)))
save_path_var.set(config.get('Settings', 'log_path', fallback=DEFAULT_LOG_PATH))
read_delay_var.set(config.get('Settings', 'read_delay', fallback=str(DEFAULT_READ_DELAY)))
show_time_stamp_var.set(config.get('Settings', 'show_timestamp', fallback=str(DEFAULT_SHOW_TIMESTAMP)))
baud_rate_list_var = list(map(int, config.get('Settings', 'visible_baud_rates_list', fallback=DEFAULT_COMMON_BAUD_RATES_LIST).split(',')))


# 菜单栏
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

menu_bar.add_command(label="Settings", command=open_settings)
menu_bar.add_command(label="?", command=about_app)

# COM端口选择
ttk.Label(root, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
com_port_var = tk.StringVar()
com_ports = get_com_ports()
last_com_port = config.get('Settings', 'last_com_port', fallback="")

if com_ports:
    com_port_combobox = ttk.Combobox(root, textvariable=com_port_var, values=com_ports, state="readonly")
    com_port_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    if last_com_port in com_ports:
        com_port_combobox.set(last_com_port)
    else:
        com_port_combobox.current(0)
else:
    com_port_combobox = ttk.Combobox(root, textvariable=com_port_var, values=["No COM Ports Available"], state="readonly")
    com_port_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    com_port_combobox.current(0)
    com_port_combobox.config(state="disabled")

# 按钮区域
start_button = ttk.Button(root, text="Start", command=on_start)
start_button.grid(row=0, column=2, padx=5, pady=5)

stop_button = ttk.Button(root, text="Stop", command=stop_communication)
stop_button.grid(row=0, column=3, padx=5, pady=5)
stop_button.config(state=tk.DISABLED)  # 默认禁用，启动后启用

# 消息输出区域
text_widget = tk.Text(root, height=15, width=50, wrap="none")
text_widget.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

# 设置滚动条
x_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=text_widget.xview)
y_scroll = tk.Scrollbar(root, orient=tk.VERTICAL, command=text_widget.yview)
text_widget.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
x_scroll.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
y_scroll.grid(row=1, column=4, padx=5, pady=5, sticky="ns")

# 输入框
input_field = ttk.Entry(root)
input_field.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

# 发送按钮
send_button = ttk.Button(root, text="Send", command=send_message)
send_button.grid(row=3, column=3, padx=5, pady=5, sticky="ew")

# 使窗口自适应调整
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

popup = None

# binding events
root.bind("<FocusIn>", on_popup_focus)      # focus event
root.bind("<Unmap>", on_window_minimize)    # minimum event
root.bind("<Map>", on_window_restore)       # restore event

root.mainloop()
