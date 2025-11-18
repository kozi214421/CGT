# CGT Usage Guide

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/kozi214421/CGT.git
cd CGT
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install Tesseract OCR for scanned documents:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Running the System

#### Demo Mode

See what the system can do:
```bash
python main.py --demo
```

#### Process Real Filings

Process a single PDF:
```bash
python main.py --input path/to/filing.pdf
```

Process all PDFs in a directory:
```bash
python main.py --input path/to/filings_directory/
```

With custom configuration:
```bash
python main.py --input filings/ --config my_config.json --output my_output/
```

Verbose logging:
```bash
python main.py --input filings/ --verbose
```

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "ocr_enabled": true,
  "confidence_threshold": 0.7,
  "data_sources": {
    "stock_act_filings": "https://disclosures-clerk.house.gov",
    "senate_filings": "https://efdsearch.senate.gov"
  },
  "output_format": "json",
  "output_directory": "output",
  "validation_rules": {
    "required_fields": [
      "official_name",
      "transaction_date",
      "security_name",
      "transaction_type",
      "amount_range"
    ],
    "date_format": "%Y-%m-%d"
  },
  "performance_metrics": {
    "calculate_returns": true,
    "benchmark_index": "SPY",
    "time_periods": ["1M", "3M", "6M", "1Y", "lifetime"]
  }
}
```

### Configuration Options

- **ocr_enabled**: Enable OCR for scanned documents (requires Tesseract)
- **confidence_threshold**: Minimum confidence score for transactions (0.0-1.0)
- **output_directory**: Where to save exported JSON files
- **required_fields**: Fields that must be present in each transaction
- **time_periods**: Time periods for performance analysis

## Understanding the Output

### File Structure

When you run the system, it creates several JSON files in the output directory:

```
output/
├── officials_20231118_120000.json
├── transactions_20231118_120000.json
├── filings_20231118_120000.json
├── performance_metrics_20231118_120000.json
└── comprehensive_report_20231118_120000.json
```

### Output File Contents

#### Officials Export
```json
{
  "export_date": "2023-11-18T12:00:00",
  "total_officials": 10,
  "total_transactions": 150,
  "officials": [
    {
      "name": "John Smith",
      "title": "Representative",
      "chamber": "House",
      "state": "CA",
      "party": "Democrat",
      "transaction_count": 15,
      "transactions": [...]
    }
  ]
}
```

#### Transactions Export
```json
{
  "export_date": "2023-11-18T12:00:00",
  "total_transactions": 150,
  "transactions": [
    {
      "official_name": "John Smith",
      "transaction_date": "2023-01-15T00:00:00",
      "security_name": "Apple Inc.",
      "ticker_symbol": "AAPL",
      "transaction_type": "purchase",
      "amount_range": "$15,001 - $50,000",
      "filing_date": "2023-02-01T00:00:00",
      "document_id": "DOC-2023-001",
      "confidence_score": 0.92,
      "raw_data": {...}
    }
  ]
}
```

#### Performance Metrics
```json
{
  "export_date": "2023-11-18T12:00:00",
  "total_officials": 10,
  "metrics": [
    {
      "official_name": "John Smith",
      "total_transactions": 15,
      "purchase_count": 9,
      "sale_count": 6,
      "total_estimated_value": 375000.0,
      "average_confidence_score": 0.87,
      "filing_compliance_rate": 0.93,
      "data_quality_score": 0.85,
      "time_period": "lifetime"
    }
  ]
}
```

#### Comprehensive Report
Combines all the above with aggregate statistics and top traders.

## Working with the Data

### Using Python

```python
import json
from cgt.audit_system import FinancialTradeAuditSystem

# Initialize system
system = FinancialTradeAuditSystem('config.json')

# Process a filing
from datetime import datetime
filing_data = {
    "document_id": "DOC-001",
    "official_name": "John Smith",
    "filing_date": datetime(2023, 2, 1),
    "filing_type": "PTR",
    "pdf_path": "filing.pdf"
}
filing = system.process_filing("filing.pdf", filing_data)

# Get summary
summary = system.get_summary()
print(f"Processed {summary['total_transactions']} transactions")

# Export results
files = system.export_results(format='json')
print(f"Exported to: {files}")

# Generate comprehensive report
report_path = system.generate_comprehensive_report()
print(f"Report saved to: {report_path}")
```

### Analyzing Results

Load and analyze exported data:

```python
import json

# Load comprehensive report
with open('output/comprehensive_report_20231118_120000.json', 'r') as f:
    data = json.load(f)

# Get aggregate stats
stats = data['aggregate_statistics']
print(f"Total officials: {stats['total_officials']}")
print(f"Total transactions: {stats['total_transactions']}")
print(f"Overall compliance rate: {stats['overall_compliance_rate']:.1%}")

# Find top traders
top_traders = stats['top_traders']
for trader in top_traders[:5]:
    print(f"{trader['name']}: {trader['transaction_count']} transactions")

# Analyze individual official
for official in data['officials']:
    if official['name'] == 'John Smith':
        print(f"Transactions: {len(official['transactions'])}")
        for txn in official['transactions']:
            print(f"  {txn['transaction_date']}: {txn['security_name']}")
```

## Common Workflows

### 1. Audit New Filings

```bash
# Download filings to data/new_filings/
# Process them
python main.py --input data/new_filings/

# Results saved to output/
```

### 2. Generate Reports

```python
from cgt.audit_system import FinancialTradeAuditSystem

system = FinancialTradeAuditSystem()
# ... process filings ...
report = system.generate_comprehensive_report('monthly_report.json')
```

### 3. Validate Data Quality

```python
from cgt.validators.data_validator import DataValidator

validator = DataValidator(config)
is_valid, errors = validator.validate_transaction(transaction)

if not is_valid:
    print(f"Validation errors: {errors}")

quality_score = validator.calculate_data_quality_score(transaction)
print(f"Quality score: {quality_score:.2%}")
```

### 4. Calculate Custom Metrics

```python
from cgt.analyzers.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(config)

# Metrics for specific time period
metrics_1m = analyzer.calculate_official_metrics(official, "1M")
metrics_1y = analyzer.calculate_official_metrics(official, "1Y")

# Top traders by value
top_by_value = analyzer.get_top_traders(officials, limit=20, by="estimated_value")
```

## Interpreting Scores

### Confidence Score (0.0-1.0)

- **0.9-1.0**: High confidence - Clean extraction, all fields present
- **0.7-0.9**: Good confidence - Most fields present, minor issues
- **0.5-0.7**: Medium confidence - Some missing fields or extraction issues
- **0.0-0.5**: Low confidence - Significant issues, manual review recommended

### Data Quality Score (0.0-1.0)

Factors:
- Ticker symbol presence
- Complete official name
- Security name quality
- Date reasonableness
- Raw data availability

### Filing Compliance Rate (0.0-1.0)

Percentage of transactions filed within 45 days (STOCK Act requirement)
- **0.9-1.0**: Excellent compliance
- **0.7-0.9**: Good compliance
- **0.5-0.7**: Poor compliance
- **0.0-0.5**: Very poor compliance

## Troubleshooting

### Issue: "pdfplumber not installed"

Install the required package:
```bash
pip install pdfplumber
```

### Issue: "pytesseract not installed"

OCR is optional. To enable:
```bash
pip install pytesseract
# Also install Tesseract system package (see Installation section)
```

### Issue: No transactions found

Possible causes:
1. PDF is scanned image (enable OCR in config)
2. PDF format not recognized (try different parser)
3. Transaction format different than expected (adjust regex patterns)

### Issue: Low confidence scores

Review the raw data and consider:
1. Adjusting validation rules
2. Improving PDF quality
3. Manual data entry for problematic filings

### Issue: Memory errors with large datasets

Process in batches:
```python
import glob

pdf_files = glob.glob('filings/*.pdf')
batch_size = 100

for i in range(0, len(pdf_files), batch_size):
    batch = pdf_files[i:i+batch_size]
    # Process batch
    system.process_multiple_filings(batch)
    # Export and clear
    system.export_results()
    system.officials.clear()
    system.filings.clear()
```

## Best Practices

1. **Validate Input**: Check PDF quality before processing
2. **Review Output**: Manually verify sample of results
3. **Monitor Scores**: Track confidence and quality scores
4. **Batch Processing**: Process similar filings together
5. **Regular Backups**: Save exported JSON files
6. **Version Control**: Track configuration changes
7. **Documentation**: Note any manual corrections
8. **Compliance**: Verify filing dates and timelines

## Advanced Usage

### Custom Parsers

Create custom parser for different filing formats:

```python
from cgt.parsers.pdf_parser import PDFParser

class CustomParser(PDFParser):
    def _extract_transactions(self, text, filing):
        # Custom extraction logic
        pass
```

### Custom Validators

Add domain-specific validation:

```python
from cgt.validators.data_validator import DataValidator

class CustomValidator(DataValidator):
    def validate_transaction(self, transaction):
        # Call parent validator
        is_valid, errors = super().validate_transaction(transaction)
        
        # Add custom validation
        if transaction.amount_range == "$50,000+":
            errors.append("Requires specific amount for large transactions")
            is_valid = False
        
        return is_valid, errors
```

### Integration with External APIs

```python
# Example: Enrich with stock price data
import requests

def enrich_with_price(transaction):
    """Add market price at transaction date."""
    response = requests.get(
        f"https://api.example.com/price/{transaction.ticker_symbol}",
        params={"date": transaction.transaction_date}
    )
    transaction.raw_data['market_price'] = response.json()['price']
    return transaction
```

## Support

For issues or questions:
1. Check this usage guide
2. Review ARCHITECTURE.md for technical details
3. Examine example_output.json for expected format
4. Submit issues on GitHub

## Updates

Stay current with system updates:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```
