import argparse
import sys
import os
from scanner import SecurityScanner
from reporter import Reporter
from fixer import AutoFixer
from logger import setup_logger, get_logger, setup_global_exception_handler, view_logs

# Setup global exception handler (menangkap SEMUA error)
setup_global_exception_handler()

# Setup logger
logger = setup_logger()


def main():
    parser = argparse.ArgumentParser(
        description="🔒 Deep Project Security & Bug Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py /path/to/project
  python main.py /path/to/project --export json
  python main.py /path/to/project --export html
  python main.py --fix output/scan_report_20261027_120000.json
  python main.py --view-logs app
  python main.py --view-logs error
        """
    )
    
    parser.add_argument("target_dir", nargs="?", default=".", help="Direktori target")
    parser.add_argument("--export", choices=['json', 'html', 'both'], help="Export laporan")
    parser.add_argument("--fix", metavar="REPORT_FILE", help="Auto-fix berdasarkan laporan")
    parser.add_argument("--view-logs", metavar="LOG_TYPE", 
                       help="Lihat log (app/error)")
    parser.add_argument("--log-lines", type=int, default=50,
                       help="Jumlah baris log yang ditampilkan (default: 50)")
    
    args = parser.parse_args()
    
    # =========================================================================
    # Mode: Lihat Log
    # =========================================================================
    if args.view_logs:
        view_logs(args.view_logs, args.log_lines)
        sys.exit(0)
    
    # =========================================================================
    # Mode: Auto-Fix
    # =========================================================================
    if args.fix:
        try:
            if not os.path.exists(args.fix):
                logger.error(f"File laporan tidak ditemukan: {args.fix}")
                sys.exit(1)
            
            logger.info(f"Memulai Auto-Fix dari: {args.fix}")
            fixer = AutoFixer()
            stats = fixer.fix_from_report(args.fix, ".")
            
            logger.info(f"Auto-Fix selesai: {stats}")
            print(f"\n{'='*70}")
            print(f"✅ Auto-Fix Selesai!")
            print(f"   Files diperbaiki: {stats['files_fixed']}")
            print(f"   Issues diperbaiki: {stats['issues_fixed']}")
            print(f"{'='*70}")
            sys.exit(0)
            
        except Exception as e:
            logger.exception(f"Gagal melakukan auto-fix: {e}")
            sys.exit(1)
    
    # =========================================================================
    # Mode: Scan
    # =========================================================================
    try:
        target_dir = os.path.abspath(args.target_dir)
        
        if not os.path.isdir(target_dir):
            logger.error(f"Direktori tidak ditemukan: {target_dir}")
            sys.exit(1)
        
        logger.info(f"Memulai scan di: {target_dir}")
        
        print(f"\n{'='*70}")
        print(f"🔒 DEEP PROJECT SECURITY & BUG ANALYZER")
        print(f"{'='*70}")
        print(f"[*] Target: {target_dir}")
        print(f"[*] Log disimpan di: logs/\n")
        
        # Initialize scanner
        scanner = SecurityScanner()
        
        # Progress callback
        def progress_callback(file_count, current_file):
            print(f"\r[*] Scanning... File #{file_count}: {current_file[:50]}{'...' if len(current_file) > 50 else ''}", 
                  end='', flush=True)
        
        # Scan
        issues, total_files = scanner.scan_directory(target_dir, progress_callback)
        print("\n")
        
        # Report
        Reporter.console_report(issues, total_files)
        
        # Export
        if args.export:
            if args.export in ['json', 'both']:
                Reporter.export_json(issues, total_files)
            if args.export in ['html', 'both']:
                Reporter.export_html(issues, total_files)
        
        # Log summary
        critical_count = sum(1 for i in issues if i['severity'] == 'CRITICAL')
        logger.info(f"Scan selesai. Files: {total_files}, Issues: {len(issues)}, Critical: {critical_count}")
        
        # Exit code untuk CI/CD
        if critical_count > 0:
            logger.warning(f"Ditemukan {critical_count} celah CRITICAL!")
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.warning("Scan dibatalkan oleh user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Error tidak terduga saat scan: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()