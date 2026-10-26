from flask import Flask, render_template, request, jsonify, send_file
from scanner import SecurityScanner
from reporter import Reporter
from fixer import AutoFixer
from logger import setup_logger, get_logger, setup_global_exception_handler
import os
import json
from datetime import datetime
import traceback

# Setup
setup_global_exception_handler()
logger = setup_logger()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


# =============================================================================
# Global Flask Error Handlers
# =============================================================================
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Endpoint tidak ditemukan'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception(f"500 Internal Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(405)
def method_not_allowed(error):
    logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
    return jsonify({'error': 'Method tidak diizinkan'}), 405


@app.errorhandler(Exception)
def handle_exception(error):
    logger.exception(f"Unhandled exception: {error}")
    return jsonify({
        'error': 'Terjadi kesalahan internal',
        'details': str(error) if app.debug else None
    }), 500


# =============================================================================
# Routes
# =============================================================================
@app.route('/')
def index():
    logger.info(f"Web interface diakses dari: {request.remote_addr}")
    return render_template('index.html')


@app.route('/scan', methods=['POST'])
def scan():
    try:
        target_dir = request.form.get('target_path', '.')
        logger.info(f"Scan request dari {request.remote_addr}: {target_dir}")
        
        if not os.path.isdir(target_dir):
            logger.warning(f"Direktori tidak ditemukan: {target_dir}")
            return jsonify({'error': 'Direktori tidak ditemukan'}), 400
        
        scanner = SecurityScanner()
        issues, total_files = scanner.scan_directory(target_dir)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(app.config['OUTPUT_FOLDER'], f"web_scan_{timestamp}.json")
        
        report = {
            'scan_date': datetime.now().isoformat(),
            'target_dir': os.path.abspath(target_dir),
            'total_files': total_files,
            'total_issues': len(issues),
            'critical_count': sum(1 for i in issues if i['severity'] == 'CRITICAL'),
            'issues': issues
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Scan selesai: {total_files} files, {len(issues)} issues")
        
        return jsonify({
            'success': True,
            'report_file': report_file,
            'summary': {
                'total_files': total_files,
                'total_issues': len(issues),
                'critical_count': report['critical_count']
            },
            'issues': issues[:50]
        })
    
    except Exception as e:
        logger.exception(f"Error saat scan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download(filename):
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(filepath):
            logger.info(f"File didownload: {filename}")
            return send_file(filepath, as_attachment=True)
        logger.warning(f"File tidak ditemukan: {filename}")
        return jsonify({'error': 'File tidak ditemukan'}), 404
    except Exception as e:
        logger.exception(f"Error saat download: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/fix', methods=['POST'])
def fix():
    try:
        report_file = request.json.get('report_file')
        
        if not report_file or not os.path.exists(report_file):
            return jsonify({'error': 'Laporan tidak ditemukan'}), 400
        
        # Baca JSON untuk tahu folder mana yang harus di-fix
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        target_dir = report_data.get('target_dir', '.')
        
        logger.info(f"Auto-fix request untuk folder: {target_dir}")
        
        fixer = AutoFixer()
        stats = fixer.fix_from_report(report_file, target_dir)
        
        logger.info(f"Auto-fix selesai: {stats}")
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.exception(f"Error saat auto-fix: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/logs/<log_type>')
def view_logs_web(log_type):
    try:
        if log_type not in ['app', 'error']:
            return jsonify({'error': 'Tipe log tidak valid'}), 400
        
        log_file = os.path.join('logs', f"{log_type}.log")
        lines = int(request.args.get('lines', 100))
        
        if not os.path.exists(log_file):
            return jsonify({'error': 'File log tidak ditemukan'}), 404
        
        with open(log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        return jsonify({
            'log_type': log_type,
            'total_lines': len(log_lines),
            'lines': log_lines[-lines:]
        })
    
    except Exception as e:
        logger.exception(f"Error saat membaca log: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("="*50)
    logger.info("🌐 Web Interface dimulai")
    logger.info("   URL: http://localhost:5000")
    logger.info("   Logs: http://localhost:5000/logs/app")
    logger.info("="*50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.critical(f"Gagal menjalankan web server: {e}")
        sys.exit(1)