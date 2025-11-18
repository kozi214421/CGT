# CGT - Congressional & Government Trading Audit System

A comprehensive financial trade auditing system for U.S. federal officials under the STOCK Act and EIGA (Ethics in Government Act). This system extracts, validates, and analyzes securities transactions from official government filings using advanced PDF parsing, OCR, and data normalization techniques.

## Features

- **PDF Parsing**: Extract transaction data from official filings using PyPDF2 and pdfplumber
- **OCR Support**: Process scanned documents with Tesseract OCR
- **Data Validation**: Normalize and validate transaction data with confidence scoring
- **Performance Metrics**: Calculate lifetime performance metrics per official
- **Compliance Tracking**: Monitor filing compliance with STOCK Act requirements
- **JSON Export**: Export verified results in structured JSON format
- **Comprehensive Reporting**: Generate detailed audit reports with aggregate statistics

## Installation

### Requirements

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/kozi214421/CGT.git
cd CGT
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) For OCR functionality, install Tesseract:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

## Usage

### Demo Mode

Run the system in demo mode to see capabilities:

```bash
python main.py --demo
```

### Process PDF Filings

Process a single PDF filing:

```bash
python main.py --input path/to/filing.pdf
```

Process multiple filings from a directory:

```bash
python main.py --input path/to/filings/directory/
```

### Configuration

Edit `config.json` to customize system behavior:

```json
{
  "ocr_enabled": true,
  "confidence_threshold": 0.7,
  "output_directory": "output",
  "validation_rules": {
    "required_fields": [
      "official_name",
      "transaction_date",
      "security_name",
      "transaction_type",
      "amount_range"
    ]
  }
}
```

## System Architecture

### Core Components

- **Models** (`cgt/models.py`): Data structures for transactions, officials, and filings
- **Parsers** (`cgt/parsers/`): PDF and OCR parsing modules
- **Validators** (`cgt/validators/`): Data validation and normalization
- **Analyzers** (`cgt/analyzers/`): Performance metrics calculation
- **Exporters** (`cgt/exporters/`): JSON export functionality
- **Audit System** (`cgt/audit_system.py`): Main orchestration

### Data Flow

1. **Input**: PDF filings from House/Senate disclosure systems
2. **Parsing**: Extract text using PDF parsers or OCR
3. **Extraction**: Pattern matching to identify transactions
4. **Validation**: Normalize and validate transaction data
5. **Scoring**: Calculate confidence and quality scores
6. **Analysis**: Compute performance metrics
7. **Export**: Generate structured JSON reports

## Output Format

The system exports data in structured JSON format:

### Officials Export
```json
{
  "export_date": "2023-01-15T10:30:00",
  "total_officials": 10,
  "total_transactions": 150,
  "officials": [
    {
      "name": "John Smith",
      "title": "Representative",
      "chamber": "House",
      "transactions": [...]
    }
  ]
}
```

### Performance Metrics
```json
{
  "official_name": "John Smith",
  "total_transactions": 25,
  "purchase_count": 15,
  "sale_count": 10,
  "total_estimated_value": 750000.0,
  "average_confidence_score": 0.85,
  "filing_compliance_rate": 0.92,
  "data_quality_score": 0.88
}
```

## Compliance

This system helps audit compliance with:

- **STOCK Act (2012)**: Requires federal officials to report securities transactions within 45 days
- **EIGA (1978)**: Requires annual financial disclosures from government officials

## Data Sources

The system is designed to process filings from:

- House of Representatives: https://disclosures-clerk.house.gov
- U.S. Senate: https://efdsearch.senate.gov

## Development

### Project Structure

```
CGT/
├── cgt/
│   ├── __init__.py
│   ├── models.py
│   ├── audit_system.py
│   ├── parsers/
│   │   ├── pdf_parser.py
│   │   └── ocr_parser.py
│   ├── validators/
│   │   └── data_validator.py
│   ├── analyzers/
│   │   └── performance_analyzer.py
│   └── exporters/
│       └── json_exporter.py
├── tests/
├── main.py
├── config.json
├── requirements.txt
└── README.md
```

### Running Tests

```bash
pytest tests/
```

## Limitations

- PDF parsing accuracy depends on document format consistency
- OCR quality varies with scan quality
- Performance metrics are estimates based on reported ranges
- Historical data limited to STOCK Act effective date (2012)

## License

This project is open source and available for use in monitoring government transparency.

## Contributing

Contributions are welcome! Please submit issues and pull requests on GitHub.

## Disclaimer

This tool is for research and transparency purposes. Transaction data should be verified against official government sources. Performance metrics are estimates and not financial advice.
