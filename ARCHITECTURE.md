# CGT System Architecture

## Overview

The Congressional & Government Trading (CGT) Audit System is designed to audit U.S. federal officials' financial trades under the STOCK Act (2012) and EIGA (Ethics in Government Act, 1978).

## System Components

### 1. Data Models (`cgt/models.py`)

Core data structures representing the domain:

- **Transaction**: Individual securities transaction with fields for official name, dates, security info, amounts, and confidence scores
- **Official**: Government official with metadata and collection of transactions
- **Filing**: Filing document metadata with parsing status and OCR indicators
- **PerformanceMetrics**: Calculated metrics including transaction counts, estimated values, compliance rates, and quality scores
- **Enums**: TransactionType (purchase/sale/exchange), AmountRange (standard reporting ranges)

### 2. Parsers Module (`cgt/parsers/`)

#### PDF Parser (`pdf_parser.py`)
- Extracts text from PDF filings using two libraries:
  - **pdfplumber**: Primary parser with better accuracy
  - **PyPDF2**: Fallback parser
- Pattern matching to identify transaction data
- Calculates parse confidence scores based on:
  - Text quality and quantity
  - Number of transactions found
  - Presence of expected keywords
- Triggers OCR when minimal text is extracted

#### OCR Parser (`ocr_parser.py`)
- Processes scanned documents using Tesseract OCR
- Extracts text from images
- Calculates OCR confidence scores
- Supports multiple languages (default: English)

### 3. Validators Module (`cgt/validators/`)

#### Data Validator (`data_validator.py`)
Ensures data quality through:

**Validation:**
- Required field presence
- Date consistency (filing after transaction)
- Amount range format
- Ticker symbol format (1-5 uppercase letters)
- Confidence score range (0.0-1.0)

**Normalization:**
- Name formatting (title case, suffix handling)
- Security name standardization (Inc., Corp., LLC)
- Amount range formatting
- Ticker symbol uppercase conversion

**Quality Scoring:**
- Ticker symbol presence
- Name completeness
- Security name quality
- Date reasonableness
- Confidence level
- Raw data availability

### 4. Analyzers Module (`cgt/analyzers/`)

#### Performance Analyzer (`performance_analyzer.py`)
Calculates comprehensive metrics:

**Per-Official Metrics:**
- Total transaction count
- Purchase vs. sale breakdown
- Estimated total value (using range midpoints)
- Average confidence score
- Filing compliance rate (45-day requirement)
- Data quality score

**Aggregate Statistics:**
- Total officials and transactions
- Average transactions per official
- Overall confidence and compliance rates
- Top traders rankings

**Time Period Analysis:**
- 1M, 3M, 6M, 1Y, lifetime periods
- Transaction filtering by date range

**Compliance Monitoring:**
- STOCK Act 45-day filing requirement
- Calculates percentage of timely filings

### 5. Exporters Module (`cgt/exporters/`)

#### JSON Exporter (`json_exporter.py`)
Structured data export with:

- **Officials Export**: Complete official records with transactions
- **Transactions Export**: All transactions with metadata
- **Performance Metrics**: Calculated metrics per official
- **Filings Export**: Filing metadata and parse status
- **Comprehensive Report**: Combined export with aggregate statistics

All exports include:
- ISO 8601 timestamp formatting
- UTF-8 encoding
- Pretty-printed JSON (2-space indent)
- Export metadata (date, counts, sources)

### 6. Audit System (`cgt/audit_system.py`)

Main orchestration class coordinating all components:

**Initialization:**
- Loads configuration from JSON
- Initializes all subsystem components
- Sets up output directories

**Processing Pipeline:**
1. Parse filing PDF → Extract transactions
2. Normalize transaction data
3. Validate each transaction
4. Calculate quality scores
5. Store in official records
6. Generate performance metrics
7. Export results to JSON

**Features:**
- Single filing or batch processing
- Progress tracking and logging
- Error handling and recovery
- Summary statistics generation

## Data Flow

```
Input (PDF Filing)
    ↓
PDF Parser (with OCR fallback)
    ↓
Transaction Extraction (pattern matching)
    ↓
Data Normalization (standardize formats)
    ↓
Validation (check consistency)
    ↓
Quality Scoring (calculate confidence)
    ↓
Official Records (aggregate by person)
    ↓
Performance Analysis (calculate metrics)
    ↓
JSON Export (structured output)
```

## Configuration (`config.json`)

Customizable settings:
- OCR enablement
- Confidence thresholds
- Data source URLs
- Output format and directory
- Validation rules
- Performance metric parameters

## Error Handling

- Try-catch blocks at each processing stage
- Detailed logging (INFO, WARNING, ERROR levels)
- Graceful degradation (e.g., PDF parser fallback)
- Validation error collection without stopping
- Transaction-level error isolation

## Scoring System

### Confidence Scores (0.0-1.0)

**Parse Confidence:**
- Text extraction quality: 0.1-0.2
- Transaction count: 0.1-0.2
- Keyword presence: up to 0.1
- Base score: 0.5

**Data Quality Score:**
- Ticker symbol: 1.0 point
- Complete name: 1.0 point
- Security name: 1.0 point
- Reasonable dates: 1.0 point
- High confidence: 0.5-1.0 point
- Raw data: 1.0 point
- Normalized to 0.0-1.0 scale

### Compliance Rate

Percentage of transactions filed within 45 days of transaction date, per STOCK Act requirements.

## Extensibility

The modular design allows easy extension:

- Add new parsers (e.g., XML, HTML)
- Implement additional validators
- Create new exporters (CSV, Excel, Database)
- Add more performance metrics
- Integrate external APIs (e.g., stock price data)
- Support additional filing types (AIF, OGE-278)

## Dependencies

**Core:**
- Python 3.8+
- json, datetime, pathlib (standard library)

**PDF Processing:**
- PyPDF2 >= 3.0.0
- pdfplumber >= 0.10.0

**OCR:**
- pytesseract >= 0.3.10
- Pillow >= 10.0.0

**Data Processing:**
- pandas >= 2.0.0 (optional, for future enhancements)
- numpy >= 1.24.0 (optional, for future enhancements)

**Utilities:**
- python-dateutil >= 2.8.2
- requests >= 2.31.0 (for future API integration)

## Security Considerations

1. **Input Validation**: All transaction data validated before processing
2. **Path Sanitization**: File paths checked before access
3. **Error Isolation**: Individual transaction errors don't crash system
4. **Logging**: Sensitive data not logged
5. **Dependencies**: Using maintained, security-patched libraries

## Performance Characteristics

- **Memory**: O(n) where n = number of transactions
- **Processing**: Linear with number of filings
- **I/O**: Minimized with batch processing
- **Scalability**: Can process thousands of filings
- **Parallelization**: Future enhancement opportunity

## Testing Strategy

1. **Unit Tests**: Models, validators, analyzers
2. **Integration Tests**: End-to-end workflow (future)
3. **Validation Tests**: Data consistency checks
4. **Edge Cases**: Empty inputs, malformed data
5. **Performance Tests**: Large dataset handling (future)

Current test coverage:
- 19 unit tests
- All core functionality validated
- Models, validators, analyzers tested
- 100% test pass rate
