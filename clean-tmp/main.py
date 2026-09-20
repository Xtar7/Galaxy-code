#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统软件清理工具 - 启动入口
选择运行模式：GUI 图形界面 或 CLI 命令行
"""

import sys
import os
import argparse

# 确保可以导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(
        description='系统软件清理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python main.py                  # 启动图形界面
  python main.py --cli            # 命令行模式
  python main.py --cli --scan     # 命令行扫描
  python main.py --cli --clean    # 命令行清理
  python main.py --help           # 显示帮助
        """
    )
    parser.add_argument('--cli', action='store_true', help='命令行模式')
    parser.add_argument('--admin', action='store_true', help='请求管理员权限')
    parser.add_argument('--scan', action='store_true', help='扫描')
    parser.add_argument('--clean', action='store_true', help='清理')
    parser.add_argument('--auto', action='store_true', help='自动确认')
    parser.add_argument('--dry-run', action='store_true', help='演习模式')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    parser.add_argument('--custom-install', type=str, action='append', default=[],
                        help='自定义安装路径')
    parser.add_argument('--custom-appdata', type=str, action='append', default=[],
                        help='自定义数据路径')

    args = parser.parse_args()

    if args.admin and not args.cli:
        args.cli = True  # 管理员权限只能通过命令行

    if args.admin and not args.cli:
        # 以管理员权限运行
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable,
                    " ".join(sys.argv[1:] + ['--admin']), None, 1)
                sys.exit(0)
        except Exception:
            pass

    if args.cli:
        from app_cleaner import main as cli_main
        sys.exit(cli_main())
    else:
        try:
            from app_cleaner_gui import AppCleanerGUI
            app = AppCleanerGUI()
            app.run()
        except ImportError as e:
            print(f"图形界面启动失败: {e}")
            print("请使用 --cli 参数运行命令行模式，或确保系统为 Windows。")
            sys.exit(1)


if __name__ == '__main__':
    main()
