import os
import re
import shutil
from datetime import datetime
from typing import List, Dict

class AutoFixer:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def fix_from_report(self, report_file: str, root_dir: str) -> Dict[str, int]:
        """Auto-fix berdasarkan laporan JSON"""
        import json
        
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        issues = report.get('issues', [])
        fixable_issues = [i for i in issues if i.get('auto_fixable', False)]
        
        if not fixable_issues:
            print("Tidak ada masalah yang bisa di-fix otomatis.")
            return {}
        
        # Group by file
        issues_by_file = {}
        for issue in fixable_issues:
            file = issue['file']
            if file not in issues_by_file:
                issues_by_file[file] = []
            issues_by_file[file].append(issue)
        
        stats = {'files_fixed': 0, 'issues_fixed': 0}
        
        for file, file_issues in issues_by_file.items():
            file_path = os.path.join(root_dir, file)
            
            if not os.path.exists(file_path):
                print(f"[!] File tidak ditemukan: {file_path}")
                continue
            
            # Backup file
            backup_path = self._create_backup(file_path)
            
            # Apply fixes
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Sort issues by line number (descending) untuk menghindari pergeseran baris
                file_issues.sort(key=lambda x: x['line'], reverse=True)
                
                for issue in file_issues:
                    line_idx = issue['line'] - 1
                    
                    if issue['id'] == 'ANOMALI-001':
                        # Hapus baris debug function
                        lines[line_idx] = ''
                        stats['issues_fixed'] += 1
                    
                    elif issue['id'] == 'BUG-002':
                        # Ganti md5/sha1 dengan password_hash
                        line = lines[line_idx]
                        # Simple replacement (bisa diperluas)
                        line = re.sub(r'\bmd5\s*\(', 'password_hash(', line)
                        lines[line_idx] = line
                        stats['issues_fixed'] += 1
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                stats['files_fixed'] += 1
                print(f"[✓] Fixed: {file} (Backup: {backup_path})")
                
            except Exception as e:
                print(f"[!] Error fixing {file}: {e}")
                # Restore from backup
                shutil.copy(backup_path, file_path)
                print(f"[↩] Restored from backup: {backup_path}")
        
        return stats
    
    def _create_backup(self, file_path: str) -> str:
        """Buat backup file dengan timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        shutil.copy(file_path, backup_path)
        return backup_path