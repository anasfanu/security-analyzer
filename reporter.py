import json
import os
from datetime import datetime
from typing import List, Dict

# ANSI Colors
COLORS = {
    'GREEN': "\033[92m",
    'YELLOW': "\033[93m",
    'RED': "\033[91m",
    'BLUE': "\033[94m",
    'CYAN': "\033[96m",
    'MAGENTA': "\033[95m",
    'RESET': "\033[0m"
}

class Reporter:
    @staticmethod
    def console_report(issues: List[Dict], total_files: int):
        """Output ke terminal dengan warna"""
        if not issues:
            print(f"\n{COLORS['GREEN']}[✓] 0 Masalah. Proyek Anda Bersih & Aman!{COLORS['RESET']}")
            return
        
        print(f"\n{COLORS['BLUE']}{'='*70}")
        print(f"{'HASIL PEMINDAIAN KEAMANAN':^70}")
        print(f"{'='*70}{COLORS['RESET']}\n")
        
        # Group by file
        issues_by_file = {}
        for issue in issues:
            file = issue['file']
            if file not in issues_by_file:
                issues_by_file[file] = []
            issues_by_file[file].append(issue)
        
        for file, file_issues in issues_by_file.items():
            print(f"{COLORS['RED']}[✗] FILE: {file}{COLORS['RESET']}")
            
            for issue in file_issues:
                sev_color = COLORS['RED'] if issue['severity'] == 'CRITICAL' else (
                    COLORS['YELLOW'] if issue['severity'] == 'HIGH' else COLORS['CYAN']
                )
                
                print(f"  {sev_color}[{issue['severity']}]{COLORS['RESET']} "
                      f"{COLORS['CYAN']}Baris {issue['line']:4d}:{COLORS['RESET']} {issue['content']}")
                print(f"    {COLORS['MAGENTA']}[{issue['id']}] Kategori:{COLORS['RESET']} {issue['kategori']}")
                print(f"    {COLORS['YELLOW']}Info    :{COLORS['RESET']} {issue['info']}")
                print(f"    {COLORS['GREEN']}Solusi  :{COLORS['RESET']} {issue['solusi']}")
                print("-" * 70)
        
        # Summary
        critical_count = sum(1 for i in issues if i['severity'] == 'CRITICAL')
        print(f"\n{COLORS['BLUE']}{'='*70}")
        print(f"{'RINGKASAN':^70}")
        print(f"{'='*70}{COLORS['RESET']}")
        print(f"Total File Diperiksa : {total_files}")
        print(f"Total Masalah        : {len(issues)}")
        
        if critical_count > 0:
            print(f"Celaha CRITICAL      : {COLORS['RED']}{critical_count} Ditemukan!{COLORS['RESET']}")
    
    @staticmethod
    def export_json(issues: List[Dict], total_files: int, output_dir: str = "output"):
        """Export ke JSON"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_report_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        report = {
            'scan_date': datetime.now().isoformat(),
            'total_files': total_files,
            'total_issues': len(issues),
            'critical_count': sum(1 for i in issues if i['severity'] == 'CRITICAL'),
            'issues': issues
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{COLORS['GREEN']}[✓] Laporan JSON disimpan: {filepath}{COLORS['RESET']}")
        return filepath
    
    @staticmethod
    def export_html(issues: List[Dict], total_files: int, output_dir: str = "output"):
        """Export ke HTML"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_report_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)
        
        html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laporan Keamanan - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .issue {{ background: #fff; border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0; border-radius: 4px; }}
        .issue.CRITICAL {{ border-left-color: #c0392b; }}
        .issue.HIGH {{ border-left-color: #e67e22; }}
        .issue.MEDIUM {{ border-left-color: #f39c12; }}
        .issue.LOW {{ border-left-color: #3498db; }}
        .severity {{ display: inline-block; padding: 4px 12px; border-radius: 3px; color: white; font-weight: bold; font-size: 12px; }}
        .severity.CRITICAL {{ background: #c0392b; }}
        .severity.HIGH {{ background: #e67e22; }}
        .severity.MEDIUM {{ background: #f39c12; }}
        .severity.LOW {{ background: #3498db; }}
        .file-path {{ font-family: monospace; color: #7f8c8d; font-size: 14px; }}
        .code {{ background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 3px; font-family: 'Courier New', monospace; font-size: 13px; overflow-x: auto; }}
        .info-label {{ font-weight: bold; color: #34495e; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Laporan Pemindaian Keamanan</h1>
        <p><strong>Tanggal Scan:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <h2>📊 Ringkasan</h2>
            <p><strong>Total File Diperiksa:</strong> {total_files}</p>
            <p><strong>Total Masalah Ditemukan:</strong> {len(issues)}</p>
            <p><strong>Celaha CRITICAL:</strong> <span style="color: #c0392b; font-weight: bold;">{sum(1 for i in issues if i['severity'] == 'CRITICAL')}</span></p>
        </div>
        
        <h2>🚨 Detail Masalah</h2>
"""
        
        for issue in issues:
            html_content += f"""
        <div class="issue {issue['severity']}">
            <span class="severity {issue['severity']}">{issue['severity']}</span>
            <span class="file-path">{issue['file']} : Baris {issue['line']}</span>
            <h3>[{issue['id']}] {issue['kategori']}</h3>
            <div class="code">{issue['content']}</div>
            <p><span class="info-label">ℹ️ Informasi:</span> {issue['info']}</p>
            <p><span class="info-label">✅ Solusi:</span> {issue['solusi']}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"{COLORS['GREEN']}[✓] Laporan HTML disimpan: {filepath}{COLORS['RESET']}")
        return filepath