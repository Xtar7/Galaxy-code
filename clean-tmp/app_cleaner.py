#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统软件清理工具 - 核心扫描模块
扫描已安装软件、应用数据，对比找出孤儿数据，支持批量清理
"""

import os
import sys
import json
import re
import hashlib
import shutil
import subprocess
import winreg
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ 配置常量 ============
class ScanScope(Enum):
    SYSTEM = "system"           # C:\Program Files, C:\Program Files (x86)
    USER = "user"               # C:\Users\{user}\AppData\Local\Programs
    CUSTOM = "custom"           # 用户指定路径 (如 D:\Programs)

# Windows 常见应用数据目录
APPDATA_ROOTS = [
    Path(os.environ.get('LOCALAPPDATA', '')) if os.environ.get('LOCALAPPDATA') else None,
    Path(os.environ.get('APPDATA', '')) if os.environ.get('APPDATA') else None,
    Path(os.environ.get('PROGRAMDATA', '')) if os.environ.get('PROGRAMDATA') else None,
]
APPDATA_ROOTS = [p for p in APPDATA_ROOTS if p and p.exists()]

# 扫描的注册表位置
REGISTRY_UNINSTALL_PATHS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]

# 忽略的系统目录/文件
IGNORE_PATTERNS = [
    r'Microsoft',
    r'Windows',
    r'Intel',
    r'NVIDIA',
    r'AMD',
    r'Realtek',
    r'Dell',
    r'HP',
    r'Lenovo',
    r'ASUS',
    r'MSI',
    r'System32',
    r'SysWOW64',
    r'WinSxS',
    r'WindowsPowerShell',
    r'OneDrive',
    r'Edge',
    r'Chrome',
    r'Firefox',
    r'Adobe',
    r'NVIDIA Corporation',
    r'AMD',
    r'Intel Corporation',
    r'VC_Redist',
    r'Visual C++',
    r'.NET',
    r'Microsoft Visual',
    r'Windows Driver',
    r'Windows Update',
    r'Hotfix',
    r'Security Update',
    r'KB\d+',
]

# 常见的应用数据子目录名称
APPDATA_SUBDIRS = [
    'Local', 'Roaming', 'LocalLow',
    'Cache', 'Logs', 'Crashpad', 'CrashReports',
    'Temp', 'tmp', 'temp',
    'Data', 'data',
    'Config', 'config',
    'Settings', 'settings',
    'Profiles', 'profiles',
    'Storage', 'storage',
    'Databases', 'databases',
    'IndexedDB', 'indexeddb',
    'Local Storage', 'localstorage',
    'Session Storage', 'sessionstorage',
    'Service Worker', 'serviceworker',
    'GPUCache', 'gpucache',
    'ShaderCache', 'shadercache',
    'blob_storage', 'BlobStorage',
]

# ============ 数据结构 ============
@dataclass
class InstalledApp:
    """已安装软件信息"""
    name: str
    version: str = ""
    publisher: str = ""
    install_location: str = ""
    install_date: str = ""
    uninstall_string: str = ""
    registry_key: str = ""
    source: str = "registry"  # registry, filesystem, winget, scoop, chocolatey
    size_mb: float = 0.0
    is_system: bool = False

    @property
    def normalized_name(self) -> str:
        """标准化名称用于匹配"""
        name = self.name.lower()
        # 移除常见后缀
        for suffix in [' (64-bit)', ' (x64)', ' (x86)', ' 64-bit', ' x64', ' x86']:
            name = name.replace(suffix, '')
        return re.sub(r'[^\w\s\-]', '', name).strip()

    @property
    def key_name(self) -> str:
        """用于匹配的关键名称"""
        return self.normalized_name.replace(' ', '')

@dataclass
class AppDataFolder:
    """应用数据文件夹信息"""
    path: Path
    name: str
    size_mb: float
    file_count: int
    modified_time: datetime
    matched_app: Optional[str] = None  # 匹配的已安装软件名
    confidence: float = 0.0  # 匹配置信度 0-1
    is_orphan: bool = False  # 是否为孤儿数据

    def to_dict(self) -> dict:
        return {
            'path': str(self.path),
            'name': self.name,
            'size_mb': round(self.size_mb, 2),
            'file_count': self.file_count,
            'modified_time': self.modified_time.isoformat(),
            'matched_app': self.matched_app,
            'confidence': round(self.confidence, 2),
            'is_orphan': self.is_orphan,
        }

@dataclass
class ScanResult:
    """扫描结果汇总"""
    installed_apps: List[InstalledApp] = field(default_factory=list)
    appdata_folders: List[AppDataFolder] = field(default_factory=list)
    orphan_folders: List[AppDataFolder] = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    scan_paths: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'scan_time': self.scan_time.isoformat(),
            'scan_paths': self.scan_paths,
            'installed_apps': [asdict(app) for app in self.installed_apps],
            'appdata_folders': [f.to_dict() for f in self.appdata_folders],
            'orphan_folders': [f.to_dict() for f in self.orphan_folders],
            'errors': self.errors,
            'summary': {
                'total_apps': len(self.installed_apps),
                'total_appdata_folders': len(self.appdata_folders),
                'orphan_count': len(self.orphan_folders),
                'orphan_size_mb': round(sum(f.size_mb for f in self.orphan_folders), 2),
            }
        }

# ============ 工具函数 ============
def setup_logging(verbose: bool = False) -> logging.Logger:
    """设置日志"""
    logger = logging.getLogger('AppCleaner')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def get_folder_size(path: Path) -> Tuple[float, int]:
    """获取文件夹大小(MB)和文件数量"""
    total_size = 0
    file_count = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return total_size / (1024 * 1024), file_count

def normalize_string(s: str) -> str:
    """标准化字符串用于匹配"""
    s = s.lower()
    s = re.sub(r'[^\w\s\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def calculate_similarity(a: str, b: str) -> float:
    """计算两个字符串的相似度 (Jaccard 系数)"""
    if not a or not b:
        return 0.0
    set_a = set(a.split())
    set_b = set(b.split())
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0

def is_system_folder(name: str) -> bool:
    """判断是否为系统/驱动相关文件夹"""
    name_lower = name.lower()
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return True
    return False

def require_admin() -> bool:
    """检查是否以管理员权限运行"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    """请求管理员权限重新运行"""
    import ctypes
    import sys
    if not require_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

# ============ 核心扫描器 ============
class SoftwareScanner:
    """软件扫描器 - 扫描已安装软件"""

    def __init__(self, logger: logging.Logger, custom_paths: List[Path] = None):
        self.logger = logger
        self.custom_paths = custom_paths or []
        self.apps: List[InstalledApp] = []

    def scan_registry(self) -> List[InstalledApp]:
        """从注册表扫描已安装软件"""
        apps = []
        for hive, subkey in REGISTRY_UNINSTALL_PATHS:
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as sub:
                                name = self._get_reg_value(sub, 'DisplayName')
                                if not name or is_system_folder(name):
                                    continue

                                # 检查是否为系统组件
                                system_component = self._get_reg_value(sub, 'SystemComponent')
                                if system_component == 1:
                                    continue

                                app = InstalledApp(
                                    name=name,
                                    version=self._get_reg_value(sub, 'DisplayVersion') or "",
                                    publisher=self._get_reg_value(sub, 'Publisher') or "",
                                    install_location=self._get_reg_value(sub, 'InstallLocation') or "",
                                    install_date=self._get_reg_value(sub, 'InstallDate') or "",
                                    uninstall_string=self._get_reg_value(sub, 'UninstallString') or "",
                                    registry_key=subkey_name,
                                    source="registry",
                                    is_system=bool(system_component),
                                )
                                # 计算安装目录大小
                                if app.install_location and Path(app.install_location).exists():
                                    app.size_mb, _ = get_folder_size(Path(app.install_location))

                                apps.append(app)
                        except (OSError, PermissionError, WindowsError):
                            continue
            except (OSError, PermissionError, WindowsError) as e:
                self.logger.debug(f"无法访问注册表 {hive}\\{subkey}: {e}")
        return apps

    def _get_reg_value(self, key, name: str):
        """安全读取注册表值"""
        try:
            value, _ = winreg.QueryValueEx(key, name)
            return value
        except (OSError, WindowsError):
            return None

    def scan_filesystem(self, paths: List[Path]) -> List[InstalledApp]:
        """从文件系统扫描安装目录"""
        apps = []
        for base_path in paths:
            if not base_path.exists():
                continue
            try:
                for entry in base_path.iterdir():
                    if not entry.is_dir() or is_system_folder(entry.name):
                        continue

                    # 尝试读取版本信息
                    version = ""
                    uninstall = ""

                    # 查找卸载信息
                    for uninstall_file in entry.rglob('unins*.exe'):
                        uninstall = str(uninstall_file)
                        break
                    for uninstall_file in entry.rglob('uninstall*.exe'):
                        uninstall = str(uninstall_file)
                        break

                    size_mb, _ = get_folder_size(entry)

                    app = InstalledApp(
                        name=entry.name,
                        version=version,
                        install_location=str(entry),
                        uninstall_string=uninstall,
                        source="filesystem",
                        size_mb=size_mb,
                    )
                    apps.append(app)
            except (OSError, PermissionError) as e:
                self.logger.debug(f"扫描 {base_path} 出错: {e}")
        return apps

    def scan_winget(self) -> List[InstalledApp]:
        """扫描 winget 安装的软件"""
        apps = []
        try:
            result = subprocess.run(
                ['winget', 'list', '--accept-source-agreements'],
                capture_output=True, text=True, timeout=30,
                encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[2:]:  # 跳过表头
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) >= 3:
                        name = parts[0]
                        if not is_system_folder(name):
                            apps.append(InstalledApp(
                                name=name,
                                version=parts[1] if len(parts) > 1 else "",
                                source="winget",
                            ))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return apps

    def scan_scoop(self) -> List[InstalledApp]:
        """扫描 Scoop 安装的软件"""
        apps = []
        try:
            scoop_dir = Path(os.environ.get('SCOOP', '')) / 'apps'
            if scoop_dir.exists():
                for entry in scoop_dir.iterdir():
                    if entry.is_dir() and not is_system_folder(entry.name):
                        current = entry / 'current'
                        if current.exists() and current.is_symlink():
                            target = current.readlink()
                            size_mb, _ = get_folder_size(target)
                            apps.append(InstalledApp(
                                name=entry.name,
                                install_location=str(target),
                                source="scoop",
                                size_mb=size_mb,
                            ))
        except Exception:
            pass
        return apps

    def scan_chocolatey(self) -> List[InstalledApp]:
        """扫描 Chocolatey 安装的软件"""
        apps = []
        try:
            choco_dir = Path(os.environ.get('ChocolateyInstall', 'C:\\ProgramData\\chocolatey')) / 'lib'
            if choco_dir.exists():
                for entry in choco_dir.iterdir():
                    if entry.is_dir() and not is_system_folder(entry.name):
                        size_mb, _ = get_folder_size(entry)
                        apps.append(InstalledApp(
                            name=entry.name.replace('.', ' ').title(),
                            install_location=str(entry),
                            source="chocolatey",
                            size_mb=size_mb,
                        ))
        except Exception:
            pass
        return apps

    def scan_all(self) -> List[InstalledApp]:
        """执行完整扫描"""
        self.logger.info("开始扫描已安装软件...")

        # 从注册表扫描
        self.logger.debug("扫描注册表...")
        reg_apps = self.scan_registry()
        self.logger.info(f"注册表扫描到 {len(reg_apps)} 个应用")

        # 从文件系统扫描 (C盘默认路径 + 自定义路径)
        default_paths = [
            Path(r"C:\Program Files"),
            Path(r"C:\Program Files (x86)"),
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' if os.environ.get('LOCALAPPDATA') else None,
        ]
        default_paths = [p for p in default_paths if p and p.exists()]
        all_paths = default_paths + self.custom_paths

        self.logger.debug(f"扫描文件系统: {[str(p) for p in all_paths]}")
        fs_apps = self.scan_filesystem(all_paths)
        self.logger.info(f"文件系统扫描到 {len(fs_apps)} 个应用")

        # 包管理器扫描
        winget_apps = self.scan_winget()
        self.logger.info(f"Winget 扫描到 {len(winget_apps)} 个应用")

        scoop_apps = self.scan_scoop()
        self.logger.info(f"Scoop 扫描到 {len(scoop_apps)} 个应用")

        choco_apps = self.scan_chocolatey()
        self.logger.info(f"Chocolatey 扫描到 {len(choco_apps)} 个应用")

        # 合并去重
        all_apps = reg_apps + fs_apps + winget_apps + scoop_apps + choco_apps
        self.apps = self._deduplicate_apps(all_apps)

        self.logger.info(f"去重后共 {len(self.apps)} 个应用")
        return self.apps

    def _deduplicate_apps(self, apps: List[InstalledApp]) -> List[InstalledApp]:
        """去重：按名称合并"""
        seen = {}
        for app in apps:
            key = app.key_name
            if key not in seen:
                seen[key] = app
            else:
                # 合并信息：优先保留注册表信息
                existing = seen[key]
                if app.source == "registry" and existing.source != "registry":
                    seen[key] = app
                elif app.source == existing.source and app.size_mb > existing.size_mb:
                    seen[key] = app
        return list(seen.values())


class AppDataScanner:
    """应用数据扫描器 - 扫描 AppData 等目录下的软件数据"""

    def __init__(self, logger: logging.Logger, custom_appdata_paths: List[Path] = None):
        self.logger = logger
        self.custom_paths = custom_appdata_paths or []
        self.folders: List[AppDataFolder] = []

    def scan(self, installed_apps: List[InstalledApp]) -> List[AppDataFolder]:
        """扫描应用数据目录"""
        self.logger.info("开始扫描应用数据目录...")

        # 构建扫描路径
        scan_paths = APPDATA_ROOTS + self.custom_paths
        scan_paths = [p for p in scan_paths if p and p.exists()]

        # 建立已安装应用的名称索引
        app_names = {app.normalized_name: app for app in installed_apps}
        app_key_names = {app.key_name: app for app in installed_apps}

        all_folders = []

        for base_path in scan_paths:
            self.logger.debug(f"扫描: {base_path}")
            folders = self._scan_directory(base_path, app_names, app_key_names)
            all_folders.extend(folders)

        self.folders = all_folders
        self.logger.info(f"扫描到 {len(all_folders)} 个应用数据文件夹")
        return all_folders

    def _scan_directory(self, base_path: Path, app_names: Dict, app_key_names: Dict) -> List[AppDataFolder]:
        """递归扫描目录"""
        folders = []
        try:
            for entry in base_path.iterdir():
                if not entry.is_dir():
                    continue

                if is_system_folder(entry.name):
                    continue

                # 检查是否为已知应用数据子目录
                if entry.name in APPDATA_SUBDIRS:
                    # 继续深入扫描
                    sub_folders = self._scan_directory(entry, app_names, app_key_names)
                    folders.extend(sub_folders)
                    continue

                # 计算大小
                size_mb, file_count = get_folder_size(entry)
                if size_mb < 0.1:  # 忽略太小的文件夹
                    continue

                modified_time = datetime.fromtimestamp(entry.stat().st_mtime)

                # 尝试匹配已安装应用
                matched_app, confidence = self._match_app(entry.name, app_names, app_key_names)

                folder = AppDataFolder(
                    path=entry,
                    name=entry.name,
                    size_mb=size_mb,
                    file_count=file_count,
                    modified_time=modified_time,
                    matched_app=matched_app,
                    confidence=confidence,
                    is_orphan=(matched_app is None or confidence < 0.3),
                )
                folders.append(folder)

        except (OSError, PermissionError) as e:
            self.logger.debug(f"无法访问 {base_path}: {e}")

        return folders

    def _match_app(self, folder_name: str, app_names: Dict, app_key_names: Dict) -> Tuple[Optional[str], float]:
        """匹配文件夹名到已安装应用"""
        norm_folder = normalize_string(folder_name)
        key_folder = norm_folder.replace(' ', '')

        best_match = None
        best_score = 0.0

        # 1. 精确匹配 key_name
        if key_folder in app_key_names:
            return app_key_names[key_folder].name, 1.0

        # 2. 精确匹配 normalized_name
        if norm_folder in app_names:
            return app_names[norm_folder].name, 0.95

        # 3. 模糊匹配
        for app_name, app in app_names.items():
            score = calculate_similarity(norm_folder, app_name)
            if score > best_score:
                best_score = score
                best_match = app.name

        for key_name, app in app_key_names.items():
            score = calculate_similarity(key_folder, key_name)
            if score > best_score:
                best_score = score
                best_match = app.name

        # 阈值判断
        if best_score >= 0.6:
            return best_match, best_score

        return None, 0.0


class OrphanAnalyzer:
    """孤儿数据分析器 - 对比找出已卸载软件的残留数据"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def analyze(self, installed_apps: List[InstalledApp], appdata_folders: List[AppDataFolder]) -> List[AppDataFolder]:
        """分析并标记孤儿数据"""
        self.logger.info("分析孤儿数据...")

        # 建立已安装应用名称集合
        installed_names = {app.normalized_name for app in installed_apps}
        installed_keys = {app.key_name for app in installed_apps}

        orphans = []
        for folder in appdata_folders:
            # 已经标记为孤儿的保持
            if folder.is_orphan:
                orphans.append(folder)
                continue

            # 检查匹配的应用是否仍然安装
            if folder.matched_app:
                matched_norm = normalize_string(folder.matched_app)
                matched_key = matched_norm.replace(' ', '')

                if matched_norm not in installed_names and matched_key not in installed_keys:
                    folder.is_orphan = True
                    folder.confidence = 0.0
                    orphans.append(folder)
            else:
                folder.is_orphan = True
                orphans.append(folder)

        # 按大小排序
        orphans.sort(key=lambda f: f.size_mb, reverse=True)

        self.logger.info(f"发现 {len(orphans)} 个孤儿数据文件夹，总大小: {sum(f.size_mb for f in orphans):.2f} MB")
        return orphans


class Cleaner:
    """清理执行器"""

    def __init__(self, logger: logging.Logger, dry_run: bool = False, use_recycle_bin: bool = True):
        self.logger = logger
        self.dry_run = dry_run
        self.use_recycle_bin = use_recycle_bin
        self.results = {
            'deleted': [],
            'failed': [],
            'skipped': [],
            'total_size_mb': 0.0,
        }

    def clean(self, folders: List[AppDataFolder], confirm_callback=None) -> dict:
        """执行清理"""
        if not folders:
            self.logger.info("没有要清理的文件夹")
            return self.results

        self.logger.info(f"准备清理 {len(folders)} 个文件夹...")

        for folder in folders:
            if confirm_callback and not confirm_callback(folder):
                self.results['skipped'].append(folder.to_dict())
                self.logger.info(f"跳过: {folder.path}")
                continue

            success = self._delete_folder(folder.path)
            if success:
                self.results['deleted'].append(folder.to_dict())
                self.results['total_size_mb'] += folder.size_mb
                self.logger.info(f"已删除: {folder.path} ({folder.size_mb:.2f} MB)")
            else:
                self.results['failed'].append(folder.to_dict())
                self.logger.error(f"删除失败: {folder.path}")

        self.logger.info(f"清理完成: 成功 {len(self.results['deleted'])}, 失败 {len(self.results['failed'])}, 跳过 {len(self.results['skipped'])}")
        self.logger.info(f"释放空间: {self.results['total_size_mb']:.2f} MB")
        return self.results

    def _delete_folder(self, path: Path) -> bool:
        """删除文件夹"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] 将删除: {path}")
            return True

        try:
            if self.use_recycle_bin:
                return self._move_to_recycle_bin(path)
            else:
                shutil.rmtree(path, ignore_errors=False)
                return True
        except PermissionError:
            # 尝试修改权限后删除
            return self._force_delete(path)
        except Exception as e:
            self.logger.error(f"删除 {path} 异常: {e}")
            return False

    def _move_to_recycle_bin(self, path: Path) -> bool:
        """移动到回收站"""
        try:
            # 尝试使用 send2trash
            import send2trash
            send2trash.send2trash(str(path))
            return True
        except ImportError:
            # 回退到 SHFileOperation
            return self._shell_delete(path)
        except Exception:
            return self._shell_delete(path)

    def _shell_delete(self, path: Path) -> bool:
        """使用 Windows Shell API 删除到回收站"""
        try:
            import ctypes
            from ctypes import wintypes

            FO_DELETE = 3
            FOF_ALLOWUNDO = 0x40
            FOF_NOCONFIRMATION = 0x10
            FOF_SILENT = 0x4

            class SHFILEOPSTRUCT(ctypes.Structure):
                _fields_ = [
                    ('hwnd', wintypes.HWND),
                    ('wFunc', wintypes.UINT),
                    ('pFrom', wintypes.LPCWSTR),
                    ('pTo', wintypes.LPCWSTR),
                    ('fFlags', wintypes.USHORT),
                    ('fAnyOperationsAborted', wintypes.BOOL),
                    ('hNameMappings', wintypes.LPVOID),
                    ('lpszProgressTitle', wintypes.LPCWSTR),
                ]

            SHFileOperation = ctypes.windll.shell32.SHFileOperationW
            SHFileOperation.argtypes = [ctypes.POINTER(SHFILEOPSTRUCT)]
            SHFileOperation.restype = wintypes.INT

            # 双重空终止
            p_from = str(path) + '\0\0'

            op = SHFILEOPSTRUCT(
                hwnd=0,
                wFunc=FO_DELETE,
                pFrom=p_from,
                pTo=None,
                fFlags=FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT,
                fAnyOperationsAborted=False,
                hNameMappings=None,
                lpszProgressTitle=None,
            )

            result = SHFileOperation(ctypes.byref(op))
            return result == 0
        except Exception as e:
            self.logger.debug(f"Shell 删除失败: {e}")
            return False

    def _force_delete(self, path: Path) -> bool:
        """强制删除 (修改权限后)"""
        try:
            # 使用 icacls 修改权限
            subprocess.run(
                ['icacls', str(path), '/grant', 'Administrators:F', '/t', '/c', '/q'],
                capture_output=True, timeout=30
            )
            subprocess.run(
                ['icacls', str(path), '/setowner', 'Administrators', '/t', '/c', '/q'],
                capture_output=True, timeout=30
            )

            # 移除只读属性
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o666)

            shutil.rmtree(path)
            return True
        except Exception as e:
            self.logger.error(f"强制删除失败: {e}")
            return False


# ============ 主控制器 ============
class AppCleaner:
    """主控制器 - 协调扫描、分析、清理"""

    def __init__(self,
                 custom_install_paths: List[str] = None,
                 custom_appdata_paths: List[str] = None,
                 verbose: bool = False,
                 dry_run: bool = False,
                 use_recycle_bin: bool = True):
        self.logger = setup_logging(verbose)
        self.dry_run = dry_run
        self.use_recycle_bin = use_recycle_bin

        self.custom_install_paths = [Path(p) for p in (custom_install_paths or [])]
        self.custom_appdata_paths = [Path(p) for p in (custom_appdata_paths or [])]

        self.software_scanner = SoftwareScanner(self.logger, self.custom_install_paths)
        self.appdata_scanner = AppDataScanner(self.logger, self.custom_appdata_paths)
        self.orphan_analyzer = OrphanAnalyzer(self.logger)
        self.cleaner = Cleaner(self.logger, dry_run, use_recycle_bin)

        self.result: Optional[ScanResult] = None

    def run_scan(self) -> ScanResult:
        """执行完整扫描"""
        self.logger.info("=" * 50)
        self.logger.info("开始完整扫描")
        self.logger.info("=" * 50)

        # 1. 扫描已安装软件
        installed_apps = self.software_scanner.scan_all()

        # 2. 扫描应用数据
        appdata_folders = self.appdata_scanner.scan(installed_apps)

        # 3. 分析孤儿数据
        orphan_folders = self.orphan_analyzer.analyze(installed_apps, appdata_folders)

        # 4. 汇总结果
        self.result = ScanResult(
            installed_apps=installed_apps,
            appdata_folders=appdata_folders,
            orphan_folders=orphan_folders,
            scan_paths=[str(p) for p in self.custom_install_paths + self.custom_appdata_paths],
        )

        self.logger.info("=" * 50)
        self.logger.info("扫描完成")
        self.logger.info(f"已安装软件: {len(installed_apps)}")
        self.logger.info(f"应用数据文件夹: {len(appdata_folders)}")
        self.logger.info(f"孤儿数据: {len(orphan_folders)} ({sum(f.size_mb for f in orphan_folders):.2f} MB)")
        self.logger.info("=" * 50)

        return self.result

    def clean_orphans(self, selected_indices: List[int] = None, confirm_callback=None) -> dict:
        """清理选定的孤儿数据"""
        if not self.result:
            raise RuntimeError("请先运行扫描")

        orphans = self.result.orphan_folders
        if selected_indices is not None:
            orphans = [orphans[i] for i in selected_indices if 0 <= i < len(orphans)]

        return self.cleaner.clean(orphans, confirm_callback)

    def export_report(self, filepath: Path) -> bool:
        """导出扫描报告"""
        if not self.result:
            return False
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.result.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.info(f"报告已导出: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            return False


# ============ 命令行界面 ============
def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='系统软件清理工具 - 扫描孤儿应用数据并清理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --scan                    # 仅扫描并显示结果
  %(prog)s --scan --custom-install D:\\Programs --custom-appdata D:\\AppData
  %(prog)s --clean --auto            # 扫描并自动清理所有孤儿数据
  %(prog)s --clean --select 0,1,2    # 扫描并清理指定索引的孤儿数据
  %(prog)s --export report.json      # 导出扫描报告
        """
    )

    parser.add_argument('--scan', action='store_true', help='执行扫描')
    parser.add_argument('--clean', action='store_true', help='执行清理 (需配合 --scan 或已有报告)')
    parser.add_argument('--auto', action='store_true', help='自动清理所有孤儿数据，不询问确认')
    parser.add_argument('--select', type=str, help='指定要清理的孤儿数据索引 (逗号分隔，如 0,1,2)')
    parser.add_argument('--export', type=str, help='导出扫描报告到 JSON 文件')
    parser.add_argument('--import', dest='import_file', type=str, help='从 JSON 文件导入扫描结果')

    parser.add_argument('--custom-install', type=str, action='append', default=[],
                        help='自定义软件安装路径 (可多次指定，如 D:\\Programs)')
    parser.add_argument('--custom-appdata', type=str, action='append', default=[],
                        help='自定义应用数据路径 (可多次指定)')

    parser.add_argument('--dry-run', action='store_true', help='演习模式，不实际删除')
    parser.add_argument('--no-recycle', action='store_true', help='直接删除，不放入回收站')
    parser.add_argument('--admin', action='store_true', help='请求管理员权限运行')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    return parser


def print_scan_result(result: ScanResult):
    """打印扫描结果"""
    print("\n" + "=" * 70)
    print(f"扫描完成 - {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"已安装软件: {len(result.installed_apps)} 个")
    print(f"应用数据文件夹: {len(result.appdata_folders)} 个")
    print(f"孤儿数据文件夹: {len(result.orphan_folders)} 个")
    print(f"可释放空间: {sum(f.size_mb for f in result.orphan_folders):.2f} MB")
    print("-" * 70)

    if result.orphan_folders:
        print("\n孤儿数据列表 (按大小排序):")
        print(f"{'索引':<6} {'名称':<40} {'大小(MB)':<10} {'文件数':<8} {'修改时间':<20} {'匹配应用'}")
        print("-" * 100)
        for i, folder in enumerate(result.orphan_folders):
            matched = folder.matched_app or "未匹配"
            if len(matched) > 30:
                matched = matched[:27] + "..."
            print(f"{i:<6} {folder.name:<40} {folder.size_mb:<10.2f} {folder.file_count:<8} "
                  f"{folder.modified_time.strftime('%Y-%m-%d %H:%M'):<20} {matched}")
    else:
        print("\n未发现孤儿数据，系统很干净！")


def main():
    parser = build_cli_parser()
    args = parser.parse_args()

    # 请求管理员权限
    if args.admin and not require_admin():
        elevate_privileges()

    # 创建清理器
    cleaner = AppCleaner(
        custom_install_paths=args.custom_install,
        custom_appdata_paths=args.custom_appdata,
        verbose=args.verbose,
        dry_run=args.dry_run,
        use_recycle_bin=not args.no_recycle,
    )

    result = None

    # 导入已有报告
    if args.import_file:
        try:
            with open(args.import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 这里简化处理，实际应该反序列化为对象
            print(f"已导入报告: {args.import_file}")
        except Exception as e:
            print(f"导入失败: {e}")
            return 1

    # 执行扫描
    if args.scan or args.clean:
        result = cleaner.run_scan()
        print_scan_result(result)

    # 导出报告
    if args.export and result:
        cleaner.export_report(Path(args.export))

    # 执行清理
    if args.clean and result:
        if not result.orphan_folders:
            print("没有孤儿数据需要清理")
            return 0

        selected = None
        if args.select:
            try:
                selected = [int(x.strip()) for x in args.select.split(',')]
            except ValueError:
                print("索引格式错误，请使用逗号分隔的数字，如: 0,1,2")
                return 1

        def confirm(folder):
            if args.auto:
                return True
            resp = input(f"删除 [{folder.name}] ({folder.size_mb:.2f} MB) ? [y/N]: ").strip().lower()
            return resp == 'y'

        clean_result = cleaner.clean_orphans(selected, confirm)

        print("\n清理结果:")
        print(f"  成功: {len(clean_result['deleted'])} 个")
        print(f"  失败: {len(clean_result['failed'])} 个")
        print(f"  跳过: {len(clean_result['skipped'])} 个")
        print(f"  释放: {clean_result['total_size_mb']:.2f} MB")

        if clean_result['failed']:
            print("\n失败列表:")
            for f in clean_result['failed']:
                print(f"  - {f['path']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())