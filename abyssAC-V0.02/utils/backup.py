# utils/backup.py
#!/usr/bin/env python3
"""
备份和恢复系统
"""

import zipfile
import tarfile
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

class BackupSystem:
    """备份系统"""
    
    def __init__(self, backup_dir: str = "./backups", max_backups: int = 10):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, source_dirs: List[str], backup_name: str = None, 
                     compression: str = "zip") -> Optional[str]:
        """创建备份"""
        try:
            # 生成备份名称
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = backup_name or f"backup_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.{compression}"
            
            # 创建备份
            if compression == "zip":
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for source_dir in source_dirs:
                        source_path = Path(source_dir)
                        if source_path.exists():
                            self._add_directory_to_zip(zipf, source_path)
            
            elif compression == "tar.gz":
                with tarfile.open(backup_path, "w:gz") as tar:
                    for source_dir in source_dirs:
                        source_path = Path(source_dir)
                        if source_path.exists():
                            tar.add(source_path, arcname=source_path.name)
            
            # 创建备份元数据
            metadata = {
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "compression": compression,
                "source_dirs": source_dirs,
                "checksum": self._calculate_checksum(backup_path),
                "size_bytes": backup_path.stat().st_size
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            print(f"✅ 备份创建成功: {backup_path}")
            return str(backup_path)
        
        except Exception as e:
            print(f"❌ 备份创建失败: {e}")
            return None
    
    def restore_backup(self, backup_path: str, target_dir: str = None, 
                      overwrite: bool = False) -> bool:
        """恢复备份"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                print(f"❌ 备份文件不存在: {backup_path}")
                return False
            
            # 验证备份完整性
            if not self._verify_backup(backup_path):
                print("❌ 备份文件损坏或验证失败")
                return False
            
            # 确定目标目录
            if target_dir is None:
                # 从元数据中读取原始目录
                metadata_path = backup_path.with_suffix('.json')
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    target_dir = metadata.get("source_dirs", ["./"])[0]
                else:
                    target_dir = "./"
            
            target_path = Path(target_dir)
            
            # 检查目标目录
            if target_path.exists() and not overwrite:
                print(f"❌ 目标目录已存在且未指定覆盖: {target_path}")
                return False
            
            # 创建临时目录用于解压
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 解压备份
                if backup_path.suffix == '.zip':
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        zipf.extractall(temp_path)
                
                elif backup_path.suffix in ['.tar.gz', '.tgz']:
                    with tarfile.open(backup_path, "r:gz") as tar:
                        tar.extractall(temp_path)
                
                # 恢复文件
                self._restore_files(temp_path, target_path, overwrite)
            
            print(f"✅ 备份恢复成功: {backup_path} -> {target_path}")
            return True
        
        except Exception as e:
            print(f"❌ 备份恢复失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.json"):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 检查对应的备份文件是否存在
                backup_path = Path(metadata.get("backup_path", ""))
                if backup_path.exists():
                    metadata["exists"] = True
                    metadata["actual_size"] = backup_path.stat().st_size
                else:
                    metadata["exists"] = False
                
                backups.append(metadata)
            
            except Exception:
                continue
        
        # 按创建时间排序
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    def delete_backup(self, backup_name: str) -> bool:
        """删除备份"""
        try:
            # 查找备份文件
            backup_files = list(self.backup_dir.glob(f"{backup_name}.*"))
            if not backup_files:
                print(f"❌ 未找到备份: {backup_name}")
                return False
            
            # 删除所有相关文件
            for backup_file in backup_files:
                backup_file.unlink()
            
            print(f"✅ 备份已删除: {backup_name}")
            return True
        
        except Exception as e:
            print(f"❌ 备份删除失败: {e}")
            return False
    
    def _add_directory_to_zip(self, zipf: zipfile.ZipFile, directory: Path):
        """递归添加目录到zip文件"""
        for item in directory.rglob("*"):
            if item.is_file():
                arcname = item.relative_to(directory.parent)
                zipf.write(item, arcname)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """验证备份完整性"""
        try:
            # 检查元数据文件
            metadata_path = backup_path.with_suffix('.json')
            if not metadata_path.exists():
                return False
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 验证校验和
            expected_checksum = metadata.get("checksum")
            if expected_checksum:
                actual_checksum = self._calculate_checksum(backup_path)
                if actual_checksum != expected_checksum:
                    print(f"❌ 校验和不匹配: {actual_checksum} != {expected_checksum}")
                    return False
            
            # 验证文件大小
            expected_size = metadata.get("size_bytes", 0)
            actual_size = backup_path.stat().st_size
            if actual_size != expected_size:
                print(f"❌ 文件大小不匹配: {actual_size} != {expected_size}")
                return False
            
            return True
        
        except Exception as e:
            print(f"❌ 备份验证失败: {e}")
            return False
    
    def _restore_files(self, source_dir: Path, target_dir: Path, overwrite: bool):
        """恢复文件到目标目录"""
        # 如果目标目录存在且需要覆盖，先删除
        if target_dir.exists() and overwrite:
            shutil.rmtree(target_dir)
        
        # 复制文件
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # 保留最新的max_backups个备份
            backups_to_delete = backups[self.max_backups:]
            
            for backup in backups_to_delete:
                backup_path = backup.get("backup_path")
                if backup_path:
                    try:
                        Path(backup_path).unlink()
                        print(f"🗑️  删除旧备份: {backup_path}")
                    except Exception:
                        pass

# 全局备份系统实例
backup_system = BackupSystem(max_backups=10)