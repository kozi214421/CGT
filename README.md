# Congressional Trading Audit System

A robust, testable package for auditing congressional trading activities. Processes PDF documents, extracts trading data, and calculates performance metrics.

## Features

- **PDF Processing**: Extract text from congressional trading PDFs using pdfplumber
- **OCR Support**: Process scanned documents with pytesseract and Poppler
- **Environment Configuration**: Flexible Poppler path configuration via CLI arguments or environment variables
- **Financial Metrics**: Calculate portfolio performance, ROI, and trading patterns using yfinance
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **CLI Interface**: Easy-to-use command-line interface
- **Unit Tested**: Full test coverage with mocked external dependencies
- **CI/CD Ready**: GitHub Actions workflow for continuous integration

## Installation

### Requirements

- Python 3.8 or higher
- Poppler utilities (for PDF processing)
- Tesseract OCR (optional, for scanned documents)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/kozi214421/CGT.git
cd CGT
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Poppler (choose your platform):

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS (Homebrew):**
```bash
brew install poppler
```

**Windows:**
Download from https://github.com/oschwartz10612/poppler-windows/releases/
and extract to a directory (e.g., `C:\poppler`)

4. (Optional) Install Tesseract for OCR:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from https://github.com/UB-Mannheim/tesseract/wiki

## Usage

### Command Line Interface

The system provides two entry points:
- `run_audit.py` (recommended)
- `congress_trades_audit.py` (backwards compatible)

#### Basic Usage

Process a single PDF:
```bash
python run_audit.py --pdf trade_report.pdf
```

Process multiple PDFs:
```bash
python run_audit.py --pdf report1.pdf report2.pdf report3.pdf
```

Use OCR for scanned documents:
```bash
python run_audit.py --pdf scanned_report.pdf --ocr
```

Specify custom output directory:
```bash
python run_audit.py --pdf report.pdf --output results/
```

#### Configuration

Specify Poppler path (if not in system PATH):
```bash
# Via command-line argument
python run_audit.py --pdf report.pdf --poppler-path /usr/local/bin

# Via environment variable
export POPPLER_BIN=/usr/local/bin
python run_audit.py --pdf report.pdf
```

Enable verbose logging:
```bash
python run_audit.py --pdf report.pdf --verbose
```

#### Validate Environment

Check if all dependencies are properly installed:
```bash
python run_audit.py --validate
```

### Python API

You can also use the package programmatically:

```python
from congress_audit import run_audit

# Run audit with custom parameters
results = run_audit(
    pdf_paths=['trade_report.pdf'],
    poppler_path='/usr/local/bin',
    output_dir='congress_trades_output',
    use_ocr=False,
    verbose=True
)

print(f"Processed {results['documents_processed']} documents")
print(f"Extracted {results['trades_extracted']} trades")
```

## Output

The system generates output files in the `congress_trades_output/` directory:

- `audit_results.json`: Complete audit results
- `trades.json`: Extracted trade data
- `metrics.json`: Performance metrics

### Example Output Structure

```json
{
  "audit_date": "2023-10-15T14:30:00",
  "documents_processed": 5,
  "trades_extracted": 25,
  "poppler_path": "/usr/local/bin",
  "ocr_enabled": false,
  "trades": [...],
  "metrics": {
    "total_trades": 25,
    "buy_count": 15,
    "sell_count": 10,
    "total_value": 1500000.0,
    "average_trade_value": 60000.0
  }
}
```

## Project Structure

```
CGT/
├── congress_audit/          # Main package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── core.py             # Core audit logic
│   ├── pdf_utils.py        # PDF processing utilities
│   ├── metrics.py          # Financial metrics calculations
│   └── io_utils.py         # I/O operations
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_metrics.py
│   └── test_pdf_utils.py
├── congress_trades_audit.py # Legacy entry point (shim)
├── run_audit.py            # Main entry point
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── .github/
│   └── workflows/
│       └── python-app.yml # CI/CD workflow
└── README.md              # This file
```

## Development

### Running Tests

Run all tests with pytest:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=congress_audit tests/
```

Run specific test file:
```bash
pytest tests/test_metrics.py -v
```

### Code Style

The project follows PEP 8 style guidelines. All functions include type hints and docstrings.

## Environment Variables

- `POPPLER_BIN`: Path to Poppler binaries directory (overridden by `--poppler-path`)

## Poppler Path Detection

The system attempts to find Poppler in the following order:

1. `--poppler-path` CLI argument
2. `POPPLER_BIN` environment variable
3. Common installation paths for the current OS
4. System PATH

If Poppler is not found and OCR is enabled, a warning is issued but the system will attempt to continue.

## Testing

All tests use mocked external dependencies to avoid:
- Network calls to yfinance
- Actual PDF file processing
- OCR operations

This ensures tests run quickly and reliably without external dependencies.

## Continuous Integration

The project includes a GitHub Actions workflow (`.github/workflows/python-app.yml`) that:
- Runs tests on multiple Python versions
- Checks code quality
- Generates coverage reports

## Troubleshooting

### Poppler Not Found

If you see warnings about Poppler not being found:

1. Install Poppler for your platform (see Installation section)
2. Set the `POPPLER_BIN` environment variable
3. Use the `--poppler-path` argument
4. Run `python run_audit.py --validate` to check your setup

### Import Errors

If you encounter import errors, ensure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### OCR Not Working

If OCR fails:
1. Ensure Tesseract is installed
2. Verify Poppler is properly configured
3. Check that the PDF is in a supported format

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Disclaimer

This tool is for transparency and research purposes. Trading data should be verified against official sources. This is not financial advice
