import os
import json
import requests
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Listbox

# 配置
MINECRAFT_DIR = Path.home() / '.minecraft'
VERSION_MANIFEST_URL = 'https://bmclapi2.bangbang93.com/mc/game/version_manifest.json'
LOG_FILE = 'error_log.txt'

# 函数：记录错误到日志文件
def log_error(message):
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{message}\n")

# 函数：创建 Minecraft 目录
def ensure_minecraft_dir():
    if not MINECRAFT_DIR.exists():
        MINECRAFT_DIR.mkdir(parents=True)

# 函数：获取 Minecraft 版本列表
def fetch_versions():
    try:
        response = requests.get(VERSION_MANIFEST_URL, verify=False)
        response.raise_for_status()
        data = response.json()
        return {version['id']: version['url'] for version in data['versions']}
    except requests.RequestException as e:
        log_error(f"获取版本列表时出错: {e}")
        show_popup("错误", "无法获取版本列表。请检查您的网络连接或 API 服务。")
        raise

# 函数：获取 Minecraft 版本的下载 URL
def fetch_download_url(version_id, version_url):
    try:
        response = requests.get(version_url, verify=False)
        response.raise_for_status()
        data = response.json()
        client_info = data['downloads'].get('client')
        if not client_info:
            raise ValueError("未找到客户端下载信息")
        return client_info['url']
    except requests.RequestException as e:
        log_error(f"获取下载地址时出错: {e}")
        show_popup("错误", "无法获取下载地址。请检查 API 服务。")
        raise

# 函数：显示弹窗
def show_popup(title, message):
    messagebox.showinfo(title, message)

# 函数：下载并保存 Minecraft 客户端
def download_client(download_url, output_dir):
    try:
        response = requests.get(download_url, stream=True, verify=False)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        chunk_size = 1024
        num_chunks = total_size // chunk_size + 1

        jar_path = output_dir / 'client.jar'
        
        # 创建进度窗口
        progress_popup = tk.Toplevel()
        progress_popup.title("下载中")
        progress_popup.geometry("400x150")
        progress_popup.wm_attributes("-topmost", True)  # 设置窗口置顶

        # 添加标签显示下载状态
        label = tk.Label(progress_popup, text="正在下载 Minecraft 客户端...")
        label.pack(pady=10)

        # 创建进度条
        progress_bar = ttk.Progressbar(progress_popup, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=10)

        # 创建标签显示百分比
        percent_label = tk.Label(progress_popup, text="0%")
        percent_label.pack()

        progress_popup.update_idletasks()

        downloaded_size = 0

        with open(jar_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    percent_complete = (downloaded_size / total_size) * 100
                    progress_bar['value'] = percent_complete
                    percent_label.config(text=f"{percent_complete:.2f}%")
                    progress_popup.update_idletasks()

        progress_popup.destroy()
        show_popup("完成", f"客户端版本下载成功，保存在 {jar_path}")

    except requests.RequestException as e:
        log_error(f"下载客户端时出错: {e}")
        show_popup("错误", "无法下载客户端。请检查 API 服务。")
        raise
    except IOError as e:
        log_error(f"保存 jar 文件时出错: {e}")
        show_popup("错误", "保存 jar 文件失败。")
        raise
    except Exception as e:
        log_error(f"下载或保存客户端时发生未处理的错误: {e}")
        show_popup("错误", "下载或保存客户端时发生错误。")
        raise

# 函数：创建并显示版本选择窗口
def show_versions_window(versions):
    root = tk.Tk()
    root.title("Minecraft 版本选择器")

    # 获取 CMD 窗口大小
    root.update_idletasks()
    width = root.winfo_screenwidth() // 4
    height = root.winfo_screenheight() // 4
    root.geometry(f"{width}x{height}")

    listbox = Listbox(root, selectmode=tk.SINGLE, font=("Courier", 10))
    for version in versions.keys():
        listbox.insert(tk.END, version)
    listbox.pack(expand=True, fill=tk.BOTH)

    selected_version = tk.StringVar()
    
    def on_button_click():
        selection = listbox.curselection()
        if selection:
            selected_version.set(listbox.get(selection[0]))
        else:
            show_popup("错误", "没有选择版本。")
        root.destroy()

    button = tk.Button(root, text="确认", command=on_button_click)
    button.pack(pady=10)
    
    root.mainloop()
    return selected_version.get()

# 主函数：启动器逻辑
def main():
    try:
        ensure_minecraft_dir()
        
        # 获取并显示可用版本
        versions = fetch_versions()
        
        # 在窗口中选择版本
        selected_version = show_versions_window(versions)
        
        if not selected_version:
            show_popup("提示", "未选择版本，程序退出。")
            return
        
        # 获取版本的下载 URL
        version_url = versions[selected_version]
        download_url = fetch_download_url(selected_version, version_url)
        
        # 选择保存位置
        save_location = filedialog.askdirectory(title="选择保存位置", initialdir=str(MINECRAFT_DIR))
        if not save_location:
            show_popup("提示", "未选择保存位置，程序退出。")
            return
        
        # 下载并保存客户端
        output_dir = Path(save_location) / 'versions' / selected_version
        output_dir.mkdir(parents=True, exist_ok=True)
        download_client(download_url, output_dir)
        
        show_popup("完成", "Minecraft 客户端下载已完成。")
    
    except Exception as e:
        log_error(f"启动器运行时发生错误: {e}")
        show_popup("错误", "启动器运行时发生错误。")

if __name__ == "__main__":
    main()
