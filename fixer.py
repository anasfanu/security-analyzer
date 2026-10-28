import os
import re
import json
import shutil
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
from logger import get_logger

logger = get_logger("fixer")


class AutoFixer:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        # Registry strategi fix (Level 1 + Level 2)
        self.fix_strategies = {
            # Level 1 - Deterministic Fix
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
            
            # Level 2 - Context-Aware Fix (BARU)
            'SEC-003': self._fix_xss_output,
            'SEC-010': self._fix_insecure_random,
            'SEC-013': self._fix_missing_security_headers,
            'SEC-017': self._fix_information_disclosure,
            'SEC-026': self._fix_js_eval,
            'SEC-027': self._fix_innerhtml_xss,
            'SEC-028': self._fix_document_write,
            'SEC-029': self._fix_localstorage_sensitive,
            
            # SEC-001 - Special Logic (Hardcoded Credentials)
            'SEC-001': self._fix_hardcoded_credentials,
        }
        
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'issues_skipped': 0,
            'backups_created': 0,
            'env_file_created': False,
            'credentials_migrated': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_category': {}
        }
    
    def fix_from_report(self, report_file: str, root_dir: str, 
                       dry_run: bool = False, interactive: bool = False) -> Dict:
        logger.info(f"Memulai auto-fix dari: {report_file} (dry_run={dry_run})")
        
        self.stats = {
            'files_processed': 0, 'files_fixed': 0, 'issues_found': 0,
            'issues_fixed': 0, 'issues_skipped': 0, 'backups_created': 0,
            'env_file_created': False, 'credentials_migrated': 0,
            'by_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_category': {}, 'dry_run': dry_run
        }
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
        except Exception as e:
            logger.error(f"Gagal membaca report: {e}")
            return self.stats
        
        issues = report.get('issues', [])
        self.stats['issues_found'] = len(issues)
        
        fixable_issues = [i for i in issues if i['id'] in self.fix_strategies]
        unfixable_issues = [i for i in issues if i['id'] not in self.fix_strategies]
        
        logger.info(f"Total: {len(issues)}, Fixable: {len(fixable_issues)}, Unfixable: {len(unfixable_issues)}")
        
        if not fixable_issues:
            print("\n[!] Tidak ada masalah yang bisa di-fix otomatis.")
            if unfixable_issues:
                print(f"[i] {len(unfixable_issues)} masalah memerlukan perbaikan manual.")
            return self.stats
        
        if unfixable_issues:
            print(f"\n{'='*70}\n⚠️  {len(unfixable_issues)} masalah TIDAK BISA di-fix otomatis:\n{'='*70}")
            unfixable_by_id = {}
            for issue in unfixable_issues:
                rule_id = issue['id']
                if rule_id not in unfixable_by_id:
                    unfixable_by_id[rule_id] = {'kategori': issue['kategori'], 'count': 0, 'severity': issue['severity']}
                unfixable_by_id[rule_id]['count'] += 1
            
            for rule_id, info in unfixable_by_id.items():
                print(f"  [{info['severity']}] {rule_id} - {info['kategori']} ({info['count']}x)")
            print(f"{'='*70}\n")
            print("📖 Lihat MANUAL_FIXES.md untuk panduan perbaikan manual.\n")
        
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
            self._process_file(file_path, file_issues, dry_run, interactive, root_dir)
        
        return self.stats
    
    def _process_file(self, file_path: str, issues: List[Dict], dry_run: bool, 
                     interactive: bool, root_dir: str):
        self.stats['files_processed'] += 1
        
        if not os.path.exists(file_path):
            logger.warning(f"File tidak ditemukan: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixed_lines = lines.copy()
            fixes_applied = []
            issues_sorted = sorted(issues, key=lambda x: x['line'], reverse=True)
            
            for issue in issues_sorted:
                line_idx = issue['line'] - 1
                
                if line_idx < 0 or line_idx >= len(fixed_lines):
                    logger.warning(f"Line number out of range: {issue['line']} di {file_path}")
                    self.stats['issues_skipped'] += 1
                    continue
                
                if interactive:
                    print(f"\n[?] Fix issue ini?\n    File: {file_path}:{issue['line']}\n    Rule: {issue['id']} - {issue['kategori']}\n    Code: {issue['content'][:80]}")
                    response = input("    [y/N]: ").strip().lower()
                    if response != 'y':
                        self.stats['issues_skipped'] += 1
                        continue
                
                fix_func = self.fix_strategies.get(issue['id'])
                if fix_func:
                    # Special handling untuk SEC-001 (butuh root_dir untuk .env)
                    if issue['id'] == 'SEC-001':
                        result = fix_func(fixed_lines, line_idx, issue, root_dir, dry_run)
                    else:
                        result = fix_func(fixed_lines, line_idx, issue)
                    
                    if result['fixed']:
                        fixed_lines = result['lines']
                        fixes_applied.append({
                            'line': issue['line'], 
                            'rule_id': issue['id'], 
                            'description': result.get('description', 'Fixed')
                        })
                        self.stats['issues_fixed'] += 1
                        self.stats['by_severity'][issue['severity']] = self.stats['by_severity'].get(issue['severity'], 0) + 1
                        self.stats['by_category'][issue['kategori']] = self.stats['by_category'].get(issue['kategori'], 0) + 1
                        
                        # Track SEC-001 special stats
                        if issue['id'] == 'SEC-001':
                            if result.get('env_created'):
                                self.stats['env_file_created'] = True
                            self.stats['credentials_migrated'] += result.get('migrated_count', 0)
                    else:
                        self.stats['issues_skipped'] += 1
            
            if fixes_applied:
                new_content = ''.join(fixed_lines)
                if dry_run:
                    print(f"\n[DRY-RUN] Akan fix {len(fixes_applied)} issue di: {file_path}")
                    for fix in fixes_applied:
                        print(f"  • Baris {fix['line']}: [{fix['rule_id']}] {fix['description']}")
                else:
                    backup_path = self._create_backup(file_path)
                    self.stats['backups_created'] += 1
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
    # LEVEL 1 - DETERMINISTIC FIX (Sudah ada, tidak diubah)
    # =========================================================================
    
    def _fix_weak_crypto(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        pattern = r'\b(md5|sha1)\s*\(\s*([^)]+)\)'
        def replace_func(match):
            return f"password_hash({match.group(2).strip()}, PASSWORD_BCRYPT)"
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Ganti md5/sha1() dengan password_hash()'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_remove_debug_php(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx].strip()
        debug_pattern = r'^\s*(var_dump|print_r|debug_print_backtrace|dd)\s*\(.*?\)\s*;?\s*$'
        if re.match(debug_pattern, line, re.IGNORECASE):
            lines[line_idx] = ''
            return {'fixed': True, 'description': 'Hapus baris debug function'}
        
        line_content = lines[line_idx]
        new_line = re.sub(r'\b(var_dump|print_r|debug_print_backtrace|dd)\s*\([^;]*\)\s*;?', '', line_content, flags=re.IGNORECASE)
        if new_line != line_content:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Hapus debug function dari baris'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_insecure_cookie(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        if re.search(r'(secure|httponly|samesite)', line, re.IGNORECASE):
            return {'fixed': False, 'reason': 'Sudah ada flag keamanan'}
        if 'setcookie(' in line and line.rstrip().endswith(');'):
            lines[line_idx] = line.rstrip()[:-2] + ', ["secure" => true, "httponly" => true, "samesite" => "Strict"]); // Auto-fixed\n'
            return {'fixed': True, 'description': 'Tambahkan flag keamanan ke cookie'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_loose_comparison(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        pattern = r'(\$\w+(?:->\w+)?)\s*==\s*([\'"]{2})'
        new_line = re.sub(pattern, r'\1 === \2', line)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Ganti == dengan === (strict comparison)'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_chmod_permission(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        pattern = r'(chmod\s*\([^,]+,\s*)0?(777)(\s*\))'
        def replace_func(match):
            return f"{match.group(1)}0755{match.group(3)}"
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Ganti permission 777 dengan 755'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_cors_wildcard(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        pattern = r'(Access-Control-Allow-Origin\s*:\s*)\*'
        new_line = re.sub(pattern, r'\1https://yourdomain.com // TODO: Ganti dengan domain yang diizinkan', line, flags=re.IGNORECASE)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Ganti wildcard CORS dengan domain spesifik'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_ssl_verify_false(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        new_line = re.sub(r'(CURLOPT_SSL_VERIFYPEER\s*(?:=>|:)\s*)false', r'\1true', line, flags=re.IGNORECASE)
        new_line = re.sub(r'(verify\s*=\s*)False', r'\1True', new_line, flags=re.IGNORECASE)
        new_line = re.sub(r'(verify\s*=\s*)false', r'\1true', new_line, flags=re.IGNORECASE)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Aktifkan SSL verification'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_directory_listing(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        pattern = r'(Options\s+)\+Indexes'
        new_line = re.sub(pattern, r'\1-Indexes', line, flags=re.IGNORECASE)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Disable directory listing (+Indexes → -Indexes)'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_remove_console_log(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx].strip()
        console_pattern = r'^\s*console\.(log|debug|info|warn|error)\s*\(.*?\)\s*;?\s*$'
        if re.match(console_pattern, line, re.IGNORECASE):
            lines[line_idx] = ''
            return {'fixed': True, 'description': 'Hapus baris console.log()'}
        
        line_content = lines[line_idx]
        new_line = re.sub(r'console\.(log|debug|info|warn|error)\s*\([^;]*\)\s*;?', '', line_content, flags=re.IGNORECASE)
        if new_line != line_content:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Hapus console.log() dari baris'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_http_to_https(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        line = lines[line_idx]
        pattern = r'(https?://)(?!localhost|127\.0\.0\.1|0\.0\.0\.0)'
        def replace_func(match):
            return 'https://' if match.group(1) == 'http://' else match.group(1)
        new_line = re.sub(pattern, replace_func, line)
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Ganti http:// dengan https://'}
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    # =========================================================================
    # LEVEL 2 - CONTEXT-AWARE FIX (BARU)
    # =========================================================================
    
    def _fix_xss_output(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-003: Wrap output dengan htmlspecialchars jika belum di-sanitize"""
        line = lines[line_idx]
        
        # Cek apakah sudah ada sanitasi di baris ini
        if re.search(r'(htmlspecialchars|e\(|clean\(|sanitize)', line, re.IGNORECASE):
            return {'fixed': False, 'reason': 'Sudah ada sanitasi'}
        
        # Cek 3 baris sebelumnya untuk sanitasi
        start_idx = max(0, line_idx - 3)
        context = ''.join(lines[start_idx:line_idx + 1])
        if re.search(r'(htmlspecialchars|e\(|clean\(|sanitize)', context, re.IGNORECASE):
            return {'fixed': False, 'reason': 'Variabel sudah di-sanitize di baris sebelumnya'}
        
        # Pattern: echo $variable;
        pattern = r'(echo\s+)(\$[\w\->]+)(\s*;)'
        
        def replace_func(match):
            prefix = match.group(1)
            variable = match.group(2)
            suffix = match.group(3)
            return f"{prefix}htmlspecialchars({variable}, ENT_QUOTES, 'UTF-8'){suffix}"
        
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Wrap output dengan htmlspecialchars()'}
        
        return {'fixed': False, 'reason': 'Pattern echo tidak cocok'}
    
    def _fix_insecure_random(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-010: Ganti rand/mt_rand dengan random_int"""
        line = lines[line_idx]
        
        # Pattern: rand($min, $max) atau mt_rand($min, $max)
        pattern = r'\b(rand|mt_rand)\s*\(\s*([^,]+),\s*([^)]+)\)'
        
        def replace_func(match):
            min_val = match.group(2).strip()
            max_val = match.group(3).strip()
            return f"random_int({min_val}, {max_val})"
        
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Ganti rand()/mt_rand() dengan random_int()'}
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_missing_security_headers(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-013: Inject security headers jika belum ada"""
        line = lines[line_idx]
        
        # Cek apakah ini di awal file PHP
        if '<?php' in ''.join(lines[:line_idx + 1]):
            # Cek apakah security headers sudah ada
            full_content = ''.join(lines)
            if 'X-Frame-Options' in full_content:
                return {'fixed': False, 'reason': 'Security headers sudah ada'}
            
            # Inject security headers setelah <?php
            if '<?php' in line:
                header_block = """
// Security Headers - Auto-added
header('X-Frame-Options: DENY');
header('X-Content-Type-Options: nosniff');
header('X-XSS-Protection: 1; mode=block');
header('Referrer-Policy: strict-origin-when-cross-origin');
"""
                lines.insert(line_idx + 1, header_block)
                return {'fixed': True, 'description': 'Inject security headers'}
        
        return {'fixed': False, 'reason': 'Bukan di awal file PHP'}
    
    def _fix_information_disclosure(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-017: Disable display_errors"""
        line = lines[line_idx]
        
        # Pattern: display_errors = 1 atau display_errors = On
        pattern = r'(display_errors\s*=\s*)(1|On|true)'
        
        def replace_func(match):
            return f"{match.group(1)}0 // Auto-fixed: disabled for production"
        
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Disable display_errors'}
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_js_eval(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-026: Comment out eval() dengan TODO marker"""
        line = lines[line_idx]
        
        # Comment out baris eval
        if 'eval(' in line and not line.strip().startswith('//'):
            lines[line_idx] = f"// TODO: SECURITY - eval() removed. Refactor this logic.\n// {line}"
            return {'fixed': True, 'description': 'Comment out eval() dengan TODO marker'}
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_innerhtml_xss(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-027: Convert innerHTML ke textContent jika memungkinkan"""
        line = lines[line_idx]
        
        # Pattern: element.innerHTML = variable;
        pattern = r'(\w+)\.innerHTML\s*=\s*(\$\w+|\w+)\s*;'
        
        def replace_func(match):
            element = match.group(1)
            variable = match.group(2)
            return f"{element}.textContent = {variable}; // Auto-fixed: innerHTML → textContent"
        
        new_line = re.sub(pattern, replace_func, line, flags=re.IGNORECASE)
        
        if new_line != line:
            lines[line_idx] = new_line
            return {'fixed': True, 'description': 'Convert innerHTML ke textContent'}
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok atau terlalu kompleks'}
    
    def _fix_document_write(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-028: Comment out document.write() dengan TODO"""
        line = lines[line_idx]
        
        if 'document.write(' in line and not line.strip().startswith('//'):
            lines[line_idx] = f"// TODO: SECURITY - document.write() removed. Use DOM manipulation.\n// {line}"
            return {'fixed': True, 'description': 'Comment out document.write() dengan TODO'}
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    def _fix_localstorage_sensitive(self, lines: List[str], line_idx: int, issue: Dict) -> Dict:
        """SEC-029: Comment out localStorage.setItem dengan migration note"""
        line = lines[line_idx]
        
        # Pattern: localStorage.setItem('token', ...)
        pattern = r'localStorage\.setItem\s*\(\s*[\'"](token|password|secret|key)[\'"]'
        
        if re.search(pattern, line, re.IGNORECASE) and not line.strip().startswith('//'):
            lines[line_idx] = f"// TODO: SECURITY - Migrate to httpOnly cookie\n// {line}"
            return {'fixed': True, 'description': 'Comment out localStorage sensitive data'}
        
        return {'fixed': False, 'reason': 'Pattern tidak cocok'}
    
    # =========================================================================
    # SEC-001 - SPECIAL LOGIC (Hardcoded Credentials Migration)
    # =========================================================================
    
    def _fix_hardcoded_credentials(self, lines: List[str], line_idx: int, 
                                   issue: Dict, root_dir: str, dry_run: bool) -> Dict:
        """SEC-001: Migrate hardcoded credentials ke .env file (hanya jika .env sudah ada)"""
        line = lines[line_idx]
        
        # Pattern: $password = "secret123"; atau $api_key = 'abc123';
        pattern = r'(\$\w+)\s*=\s*[\'"]([^\'"]{4,})[\'"]\s*;'
        
        match = re.search(pattern, line, re.IGNORECASE)
        if not match:
            return {'fixed': False, 'reason': 'Pattern credential tidak cocok'}
        
        var_name = match.group(1)  # e.g., $password
        cred_value = match.group(2)  # e.g., secret123
        
        # Convert variable name to env variable name
        # $password → PASSWORD, $api_key → API_KEY
        env_var_name = var_name.lstrip('$').upper()
        
        # Cek keberadaan file .env di root directory
        env_file_path = os.path.join(root_dir, '.env')
        
        # JIKA .ENV TIDAK ADA: Berhenti dan beri saran manual
        if not os.path.exists(env_file_path):
            return {
                'fixed': False,
                'reason': (
                    f"File .env tidak ditemukan di '{root_dir}'. "
                    f"Silakan buat file '.env' secara manual di folder tersebut, "
                    f"tambahkan baris '{env_var_name}={cred_value}', "
                    f"lalu jalankan auto-fix kembali."
                )
            }
        
        # JIKA .ENV SUDAH ADA: Lanjutkan migrasi
        with open(env_file_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Cek apakah variabel sudah ada di .env untuk menghindari duplikasi
        if f"{env_var_name}=" not in env_content:
            if not dry_run:
                # Ambil informasi asal file dan baris dari issue
                source_file = issue.get('file', 'unknown_file')
                source_line = issue.get('line', 'unknown_line')
                
                # Mode 'a' (append) secara otomatis menaruh data di PALING BAWAH file
                with open(env_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n# Dipindahkan dari {source_file} baris {source_line} oleh Security Analyzer\n")
                    f.write(f"{env_var_name}={cred_value}\n")
                
                logger.info(f"Appended {env_var_name} to .env (from {source_file}:{source_line})")
        
        # Ganti kode di file asli dengan getenv()
        # $password = "secret123"; → $password = getenv('PASSWORD') ?: 'secret123';
        new_line = re.sub(
            pattern,
            lambda m: f"{m.group(1)} = getenv('{env_var_name}') ?: '{m.group(2)}'; // Auto-migrated to .env",
            line,
            flags=re.IGNORECASE
        )
        
        if new_line != line:
            lines[line_idx] = new_line
            return {
                'fixed': True,
                'description': f'Migrate {var_name} ke .env ({env_var_name})',
                'env_created': False,
                'migrated_count': 1
            }
        
        return {'fixed': False, 'reason': 'Gagal replace credential di kode'}
    
    # =========================================================================
    # BACKUP & STATISTICS
    # =========================================================================
    
    def _create_backup(self, file_path: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        date_folder = datetime.now().strftime("%Y-%m-%d")
        backup_subdir = os.path.join(self.backup_dir, date_folder)
        os.makedirs(backup_subdir, exist_ok=True)
        backup_path = os.path.join(backup_subdir, f"{filename}.{timestamp}.bak")
        shutil.copy(file_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def print_summary(self):
        print(f"\n{'='*70}\n{'RINGKASAN AUTO-FIX':^70}\n{'='*70}")
        print(f"Files diproses       : {self.stats['files_processed']}")
        print(f"Files diperbaiki     : {self.stats['files_fixed']}")
        print(f"Issues ditemukan     : {self.stats['issues_found']}")
        print(f"Issues diperbaiki    : {self.stats['issues_fixed']}")
        print(f"Issues dilewati      : {self.stats['issues_skipped']}")
        print(f"Backups dibuat       : {self.stats['backups_created']}")
        
        # SEC-001 special stats
        if self.stats['env_file_created']:
            print(f"\n🔐 File .env BARU telah dibuat!")
            print(f"   ⚠️  PENTING: Pastikan .env ada di .gitignore!")
        if self.stats['credentials_migrated'] > 0:
            print(f"   Credentials migrated: {self.stats['credentials_migrated']}")
        
        if self.stats.get('dry_run'):
            print(f"\n⚠️  MODE DRY-RUN: Tidak ada file yang benar-benar diubah!")
        
        if self.stats['by_severity']:
            print(f"\nBerdasarkan Severity:")
            for severity, count in self.stats['by_severity'].items():
                if count > 0: print(f"  {severity:10s}: {count}")
        
        if self.stats['by_category']:
            print(f"\nBerdasarkan Kategori:")
            for kategori, count in sorted(self.stats['by_category'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {kategori[:40]:40s}: {count}")
        
        print(f"{'='*70}")
    
    def export_stats(self, output_file: str = "output/fix_stats.json"):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        logger.info(f"Statistik fix disimpan: {output_file}")
        return output_file