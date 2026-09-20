#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统软件清理工具 - 图形界面版本
基于 tkinter，无需额外依赖
"""

import os
import sys
import json
import subprocess
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from typing import Set
import tkinter as tk
from tkinter import (
    ttk, messagebox, filedialog, scrolledtext,
    Listbox, Checkbutton, Menu
)

# 导入核心模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app_cleaner import (
    AppCleaner,
    ScanResult,
    InstalledApp,
    AppDataFolder,
    require_admin,
    elevate_privileges,
    setup_logging,
)

# ============ 主题颜色 ============
COLORS = {
    'bg_dark': '#1e1e2e',
    'bg_medium': '#282838',
    'bg_light': '#32324a',
    'fg_primary': '#cdd6f4',
    'fg_secondary': '#a6adc8',
    'accent': '#89b4fa',
    'accent_hover': '#74c7ec',
    'success': '#a6e3a1',
    'warning': '#fab387',
    'danger': '#f38ba8',
    'border': '#45475a',
    'row_odd': '#252538',
    'row_even': '#1e1e2e',
}

# ============ 自定义 Treeview 样式 ============
class TreeviewStyle:
    """自定义 Treeview 样式"""
    @staticmethod
    def setup(style):
        style.configure(
            'Custom.Treeview',
            background=COLORS['bg_dark'],
            foreground=COLORS['fg_primary'],
            fieldbackground=COLORS['bg_dark'],
            rowheight=28,
            font=('Segoe UI', 10),
            borderwidth=0,
        )
        style.configure(
            'Custom.Treeview.Heading',
            background=COLORS['bg_medium'],
            foreground=COLORS['accent'],
            font=('Segoe UI', 10, 'bold'),
            borderwidth=0,
            relief='flat',
        )
        style.map(
            'Custom.Treeview',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', COLORS['bg_dark'])],
        )

# ============ 主窗口 ============
class AppCleanerGUI:
    """图形界面主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("系统软件清理工具 v1.0")
        self.root.geometry("1200x780")
        self.root.minsize(1000, 650)
        self.root.configure(bg=COLORS['bg_dark'])

        # 状态
        self.cleaner = None
        self.scan_result = None
        self.scanning = False
        self.cleaning = False
        self.selected_orphan_indices: Set[int] = set()  # 选中的孤儿索引

        # 构建界面
        self._setup_style()
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()

        # 应用主题
        self._apply_theme()

    def _apply_theme(self):
        """应用主题颜色"""
        self.root.configure(bg=COLORS['bg_dark'])
        for widget in [self.root, self.root.nametowidget(self.root.winfo_children()[0])]:
            try:
                widget.configure(bg=COLORS['bg_dark'])
            except:
                pass

    def _setup_style(self):
        """设置所有控件样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        TreeviewStyle.setup(self.style)

        # 按钮样式
        self.style.configure('Accent.TButton',
                             background=COLORS['accent'],
                             foreground=COLORS['bg_dark'],
                             font=('Segoe UI', 10, 'bold'),
                             padding=8)
        self.style.configure('Danger.TButton',
                             background=COLORS['danger'],
                             foreground=COLORS['bg_dark'],
                             font=('Segoe UI', 10, 'bold'),
                             padding=8)
        self.style.configure('Success.TButton',
                             background=COLORS['success'],
                             foreground=COLORS['bg_dark'],
                             font=('Segoe UI', 10, 'bold'),
                             padding=8)
        self.style.configure('Status.TLabel',
                             background=COLORS['bg_medium'],
                             foreground=COLORS['fg_primary'],
                             font=('Segoe UI', 9))
        self.style.configure('Title.TLabel',
                             background=COLORS['bg_dark'],
                             foreground=COLORS['accent'],
                             font=('Segoe UI', 14, 'bold'))

    def _create_menu(self):
        """创建菜单栏"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出报告", command=self._export_report)
        file_menu.add_command(label="导入报告", command=self._import_report)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 工具菜单
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="打开PowerShell", command=self._open_powershell)
        tools_menu.add_command(label="打开CMD", command=self._open_cmd)

        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=8, pady=6)

        # 扫描按钮
        self.btn_scan = ttk.Button(toolbar, text="🔍 扫描", command=self._start_scan)
        self.btn_scan.pack(side='left', padx=(0, 6))

        # 清理按钮
        self.btn_clean = ttk.Button(
            toolbar, text="🗑️ 清理", command=self._start_clean, state='disabled')
        self.btn_clean.pack(side='left', padx=(0, 6))

        # 刷新按钮
        ttk.Button(toolbar, text="↻ 刷新", command=self._start_scan).pack(side='left', padx=(0, 6))

        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10, pady=4)

        # 路径设置
        ttk.Label(toolbar, text="自定义安装路径:").pack(side='left', padx=(10, 4))
        self.entry_install_path = ttk.Entry(toolbar, width=30)
        self.entry_install_path.pack(side='left', padx=(0, 6))
        self.entry_install_path.insert(0, "D:\\Programs")

        ttk.Button(toolbar, text="+", width=3, command=self._add_install_path).pack(side='left', padx=(0, 10))

        ttk.Label(toolbar, text="自定义数据路径:").pack(side='left', padx=(0, 4))
        self.entry_appdata_path = ttk.Entry(toolbar, width=30)
        self.entry_appdata_path.pack(side='left', padx=(0, 6))
        self.entry_appdata_path.insert(0, "D:\\AppData")

        ttk.Button(toolbar, text="+", width=3, command=self._add_appdata_path).pack(side='left', padx=(0, 10))

        # 右侧选项
        self.var_dry_run = tk.BooleanVar(value=False)
        tk.Checkbutton(
            toolbar, text="演习模式", variable=self.var_dry_run,
            bg=COLORS['bg_dark'], fg=COLORS['fg_secondary'],
            selectcolor=COLORS['bg_medium'], activebackground=COLORS['bg_dark'],
        ).pack(side='right', padx=(0, 6))

        self.var_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(
            toolbar, text="回收站", variable=self.var_recycle,
            bg=COLORS['bg_dark'], fg=COLORS['fg_secondary'],
            selectcolor=COLORS['bg_medium'], activebackground=COLORS['bg_dark'],
        ).pack(side='right', padx=(0, 6))

        self.var_admin = tk.BooleanVar(value=False)
        tk.Checkbutton(
            toolbar, text="管理员权限", variable=self.var_admin,
            bg=COLORS['bg_dark'], fg=COLORS['fg_secondary'],
            selectcolor=COLORS['bg_medium'], activebackground=COLORS['bg_dark'],
        ).pack(side='right', padx=(0, 6))

        # 扫描进度条
        self.progress = ttk.Progressbar(toolbar, length=150, mode='indeterminate')
        self.progress.pack(side='right', padx=(10, 0))

    def _create_main_area(self):
        """创建主内容区域"""
        # 分隔面板
        paned = ttk.PanedWindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=8, pady=(0, 6))

        # ---- 左面板：已安装软件 ----
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="已安装软件", font=('Segoe UI', 11, 'bold'),
                  background=COLORS['bg_dark'], foreground=COLORS['accent']).pack(anchor='w', padx=4, pady=(6, 2))

        # 软件列表
        cols = ('name', 'version', 'publisher', 'size_mb', 'source')
        self.tree_apps = ttk.Treeview(left_frame, columns=cols, show='headings', style='Custom.Treeview')
        self.tree_apps.heading('name', text='名称', anchor='w')
        self.tree_apps.heading('version', text='版本', anchor='w')
        self.tree_apps.heading('publisher', text='发布者', anchor='w')
        self.tree_apps.heading('size_mb', text='大小(MB)', anchor='w')
        self.tree_apps.heading('source', text='来源', anchor='w')

        self.tree_apps.column('name', width=200, minwidth=120)
        self.tree_apps.column('version', width=80, minwidth=50)
        self.tree_apps.column('publisher', width=120, minwidth=80)
        self.tree_apps.column('size_mb', width=80, minwidth=50)
        self.tree_apps.column('source', width=70, minwidth=50)

        scrollbar_apps = ttk.Scrollbar(left_frame, orient='vertical', command=self.tree_apps.yview)
        self.tree_apps.configure(yscrollcommand=scrollbar_apps.set)
        self.tree_apps.pack(fill='both', expand=True, padx=4, pady=(0, 4))
        scrollbar_apps.pack(side='right', fill='y')

        # ---- 右面板：应用数据 & 孤儿数据 ----
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        # 标签页
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill='both', expand=True, padx=4, pady=(6, 4))

        # 标签页1: 孤儿数据
        tab_orphan = ttk.Frame(self.notebook)
        self.notebook.add(tab_orphan, text='孤儿数据 (待清理)')

        cols = ('index', 'name', 'size_mb', 'file_count', 'modified', 'matched_app', 'confidence', 'select')
        self.tree_orphans = ttk.Treeview(tab_orphan, columns=cols, show='headings', style='Custom.Treeview')
        self.tree_orphans.heading('index', text='#', anchor='w')
        self.tree_orphans.heading('name', text='路径/名称', anchor='w')
        self.tree_orphans.heading('size_mb', text='大小(MB)', anchor='w')
        self.tree_orphans.heading('file_count', text='文件数', anchor='w')
        self.tree_orphans.heading('modified', text='修改时间', anchor='w')
        self.tree_orphans.heading('matched_app', text='匹配软件', anchor='w')
        self.tree_orphans.heading('confidence', text='置信度', anchor='w')
        self.tree_orphans.heading('select', text='选择', anchor='center')

        self.tree_orphans.column('index', width=30, minwidth=25)
        self.tree_orphans.column('name', width=250, minwidth=120)
        self.tree_orphans.column('size_mb', width=70, minwidth=50)
        self.tree_orphans.column('file_count', width=55, minwidth=40)
        self.tree_orphans.column('modified', width=130, minwidth=90)
        self.tree_orphans.column('matched_app', width=150, minwidth=80)
        self.tree_orphans.column('confidence', width=70, minwidth=50)
        self.tree_orphans.column('select', width=50, minwidth=40)

        self.tree_orphans.pack(fill='both', expand=True, padx=4, pady=(4, 2))

        # 选择框列
        self._add_checkbox_column()

        # 孤儿统计
        self.lbl_orphan_stats = ttk.Label(tab_orphan, text="选中: 0 | 总大小: 0 MB")
        self.lbl_orphan_stats.pack(anchor='w', padx=4, pady=(0, 4))

        # 标签页2: 所有应用数据
        tab_all = ttk.Frame(self.notebook)
        self.notebook.add(tab_all, text='所有应用数据')

        cols = ('name', 'size_mb', 'file_count', 'modified', 'matched_app', 'is_orphan')
        self.tree_all_data = ttk.Treeview(tab_all, columns=cols, show='headings', style='Custom.Treeview')
        self.tree_all_data.heading('name', text='名称', anchor='w')
        self.tree_all_data.heading('size_mb', text='大小(MB)', anchor='w')
        self.tree_all_data.heading('file_count', text='文件数', anchor='w')
        self.tree_all_data.heading('modified', text='修改时间', anchor='w')
        self.tree_all_data.heading('matched_app', text='匹配软件', anchor='w')
        self.tree_all_data.heading('is_orphan', text='孤儿', anchor='w')

        self.tree_all_data.pack(fill='both', expand=True, padx=4, pady=4)

        # 标签页3: 扫描日志
        tab_log = ttk.Frame(self.notebook)
        self.notebook.add(tab_log, text='扫描日志')

        self.log_text = scrolledtext.ScrolledText(
            tab_log, wrap='word', font=('Consolas', 9),
            bg='#1a1b26', fg='#a9b1d6', insertbackground='#a9b1d6',
            selectbackground='#414868', relief='flat', padx=8, pady=8)
        self.log_text.pack(fill='both', expand=True, padx=4, pady=4)

        # 清空日志按钮
        ttk.Button(tab_log, text="清空日志", command=self.log_text.delete).pack(anchor='e', padx=4, pady=(0, 4))

        # 重定向日志输出
        self._redirect_logger()

    def _add_checkbox_column(self):
        """在 Treeview 中添加复选框列"""
        self.orphan_checkbuttons = {}  # index -> BooleanVar

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(
            self.root, text="就绪 - 请点击扫描按钮开始", style='Status.TLabel')
        self.status_bar.pack(fill='x', side='bottom', padx=8, pady=(0, 6))

    def _redirect_logger(self):
        """重定向日志到文本框"""
        class LogHandler:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, message):
                self.text_widget.insert(tk.END, message)
                self.text_widget.see(tk.END)
                self.text_widget.update_idletasks()

            def flush(self):
                pass

        import logging
        logger = logging.getLogger('AppCleaner')
        if logger.handlers:
            handler = logging.StreamHandler(LogHandler(self.log_text))
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.handlers = [handler]

    # ============ 事件处理 ============
    def _log(self, message):
        """输出日志"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)

    def _set_status(self, message):
        """更新状态栏"""
        self.status_bar.config(text=message)

    def _start_scan(self):
        """开始扫描"""
        if self.scanning:
            return
        self.scanning = True
        self.btn_scan.config(state='disabled')
        self.btn_clean.config(state='disabled')
        self.progress.start(10)
        self._set_status("正在扫描...")

        # 清空之前的显示
        self._clear_trees()

        # 在新线程运行扫描
        custom_paths = []
        try:
            if self.entry_install_path.get().strip():
                custom_paths.append(Path(self.entry_install_path.get().strip()))
        except:
            pass

        custom_appdata = []
        try:
            if self.entry_appdata_path.get().strip():
                custom_appdata.append(Path(self.entry_appdata_path.get().strip()))
        except:
            pass

        self.cleaner = AppCleaner(
            custom_install_paths=custom_paths,
            custom_appdata_paths=custom_appdata,
            verbose=False,
            dry_run=self.var_dry_run.get(),
            use_recycle_bin=self.var_recycle.get(),
        )

        thread = threading.Thread(target=self._scan_thread, args=(custom_paths, custom_appdata))
        thread.start()

    def _scan_thread(self, custom_paths, custom_appdata):
        """扫描线程"""
        try:
            self.cleaner = AppCleaner(
                custom_install_paths=custom_paths,
                custom_appdata_paths=custom_appdata,
                verbose=False,
                dry_run=self.var_dry_run.get(),
                use_recycle_bin=self.var_recycle.get(),
            )
            self.scan_result = self.cleaner.run_scan()

            # 更新UI（在线程安全的方式下）
            self.root.after(0, self._on_scan_complete)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._on_scan_error(msg))

    def _on_scan_complete(self):
        """扫描完成回调"""
        self.scanning = False
        self.progress.stop()
        self.btn_scan.config(state='normal')
        self.btn_clean.config(state='normal')
        self._set_status(f"扫描完成 - 发现 {len(self.scan_result.orphan_folders)} 个孤儿数据")

        self._populate_trees()

        if self.scan_result.orphan_folders:
            total_mb = sum(f.size_mb for f in self.scan_result.orphan_folders)
            messagebox.showinfo("扫描完成",
                                f"发现 {len(self.scan_result.orphan_folders)} 个孤儿数据文件夹\n"
                                f"总共可释放 {total_mb:.2f} MB 空间")
        else:
            messagebox.showinfo("扫描完成", "未发现孤儿数据，系统很干净！")

    def _on_scan_error(self, error):
        """扫描错误回调"""
        self.scanning = False
        self.progress.stop()
        self.btn_scan.config(state='normal')
        self.btn_clean.config(state='disabled')
        self._set_status(f"扫描出错: {error}")
        messagebox.showerror("错误", error)

    def _clear_trees(self):
        """清空所有 Treeview"""
        self.tree_apps.delete(*self.tree_apps.get_children())
        self.tree_orphans.delete(*self.tree_orphans.get_children())
        self.tree_all_data.delete(*self.tree_all_data.get_children())

    def _populate_trees(self):
        """填充树形列表"""
        self.selected_orphan_indices.clear()

        # 已安装软件
        for i, app in enumerate(self.scan_result.installed_apps):
            self.tree_apps.insert('', 'end', values=(
                app.name[:60],
                app.version[:20],
                app.publisher[:30],
                f"{app.size_mb:.1f}",
                app.source,
            ), tags=('odd' if i % 2 else 'even'))

        # 孤儿数据
        self.orphan_items = []  # 存储文件夹引用
        self.tree_orphans.delete(*self.tree_orphans.get_children())
        self.tree_all_data.delete(*self.tree_all_data.get_children())

        for i, folder in enumerate(self.scan_result.orphan_folders):
            self.tree_orphans.insert('', 'end', values=(
                i,
                str(folder.path)[:80],
                f"{folder.size_mb:.2f}",
                folder.file_count,
                folder.modified_time.strftime('%Y-%m-%d %H:%M'),
                (folder.matched_app or '')[:30],
                f"{folder.confidence:.0%}",
                "☑",
            ), tags=('orphan',))
            self.orphan_items.append(folder)

            # 默认全选
            self.selected_orphan_indices.add(i)

        # 所有应用数据
        for i, folder in enumerate(self.scan_result.appdata_folders):
            tag = 'orphan_tag' if folder.is_orphan else 'normal'
            self.tree_all_data.insert('', 'end', values=(
                str(folder.path)[:80],
                f"{folder.size_mb:.2f}",
                folder.file_count,
                folder.modified_time.strftime('%Y-%m-%d %H:%M'),
                (folder.matched_app or '')[:30],
                "是" if folder.is_orphan else "否",
            ), tags=(tag,))

        # 绑定点击事件切换选择
        self.tree_orphans.bind('<Button-1>', self._on_orphan_click)

        self._update_orphan_stats()

        # 配置Treeview标签样式
        self.tree_apps.tag_configure('odd', background=COLORS['row_odd'])
        self.tree_apps.tag_configure('even', background=COLORS['row_even'])
        self.tree_orphans.tag_configure('orphan', background='#3a2030')
        self.tree_all_data.tag_configure('orphan_tag', background='#3a2030')
        self.tree_all_data.tag_configure('normal', background=COLORS['row_even'])

    def _on_orphan_click(self, event):
        """点击孤儿数据行切换选择"""
        region = self.tree_orphans.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree_orphans.identify_column(event.x)
            # 只在点击选择列 (第8列: #select) 或整行时切换
            col_idx = int(column[1:]) if column else 0

            item = self.tree_orphans.identify_row(event.y)
            if item:
                values = self.tree_orphans.item(item, 'values')
                if values and len(values) > 0:
                    idx = int(values[0])
                    if col_idx == 8 or col_idx == 0:  # 点击选择列或行首
                        if idx in self.selected_orphan_indices:
                            self.selected_orphan_indices.discard(idx)
                            self.tree_orphans.set(item, 'select', "☐")
                        else:
                            self.selected_orphan_indices.add(idx)
                            self.tree_orphans.set(item, 'select', "☑")
                        self._update_orphan_stats()

    def _update_orphan_stats(self):
        """更新孤儿数据统计"""
        selected = self._get_selected_orphans()
        total_mb = sum(f.size_mb for f in selected)
        self.lbl_orphan_stats.config(
            text=f"已选 {len(selected)} 项 | 总大小: {total_mb:.2f} MB")

    def _get_selected_orphans(self):
        """获取选中的孤儿数据"""
        if not hasattr(self, 'orphan_items'):
            return []
        return [self.orphan_items[i] for i in self.selected_orphan_indices if i < len(self.orphan_items)]

    def _create_checkbox(self, index):
        """创建复选框"""
        return "☑" if index in self.selected_orphan_indices else "☐"

    def _start_clean(self):
        """开始清理"""
        if self.cleaning or not self.scan_result:
            return

        orphans = self._get_selected_orphans()
        if not orphans:
            messagebox.showwarning("提示", "请先选择要清理的数据")
            return

        # 确认对话框
        total_mb = sum(f.size_mb for f in orphans)
        if not messagebox.askyesno(
            "确认清理",
            f"确定要清理 {len(orphans)} 个文件夹吗？\n"
            f"总共将释放 {total_mb:.2f} MB 空间。\n"
            f"{'（演习模式，不会实际删除）' if self.var_dry_run.get() else ''}"
        ):
            return

        if not self.var_dry_run.get() and not messagebox.askyesno(
            "最终确认",
            "⚠️ 此操作不可完全撤销！\n"
            "确定要继续吗？"
        ):
            return

        self.cleaning = True
        self.btn_clean.config(state='disabled')
        self._set_status("正在清理...")

        thread = threading.Thread(target=self._clean_thread, args=(orphans,))
        thread.start()

    def _clean_thread(self, orphans):
        """清理线程"""
        try:
            def confirm(folder):
                return True  # 已在主线程确认过

            # 获取选中项的索引
            indices = sorted(self.selected_orphan_indices)
            result = self.cleaner.clean_orphans(selected_indices=indices, confirm_callback=confirm)
            self.root.after(0, lambda: self._on_clean_complete(result))
        except Exception as e:
            self.root.after(0, lambda: self._on_clean_error(str(e)))

    def _on_clean_complete(self, result):
        """清理完成"""
        self.cleaning = False
        self.btn_clean.config(state='normal')
        self._set_status(f"清理完成 - 成功 {len(result['deleted'])}, 失败 {len(result['failed'])}")

        total_mb = result['total_size_mb']
        msg = (f"清理完成！\n\n"
               f"成功删除: {len(result['deleted'])} 个文件夹\n"
               f"删除失败: {len(result['failed'])} 个\n"
               f"已跳过: {len(result['skipped'])} 个\n"
               f"释放空间: {total_mb:.2f} MB")
        if result['failed']:
            msg += "\n\n失败项:"
            for f in result['failed']:
                msg += f"\n  - {f['path']}"

        messagebox.showinfo("清理结果", msg)

    def _on_clean_error(self, error):
        """清理错误"""
        self.cleaning = False
        self.btn_clean.config(state='normal')
        self._set_status(f"清理出错: {error}")
        messagebox.showerror("错误", error)

    def _export_report(self):
        """导出报告"""
        if not self.scan_result:
            messagebox.showwarning("提示", "请先进行扫描")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            title="保存扫描报告"
        )
        if filepath:
            success = self.cleaner.export_report(Path(filepath))
            if success:
                messagebox.showinfo("成功", f"报告已保存到:\n{filepath}")
            else:
                messagebox.showerror("失败", "导出报告失败")

    def _import_report(self):
        """导入报告"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            title="选择扫描报告"
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.log_text.insert(tk.END, f"\n已导入报告: {filepath}\n")
                messagebox.showinfo("成功", f"已导入报告:\n{filepath}")
            except Exception as e:
                messagebox.showerror("失败", f"导入失败: {e}")

    def _open_powershell(self):
        """打开 PowerShell"""
        try:
            subprocess.Popen(['powershell', '-NoExit', '-Command', 'Start-Process powershell -Verb RunAs'])
        except:
            os.startfile('powershell.exe')

    def _open_cmd(self):
        """打开 CMD 以管理员权限"""
        try:
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "cmd.exe", "", None, 1)
        except:
            os.startfile('cmd.exe')

    def _show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于", "系统软件清理工具 v1.0\n\n"
                         "功能:\n"
                         "• 扫描已安装软件\n"
                         "• 扫描应用数据目录\n"
                         "• 对比找出孤儿数据\n"
                         "• 批量安全删除\n"
                         "• 支持管理员权限操作\n\n"
                         "版权所有 (c) 2026")

    def _add_install_path(self):
        """添加自定义安装路径"""
        path = filedialog.askdirectory(title="选择软件安装目录")
        if path:
            self.entry_install_path.insert(tk.END, f";{path}")

    def _add_appdata_path(self):
        """添加自定义数据路径"""
        path = filedialog.askdirectory(title="选择应用数据目录")
        if path:
            self.entry_appdata_path.insert(tk.END, f";{path}")

    def run(self):
        """运行主循环"""
        self.root.mainloop()


# ============ 启动 ============
if __name__ == '__main__':
    # 以管理员权限运行（可选）
    if '--admin' in sys.argv and not require_admin():
        elevate_privileges()

    app = AppCleanerGUI()
    app.run()