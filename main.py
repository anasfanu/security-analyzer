import argparse
import sys
import os
import json
from scanner import SecurityScanner
from reporter import Reporter
from fixer import AutoFixer
from logger import setup_logger, get_logger, setup_global_exception_handler, view_logs

# Setup global exception handler
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
  python main.py /path/to/project --export both
  python main.py --fix output/scan_report_20261027_120000.json
  python main.py --fix output/scan_report.json --dry-run
  python main.py --fix output/scan_report.json --interactive
  python main.py --fix output/scan_report.json --export-stats
  python main.py --view-logs app
  python main.py --view-logs error
        """
    )
    
    parser.add_argument("target_dir", nargs="?", default=".", 
                       help="Direktori target (default: current directory)")
    
    parser.add_argument("--export", choices=['json', 'html', 'both'], 
                       help="Export laporan ke format tertentu")
    
    parser.add_argument("--fix", metavar="REPORT_FILE", 
                       help="Auto-fix berdasarkan laporan JSON")
    
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview fix tanpa mengubah file (aman)")
    
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Konfirmasi setiap fix secara manual")
    
    parser.add_argument("--export-stats", action="store_true",
                       help="Export statistik fix ke JSON")
    
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
                print(f"\n[!] Error: File laporan tidak ditemukan: {args.fix}")
                sys.exit(1)
            
            # Baca JSON untuk mengetahui folder asli
            with open(args.fix, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            fix_target_dir = report_data.get('target_dir', '.')
            
            print(f"\n{'='*70}")
            print(f"🔧 AUTO-FIX ENGINE")
            print(f"{'='*70}")
            print(f"[*] Laporan    : {args.fix}")
            print(f"[*] Target     : {fix_target_dir}")
            print(f"[*] Mode       : {'DRY-RUN (Preview)' if args.dry_run else 'LIVE (Akan mengubah file)'}")
            print(f"[*] Interactive: {'Ya' if args.interactive else 'Tidak'}")
            print(f"{'='*70}\n")
            
            logger.info(f"Memulai Auto-Fix untuk folder: {fix_target_dir}")
            
            fixer = AutoFixer()
            stats = fixer.fix_from_report(
                args.fix, 
                fix_target_dir,
                dry_run=args.dry_run,
                interactive=args.interactive
            )
            
            # Print summary
            fixer.print_summary()
            
            # Export stats jika diminta
            if args.export_stats:
                stats_file = fixer.export_stats()
                print(f"\n[✓] Statistik fix disimpan: {stats_file}")
            
            logger.info(f"Auto-Fix selesai: {stats}")
            sys.exit(0)
            
        except KeyboardInterrupt:
            logger.warning("Auto-fix dibatalkan oleh user")
            print("\n[!] Auto-fix dibatalkan.")
            sys.exit(130)
        except Exception as e:
            logger.exception(f"Gagal melakukan auto-fix: {e}")
            print(f"\n[!] Error: {e}")
            sys.exit(1)
    
    # =========================================================================
    # Mode: Scan
    # =========================================================================
    try:
        target_dir = os.path.abspath(args.target_dir)
        
        if not os.path.isdir(target_dir):
            logger.error(f"Direktori tidak ditemukan: {target_dir}")
            print(f"\n[!] Error: Direktori tidak ditemukan: {target_dir}")
            sys.exit(1)
        
        logger.info(f"Memulai scan di: {target_dir}")
        
        print(f"\n{'='*70}")
        print(f"🔒 DEEP PROJECT SECURITY & BUG ANALYZER")
        print(f"{'='*70}")
        print(f"[*] Target: {target_dir}")
        print(f"[*] Log disimpan di: logs/")
        print(f"{'='*70}\n")
        
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
                Reporter.export_json(issues, total_files, target_dir)
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
        print("\n[!] Scan dibatalkan.")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Error tidak terduga saat scan: {e}")
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()