import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Callable, Optional
from logger import get_logger

logger = get_logger("scanner")


class SecurityScanner:
    def __init__(self, rules_file: str = "rules.json"):
        """Initialize scanner dengan rules dari JSON"""
        logger.debug(f"Initializing scanner with rules: {rules_file}")
        self.rules = self._load_rules(rules_file)
        
        # Konfigurasi folder yang diabaikan
        self.ignored_dirs = {
            '.git', 'vendor', 'node_modules', 'storage', 'tests', '__pycache__',
            '.idea', '.vscode', 'venv', 'env', '.venv', 'virtualenv', 'pipenv',
            'site-packages', '.next', 'dist', 'build', 'output', 'logs', 'backups', 'uploads'
        }
        
        # File yang diabaikan
        self.ignored_files = {
            'security_analyzer.py', 'deep_project_analyzer.py', 
            '.env', '.env.example', 'package-lock.json'
        }
        
        # Ekstensi yang di-scan
        self.allowed_extensions = {
            '.php', '.js', '.py', '.html', '.twig', '.blade.php', 
            '.java', '.rb', '.jsx', '.tsx', '.vue'
        }
    
    def _load_rules(self, rules_file: str) -> List[Dict]:
        """Load dan compile aturan dari JSON"""
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('rules', [])
                
                # Compile regex untuk performa
                for rule in rules:
                    rule['compiled_pattern'] = re.compile(rule['pattern'])
                
                logger.info(f"Berhasil load {len(rules)} rules")
                return rules
        except FileNotFoundError:
            logger.error(f"File rules tidak ditemukan: {rules_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON di {rules_file}: {e}")
            return []
        except Exception as e:
            logger.exception(f"Gagal load rules dari {rules_file}: {e}")
            return []
    
    def scan_directory(self, root_dir: str, progress_callback: Optional[Callable] = None) -> Tuple[List[Dict], int]:
        """
        Scan seluruh direktori secara rekursif
        
        Args:
            root_dir: Path direktori yang akan di-scan
            progress_callback: Fungsi callback untuk update progress (file_count, current_file)
        
        Returns:
            Tuple[List[Dict], int]: (list of issues, total files scanned)
        """
        logger.info(f"Memulai scan directory: {root_dir}")
        
        all_issues = []
        total_files = 0
        
        try:
            for root, dirs, files in os.walk(root_dir):
                # Filter ignored directories (modifikasi in-place)
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
                
                for file in files:
                    # Skip ignored files
                    if file in self.ignored_files:
                        continue
                    
                    # Check extension
                    ext = Path(file).suffix.lower()
                    if file.endswith('.blade.php'):
                        ext = '.blade.php'
                    
                    if ext in self.allowed_extensions:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, root_dir)
                        total_files += 1
                        
                        # Progress callback
                        if progress_callback:
                            progress_callback(total_files, relative_path)
                        
                        # Scan file
                        issues = self.scan_file(file_path)
                        
                        # Tambahkan info file ke setiap issue
                        for issue in issues:
                            issue['file'] = relative_path
                            all_issues.append(issue)
            
            logger.info(f"Scan selesai. Total files: {total_files}, Total issues: {len(all_issues)}")
            return all_issues, total_files
            
        except PermissionError as e:
            logger.error(f"Permission denied saat scan directory: {e}")
            return all_issues, total_files
        except Exception as e:
            logger.exception(f"Error tidak terduga saat scan directory: {e}")
            return all_issues, total_files
    
    def scan_file(self, file_path: str) -> List[Dict]:
        """
        Scan satu file untuk mendeteksi issues
        
        Args:
            file_path: Path file yang akan di-scan
        
        Returns:
            List[Dict]: List of issues ditemukan
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line_content in enumerate(f, 1):
                    cleaned_line = line_content.strip()
                    
                    # Skip empty lines
                    if not cleaned_line:
                        continue
                    
                    # BONUS: Skip jika ada @nosec comment
                    if '@nosec' in cleaned_line or '# nosec' in cleaned_line:
                        continue
                    
                    # Skip full-line comments
                    if re.match(r'^\s*(//|#|/\*|\*)', cleaned_line):
                        continue
                    
                    # Check against all rules
                    for rule in self.rules:
                        if rule['compiled_pattern'].search(line_content):
                            issues.append({
                                'id': rule['id'],
                                'severity': rule['severity'],
                                'kategori': rule['kategori'],
                                'line': line_num,
                                'content': cleaned_line[:120] + ('...' if len(cleaned_line) > 120 else ''),
                                'info': rule['info'],
                                'solusi': rule['solusi'],
                                'auto_fixable': rule.get('auto_fixable', False)
                            })
        
        except UnicodeDecodeError as e:
            logger.warning(f"Encoding error di {file_path}: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied: {file_path}")
        except FileNotFoundError:
            logger.warning(f"File tidak ditemukan: {file_path}")
        except Exception as e:
            logger.exception(f"Error membaca {file_path}: {e}")
        
        return issues
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik scanner"""
        return {
            'total_rules': len(self.rules),
            'ignored_dirs': len(self.ignored_dirs),
            'ignored_files': len(self.ignored_files),
            'allowed_extensions': len(self.allowed_extensions)
        }