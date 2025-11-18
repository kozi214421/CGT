"""
Data models for financial trade auditing system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TransactionType(Enum):
    """Types of securities transactions."""
    PURCHASE = "purchase"
    SALE = "sale"
    EXCHANGE = "exchange"


class AmountRange(Enum):
    """Standard reporting amount ranges for transactions."""
    RANGE_1_15K = "$1,001 - $15,000"
    RANGE_15K_50K = "$15,001 - $50,000"
    RANGE_50K_100K = "$50,001 - $100,000"
    RANGE_100K_250K = "$100,001 - $250,000"
    RANGE_250K_500K = "$250,001 - $500,000"
    RANGE_500K_1M = "$500,001 - $1,000,000"
    RANGE_1M_5M = "$1,000,001 - $5,000,000"
    RANGE_5M_25M = "$5,000,001 - $25,000,000"
    RANGE_25M_50M = "$25,000,001 - $50,000,000"
    RANGE_50M_PLUS = "$50,000,000+"


@dataclass
class Transaction:
    """Represents a single securities transaction."""
    official_name: str
    transaction_date: datetime
    security_name: str
    ticker_symbol: Optional[str]
    transaction_type: TransactionType
    amount_range: str
    filing_date: datetime
    document_id: str
    confidence_score: float = 1.0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return {
            "official_name": self.official_name,
            "transaction_date": self.transaction_date.isoformat(),
            "security_name": self.security_name,
            "ticker_symbol": self.ticker_symbol,
            "transaction_type": self.transaction_type.value,
            "amount_range": self.amount_range,
            "filing_date": self.filing_date.isoformat(),
            "document_id": self.document_id,
            "confidence_score": self.confidence_score,
            "raw_data": self.raw_data
        }


@dataclass
class Official:
    """Represents a government official."""
    name: str
    title: str
    chamber: Optional[str]  # House, Senate, Executive, Judicial
    state: Optional[str]
    party: Optional[str]
    transactions: List[Transaction] = field(default_factory=list)
    
    def add_transaction(self, transaction: Transaction):
        """Add a transaction to the official's record."""
        self.transactions.append(transaction)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert official to dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "chamber": self.chamber,
            "state": self.state,
            "party": self.party,
            "transaction_count": len(self.transactions),
            "transactions": [t.to_dict() for t in self.transactions]
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for an official's trades."""
    official_name: str
    total_transactions: int
    purchase_count: int
    sale_count: int
    total_estimated_value: float
    average_confidence_score: float
    filing_compliance_rate: float
    data_quality_score: float
    time_period: str = "lifetime"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "official_name": self.official_name,
            "total_transactions": self.total_transactions,
            "purchase_count": self.purchase_count,
            "sale_count": self.sale_count,
            "total_estimated_value": self.total_estimated_value,
            "average_confidence_score": self.average_confidence_score,
            "filing_compliance_rate": self.filing_compliance_rate,
            "data_quality_score": self.data_quality_score,
            "time_period": self.time_period
        }


@dataclass
class Filing:
    """Represents a filing document."""
    document_id: str
    official_name: str
    filing_date: datetime
    filing_type: str  # PTR (Periodic Transaction Report), AIF (Annual Investment Filing)
    document_path: Optional[str]
    parsed: bool = False
    ocr_used: bool = False
    parse_confidence: float = 0.0
    transactions: List[Transaction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filing to dictionary."""
        return {
            "document_id": self.document_id,
            "official_name": self.official_name,
            "filing_date": self.filing_date.isoformat(),
            "filing_type": self.filing_type,
            "parsed": self.parsed,
            "ocr_used": self.ocr_used,
            "parse_confidence": self.parse_confidence,
            "transaction_count": len(self.transactions)
        }
