# Congress Trading Audit Tool

A comprehensive tool for analyzing congressional trading disclosures, parsing PDF documents, and computing performance and compliance metrics.

## Features

- **PDF Parsing**: Extract trade data from congressional disclosure PDFs using pdfplumber with OCR fallback
- **Web Scraping**: Fetch trading data from online sources
- **Performance Metrics**: Compute lifetime performance metrics using real-time financial data
- **Compliance Checking**: Detect late filings and analyze compliance with STOCK Act requirements
- **CLI Interface**: Easy-to-use command-line interface with multiple commands
- **Configurable**: Support for custom Poppler paths and environment variables

## Requirements

- Python 3.10 or higher
- Poppler utilities (for PDF processing with OCR fallback)

### Installing Poppler

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kozi214421/CGT.git
cd CGT
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set Poppler path environment variable:
```bash
export POPLER_BIN=/usr/local/bin  # Adjust path as needed
```

## Usage

### Run Full Audit

Execute the complete audit workflow with sample data:

```bash
python run_audit.py run
```

With custom options:
```bash
python run_audit.py run --output-dir ./output --poppler-path /usr/local/bin
```

With PDF files:
```bash
python run_audit.py run --pdf-files disclosure1.pdf disclosure2.pdf
```

### Parse Single PDF

Parse and display contents of a PDF file:

```bash
python run_audit.py parse-pdf path/to/disclosure.pdf
```

Show extracted text:
```bash
python run_audit.py parse-pdf path/to/disclosure.pdf --show-text
```

### Print Summary

Display summary of existing audit results:

```bash
python run_audit.py print-summary
```

From custom output directory:
```bash
python run_audit.py print-summary --output-dir ./custom-output
```

### Verbose Logging

Enable detailed DEBUG logging for any command:

```bash
python run_audit.py -v run
```

## Output Files

The tool generates the following output files in `congress_trades_output/` (by default):

- **transactions_last_120_days.json**: Recent trades from the last 120 days
- **official_lifetime_performance.json**: Lifetime performance metrics by ticker
- **compliance_summary.json**: Compliance analysis with late filing statistics
- **congress_trading_outputs.zip**: ZIP bundle containing all output files

## CLI Commands

### `run`
Execute the full audit workflow including:
- Trade extraction
- Metric computation
- Compliance analysis
- Output generation

**Options:**
- `--source-url URL`: Fetch data from URL
- `--pdf-files FILE [FILE ...]`: Parse specific PDF files
- `--output-dir DIR`: Output directory (default: congress_trades_output)
- `--poppler-path PATH`: Path to Poppler binaries

### `parse-pdf`
Parse a single PDF file and display results.

**Arguments:**
- `pdf_path`: Path to PDF file

**Options:**
- `--show-text`: Display extracted text (first 1000 chars)
- `--poppler-path PATH`: Path to Poppler binaries

### `print-summary`
Print summary of existing output files.

**Options:**
- `--output-dir DIR`: Output directory to read from

## Configuration

### Poppler Path

The tool discovers Poppler binaries in the following priority order:

1. `--poppler-path` CLI argument
2. `POPLER_BIN` environment variable
3. Common system locations:
   - `/usr/bin`
   - `/usr/local/bin`
   - `/opt/homebrew/bin` (macOS)
   - `C:\Program Files\poppler\bin` (Windows)

### Environment Variables

- `POPLER_BIN`: Path to Poppler binaries directory

## Development

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=congress_audit tests/
```

### Code Quality

Run flake8 for linting:
```bash
flake8 congress_audit/ tests/
```

## Project Structure

```
CGT/
├── congress_audit/          # Main package
│   ├── __init__.py         # Package metadata
│   ├── cli.py              # CLI interface
│   ├── core.py             # Core orchestration
│   ├── pdf_utils.py        # PDF parsing utilities
│   ├── metrics.py          # Metric calculations
│   └── io_utils.py         # File I/O utilities
├── tests/                   # Unit tests
│   ├── test_metrics.py
│   └── test_pdf_utils.py
├── run_audit.py            # Main entry point
├── congress_trades_audit.py # Legacy entry point
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Backwards Compatibility

For backwards compatibility, you can still use the original script name:

```bash
python congress_trades_audit.py run
```

However, using `run_audit.py` is recommended for new usage.

## CI/CD

The project includes GitHub Actions workflow for:
- Running tests on Python 3.10 and 3.11
- Code quality checks with flake8
- Dependency caching for faster builds

## License

See repository for license information.

## Contributing

Contributions are welcome! Please ensure:
- All tests pass
- Code follows PEP 8 style guidelines
- New features include appropriate tests
