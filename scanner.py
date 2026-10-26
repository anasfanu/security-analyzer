import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
from logger import get_logger

logger = get_logger("scanner")

class SecurityScanner:
    def __init__(self, rules_file: str = "rules.json"):
        logger.debug(f"Initializing scanner with rules: {rules_file}")
        self.rules = self._load_rules(rules_file)
        # ... sisa kode tetap sama
    
    def _load_rules(self, rules_file: str) -> List[Dict]:
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('rules', [])
                
                for rule in rules:
                    rule['compiled_pattern'] = re.compile(rule['pattern'])
                
                logger.info(f"Berhasil load {len(rules)} rules")
                return rules
        except Exception as e:
            logger.exception(f"Gagal load rules dari {rules_file}: {e}")
            return []
    
    def scan_file(self, file_path: str) -> List[Dict]:
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line_content in enumerate(f, 1):
                    # ... (kode scan tetap sama)
                    pass
        except UnicodeDecodeError as e:
            logger.warning(f"Encoding error di {file_path}: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied: {file_path}")
        except Exception as e:
            logger.exception(f"Error membaca {file_path}: {e}")
        
        return issues