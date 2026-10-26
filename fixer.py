import os
import re
import json
import shutil
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
from logger import get_logger

logger = get_logger("fixer")


class AutoFixer:
    """
    Auto-Fix Engine yang canggih dengan strategi fix spesifik per rule.
    Mendukung: dry-run, backup, rollback, dan statistik detail.
    """
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        # Registry strategi fix (mapping rule_id -> fix_function)
        self.fix_strategies = {
            'SEC-009': self._fix_weak_crypto,
            'SEC-011': self._fix_remove_debug_php,
            'SEC-012': self._fix_insecure_cookie,
            'SEC-019': self._fix_loose_comparison,
            'SEC-020': self._fix_chmod_permission,
            'SEC-022': self._fix_cors_wildcard,
            'SEC-023': self._fix_ssl_verify_false,
            'SEC-024': self._fix_directory_listing,
            'SEC-025': self._fix_remove_console_log,
            'SEC-030': self._fix_http_to_https,
        }
        
        # Statistik
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'issues_skipped': 0,
            'backups_created': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_category': {}
        }
    
    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================
    
    def fix_from_report(self, report_file: str, root_dir: str, 
                       dry_run: bool = False, 
                       interactive: bool = False) -> Dict:
        """
        Auto-fix berdasarkan laporan JSON
        
        Args:
            report_file: Path ke file laporan JSON
            root_dir: Direktori root project
            dry_run: Jika True, hanya preview tanpa mengubah file
            interactive: Jika True, minta konfirmasi per issue
        
        Returns:
            Dict: Statistik hasil fix
        """
        logger.info(f"Memulai auto-fix dari: {report_file} (dry_run={dry_run})")
        
        # Reset stats
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'issues_skipped': 0,
            'backups_created': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_category': {},
            'dry_run': dry_run
        }
        
        # Load report
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
        except Exception as e:
            logger.error(f"Gagal membaca report: {e}")
            return self.stats
        
        issues = report.get('issues', [])
        self.stats['issues_found'] = len(issues)
        
        # Filter issues yang bisa di-fix
        fixable_issues = [i for i in issues if i['id'] in self.fix_strategies]
        unfixable_issues = [i for i in issues if i['id'] not in self.fix_strategies]
        
        logger.info(f"Total issues: {len(issues)}, Fixable: {len(fixable_issues)}, Unfixable: {len(unfixable_issues)}")
        
        if not fixable_issues:
            print("\n[!] Tidak ada masalah yang bisa di-fix otomatis.")
            if unfixable_issues:
                print(f"[i] {len(unfixable_issues)} masalah memerlukan perbaikan manual.")
            return self.stats
        
        # Preview unfixable issues
        if unfixable_issues:
            print(f"\n{'='*70}")
            print(f"⚠️  {len(unfixable_issues)} masalah TIDAK BISA di-fix otomatis:")
            print(f"{'='*70}")
            unfixable_by_id = {}
            for issue in unfixable_issues:
                rule_id = issue['id']
                if rule_id not in unfixable_by_id:
                    unfixable_by_id[rule_id] = {
                        'kategori': issue['kategori'],
                        'count': 0,
                        'severity': issue['severity']
                    }
                unfixable_by_id[rule_id]['count'] += 1
            
            for rule_id, info in unfixable_by_id.items():
                print(f"  [{info['severity']}] {rule_id} - {info['kategori']} ({info['count']}x)")
            print(f"{'='*70}\n")
        
        # Group fixable issues by file
        issues_by_file = {}
        for issue in fixable_issues:
            file = issue['file']
            if file not in issues_by_file:
                issues_by_file[file] = []
            issues_by_file[file].append(issue)
        
        # Process each file
        for file, file_issues in issues_by_file.items():
            file_path = os.path.join(root_dir, file)
            self._process_file(file_path, file_issues, dry_run, interactive)
        
        return self.stats
    
    # =========================================================================
    # FILE PROCESSING
    # =========================================================================
    
    def _process_file(self, file_path: str, issues: List[Dict], 
                     dry_run: bool, interactive: bool):
        """Proses satu file dengan semua issues-nya"""
        self.stats['files_processed'] += 1
        
        if not os.path.exists(file_path):
            logger.warning(f"File tidak ditemukan: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_content = ''.join(lines)
            fixed_lines = lines.copy()
            fixes_applied = []
            
            # Sort issues by line number (descending) untuk menghindari pergeseran baris
            issues_sorted = sorted(issues, key=lambda x: x['line'], reverse=True)
            
            for issue in issues_sorted:
                line_idx = issue['line'] - 1
                
                if line_idx < 0 or line_idx >= len(fixed_lines):
                    logger.warning(f"Line number out of range: {issue['line']} di {file_path}")
                    self.stats['issues_skipped'] += 1
                    continue
                
                # Interactive mode
                if interactive:
                    print(f"\n[?] Fix issue ini?")
                    print(f"    File: {file_path}:{issue['line']}")
                    print(f"    Rule: {issue['id']} - {issue['kategori']}")
                    print(f"    Code: {issue['content'][:80]}")
                    response = input("    [y/N]: ").strip().lower()
                    if response != 'y':
                        self.stats['issues_skipped'] += 1
                        continue
                
                # Apply fix
                fix_func = self.fix_strategies.get(issue['id'])
                if fix_func:
                    result = fix_func(fixed_lines, line_idx, issue)
                    
                    if result['fixed']:
                        fixed_lines = result['lines']
                        fixes_applied.append({
                            'line': issue['line'],
                            'rule_id': issue['id'],
                            'kategori': issue['kategori'],
                            'description': result.get('description', 'Fixed')
                        })
                        self.stats['issues_fixed'] += 1
                        
                        # Update severity stats
                        severity = issue['severity']
                        self.stats['by_severity'][severity] = self.stats['by_severity'].get(severity, 0) + 1
                        
                        # Update category stats
                        kategori = issue['kategori']
                        self.stats['by_category'][kategori] = self.stats['by_category'].get(kategori, 0) + 1
                    else:
                        self.stats['issues_skipped'] += 1
                        if result.get('reason'):
                            logger.warning(f"Fix skipped: {result['reason']}")
            
            # Write back if changes were made
            if fixes_applied:
                new_content = ''.join(fixed_lines)
                
                if dry_run:
                    print(f"\n[DRY-RUN] Akan fix {len(fixes_applied)} issue di: {file_path}")
                    for fix in fixes_applied:
                        print(f"  • Baris {fix['line']}: [{fix['rule_id']}] {fix['description']}")
                else:
                    # Create backup
                    backup_path = self._create_backup(file_path)
                    self.stats['backups_created'] += 1
                    
                    # Write new content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    self.stats['files_fixed'] += 1
                    print(f"\n[✓] Fixed {len(fixes_applied)} issue di: {file_path}")
                    for fix in fixes_applied:
                        print(f"  • Baris {fix['line']}: [{fix['rule_id']}] {fix['description']}")
                    print(f"  💾 Backup: {backup_path}")
        
        except Exception as e:
            logger.exception(f"Error processing {file_path}: {e}")
    
    # =========================================================================
    # FIX STRATEGIES
    # =========================================================================
    
    def _fix_weak_crypto(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-009: Ganti md5/sha1 dengan password_hash"""
        line = lines[line_idx]
        
        # Pattern: $hash = md5($password);
        # Menjadi: $hash = password_hash($password, PASSWORD_BCRYPT);
        pattern = r'\b(md5|sha1)\s*\(\s*([^)]+)\)'
        
        def replace_func(match):
            func_name = match.group(1)
            arg = match.group(2).strip()
            return f"password_hash({arg}, PASSWORD_BCRYPT)"
        
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': f"Ganti {line.split('(')[0].strip()}() dengan password_hash()"
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_remove_debug_php(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-011: Hapus baris debug PHP (var_dump, print_r, dd, dump)"""
        line = lines[line_idx].strip()
        
        # Cek apakah baris hanya berisi debug function
        debug_pattern = r'^\s*(var_dump|print_r|debug_print_backtrace|dd|dump)\s*\(.*?\)\s*;?\s*$'
        
        if re.match(debug_pattern, line, re.IGNORECASE):
            lines[line_idx] = ''  # Hapus baris
            return {
                'fixed': True,
                'description': 'Hapus baris debug function'
            }
        
        # Jika debug function ada di tengah baris, coba hapus saja fungsinya
        line_content = lines[line_idx]
        new_line = re.sub(
            r'\b(var_dump|print_r|debug_print_backtrace|dd|dump)\s*\([^;]*\)\s*;?',
            '',
            line_content,
            flags=re.IGNORECASE
        )
        
        if new_line != line_content:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Hapus debug function dari baris'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_insecure_cookie(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-012: Tambahkan flag keamanan ke setcookie()"""
        line = lines[line_idx]
        
        # Cek apakah sudah ada flag keamanan
        if re.search(r'(secure|httponly|samesite)', line, re.IGNORECASE):
            return {'fixed': False, 'reason': 'Sudah ada flag keamanan'}
        
        # Pattern: setcookie("name", "value");
        # Menjadi: setcookie("name", "value", ["expires" => 0, "path" => "/", "secure" => true, "httponly" => true, "samesite" => "Strict"]);
        
        # Simple fix: tambahkan komentar warning
        if 'setcookie(' in line and line.rstrip().endswith(');'):
            new_line = line.rstrip()[:-2] + ', ["secure" => true, "httponly" => true, "samesite" => "Strict"]); // Auto-fixed: Added security flags\n'
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Tambahkan flag secure, httponly, samesite ke cookie'
            }
        
        return {'fixed': False, 'reason': 'Pattern setcookie tidak cocok'}
    
    def _fix_loose_comparison(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-019: Ganti == dengan === untuk perbandingan string kosong"""
        line = lines[line_idx]
        
        # Pattern: if ($var == '') atau if ($var == "")
        pattern = r'(\$\w+(?:->\w+)?)\s*==\s*([\'"]{2})'
        
        new_line = re.sub(pattern, r'\1 === \2', line)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Ganti == dengan === (strict comparison)'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_chmod_permission(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-020: Ganti permission 777 dengan 755 (directory) atau 644 (file)"""
        line = lines[line_idx]
        
        # Pattern: chmod($path, 0777) atau chmod($path, 777)
        pattern = r'(chmod\s*\([^,]+,\s*)0?(777)(\s*\))'
        
        def replace_func(match):
            prefix = match.group(1)
            suffix = match.group(3)
            # Default ke 755 untuk directory (bisa disesuaikan)
            return f"{prefix}0755{suffix}"
        
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Ganti permission 777 dengan 755'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_cors_wildcard(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-022: Ganti Access-Control-Allow-Origin: * dengan domain spesifik"""
        line = lines[line_idx]
        
        # Pattern: Access-Control-Allow-Origin: *
        pattern = r'(Access-Control-Allow-Origin\s*:\s*)\*'
        
        new_line = re.sub(
            pattern,
            r'\1https://yourdomain.com // TODO: Ganti dengan domain yang diizinkan',
            line,
            flags=re.IGNORECASE
        )
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Ganti wildcard CORS dengan domain spesifik (TODO: sesuaikan)'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_ssl_verify_false(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-023: Ganti SSL verification false ke true"""
        line = lines[line_idx]
        
        # Pattern 1: CURLOPT_SSL_VERIFYPEER => false
        pattern1 = r'(CURLOPT_SSL_VERIFYPEER\s*(?:=>|:)\s*)false'
        new_line = re.sub(pattern1, r'\1true', line, flags=re.IGNORECASE)
        
        # Pattern 2: verify = False (Python requests)
        pattern2 = r'(verify\s*=\s*)False'
        new_line = re.sub(pattern2, r'\1True', new_line, flags=re.IGNORECASE)
        
        # Pattern 3: verify=False
        pattern3 = r'(verify\s*=\s*)false'
        new_line = re.sub(pattern3, r'\1true', new_line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Aktifkan SSL verification'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_directory_listing(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-024: Ganti Options +Indexes dengan Options -Indexes"""
        line = lines[line_idx]
        
        # Pattern: Options +Indexes
        pattern = r'(Options\s+)\+Indexes'
        
        new_line = re.sub(pattern, r'\1-Indexes', line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Disable directory listing (+Indexes → -Indexes)'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_remove_console_log(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-025: Hapus console.log() dari JavaScript"""
        line = lines[line_idx].strip()
        
        # Cek apakah baris hanya berisi console.log
        console_pattern = r'^\s*console\.(log|debug|info|warn|error)\s*\(.*?\)\s*;?\s*$'
        
        if re.match(console_pattern, line, re.IGNORECASE):
            lines[line_idx] = ''  # Hapus baris
            return {
                'fixed': True,
                'description': 'Hapus baris console.log()'
            }
        
        # Jika console.log ada di tengah baris
        line_content = lines[line_idx]
        new_line = re.sub(
            r'console\.(log|debug|info|warn|error)\s*\([^;]*\)\s*;?',
            '',
            line_content,
            flags=re.IGNORECASE
        )
        
        if new_line != line_content:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Hapus console.log() dari baris'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_http_to_https(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-030: Ganti http:// dengan https://"""
        line = lines[line_idx]
        
        # Pattern: http:// (tapi bukan http://localhost atau http://127.0.0.1)
        pattern = r'(https?://)(?!localhost|127\.0\.0\.1|0\.0\.0\.0)'
        
        def replace_func(match):
            protocol = match.group(1)
            if protocol == 'http://':
                return 'https://'
            return protocol
        
        new_line = re.sub(pattern, replace_func, line)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': 'Ganti http:// dengan https://'
            }
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    # =========================================================================
    # BACKUP MANAGEMENT
    # =========================================================================
    
    def _create_backup(self, file_path: str) -> str:
        """Buat backup file dengan timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        
        # Buat subfolder berdasarkan tanggal
        date_folder = datetime.now().strftime("%Y-%m-%d")
        backup_subdir = os.path.join(self.backup_dir, date_folder)
        os.makedirs(backup_subdir, exist_ok=True)
        
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(backup_subdir, backup_name)
        
        shutil.copy(file_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        
        return backup_path
    
    def rollback(self, backup_path: str, original_path: str) -> bool:
        """Rollback file dari backup"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup tidak ditemukan: {backup_path}")
                return False
            
            shutil.copy(backup_path, original_path)
            logger.info(f"Rollback berhasil: {original_path} ← {backup_path}")
            return True
        except Exception as e:
            logger.exception(f"Error saat rollback: {e}")
            return False
    
    # =========================================================================
    # STATISTICS & REPORTING
    # =========================================================================
    
    def print_summary(self):
        """Cetak ringkasan statistik"""
        print(f"\n{'='*70}")
        print(f"{'RINGKASAN AUTO-FIX':^70}")
        print(f"{'='*70}")
        print(f"Files diproses       : {self.stats['files_processed']}")
        print(f"Files diperbaiki     : {self.stats['files_fixed']}")
        print(f"Issues ditemukan     : {self.stats['issues_found']}")
        print(f"Issues diperbaiki    : {self.stats['issues_fixed']}")
        print(f"Issues dilewati      : {self.stats['issues_skipped']}")
        print(f"Backups dibuat       : {self.stats['backups_created']}")
        
        if self.stats.get('dry_run'):
            print(f"\n⚠️  MODE DRY-RUN: Tidak ada file yang benar-benar diubah!")
        
        if self.stats['by_severity']:
            print(f"\nBerdasarkan Severity:")
            for severity, count in self.stats['by_severity'].items():
                if count > 0:
                    print(f"  {severity:10s}: {count}")
        
        if self.stats['by_category']:
            print(f"\nBerdasarkan Kategori:")
            for kategori, count in sorted(self.stats['by_category'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {kategori[:40]:40s}: {count}")
        
        print(f"{'='*70}")
    
    def export_stats(self, output_file: str = "output/fix_stats.json"):
        """Export statistik ke JSON"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Statistik fix disimpan: {output_file}")
        return output_file