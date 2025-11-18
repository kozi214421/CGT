"""
Unit tests for congress_audit.pdf_utils module.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from congress_audit.pdf_utils import (
    find_poppler_path,
    validate_poppler_path,
    extract_text_from_pdf,
    extract_text_with_ocr,
    parse_trading_document,
)


class TestValidatePopplerPath:
    """Tests for validate_poppler_path function."""
    
    def test_invalid_path_none(self):
        """Test with None path."""
        assert validate_poppler_path(None) is False
    
    def test_invalid_path_empty(self):
        """Test with empty path."""
        assert validate_poppler_path("") is False
    
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_invalid_path_nonexistent(self, mock_exists):
        """Test with non-existent path."""
        mock_exists.return_value = False
        assert validate_poppler_path("/nonexistent/path") is False
    
    @patch('congress_audit.pdf_utils.Path')
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_valid_path_with_utilities(self, mock_exists, mock_path_class):
        """Test with valid path containing Poppler utilities."""
        mock_exists.return_value = True
        
        # Mock Path object
        mock_path = Mock()
        mock_pdfinfo = Mock()
        mock_pdfinfo.exists.return_value = True
        mock_pdftotext = Mock()
        mock_pdftotext.exists.return_value = True
        
        def truediv_side_effect(name):
            if name == "pdfinfo":
                return mock_pdfinfo
            elif name == "pdftotext":
                return mock_pdftotext
            return Mock(exists=Mock(return_value=False))
        
        mock_path.__truediv__ = Mock(side_effect=truediv_side_effect)
        mock_path_class.return_value = mock_path
        
        result = validate_poppler_path("/usr/bin")
        assert result is True


class TestFindPopplerPath:
    """Tests for find_poppler_path function."""
    
    @patch('congress_audit.pdf_utils.validate_poppler_path')
    def test_custom_path_valid(self, mock_validate):
        """Test with valid custom path."""
        mock_validate.return_value = True
        
        result = find_poppler_path("/custom/path")
        
        assert result == "/custom/path"
        mock_validate.assert_called_with("/custom/path")
    
    @patch('congress_audit.pdf_utils.validate_poppler_path')
    @patch('congress_audit.pdf_utils.os.environ.get')
    def test_env_var_path(self, mock_env_get, mock_validate):
        """Test with POPPLER_BIN environment variable."""
        mock_env_get.return_value = "/env/path"
        mock_validate.return_value = True
        
        result = find_poppler_path()
        
        assert result == "/env/path"
    
    @patch('congress_audit.pdf_utils.subprocess.run')
    @patch('congress_audit.pdf_utils.validate_poppler_path')
    @patch('congress_audit.pdf_utils.platform.system')
    @patch('congress_audit.pdf_utils.os.environ.get')
    def test_system_path(self, mock_env_get, mock_system, mock_validate, mock_run):
        """Test finding Poppler in system PATH."""
        mock_env_get.return_value = None
        mock_system.return_value = "Linux"
        mock_validate.return_value = False
        mock_run.return_value = Mock(returncode=0)
        
        result = find_poppler_path()
        
        assert result is None  # Found in PATH, no specific path needed
        mock_run.assert_called()
    
    @patch('congress_audit.pdf_utils.subprocess.run')
    @patch('congress_audit.pdf_utils.validate_poppler_path')
    @patch('congress_audit.pdf_utils.platform.system')
    @patch('congress_audit.pdf_utils.os.environ.get')
    def test_not_found(self, mock_env_get, mock_system, mock_validate, mock_run):
        """Test when Poppler is not found anywhere."""
        mock_env_get.return_value = None
        mock_system.return_value = "Linux"
        mock_validate.return_value = False
        mock_run.side_effect = FileNotFoundError()
        
        result = find_poppler_path()
        
        assert result is None


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf function."""
    
    @patch('pdfplumber.open')
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_extract_success(self, mock_exists, mock_pdf_open):
        """Test successful text extraction."""
        mock_exists.return_value = True
        
        # Mock PDF pages
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 text"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdf_open.return_value = mock_pdf
        
        text = extract_text_from_pdf("/path/to/test.pdf")
        
        assert "Page 1 text" in text
        assert "Page 2 text" in text
        mock_pdf_open.assert_called_once_with("/path/to/test.pdf")
    
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_extract_file_not_found(self, mock_exists):
        """Test with non-existent file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("/nonexistent/file.pdf")
    
    @patch('pdfplumber.open')
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_extract_pdf_error(self, mock_exists, mock_pdf_open):
        """Test handling of PDF extraction errors."""
        mock_exists.return_value = True
        mock_pdf_open.side_effect = Exception("PDF corrupted")
        
        with pytest.raises(RuntimeError):
            extract_text_from_pdf("/path/to/corrupted.pdf")


class TestExtractTextWithOcr:
    """Tests for extract_text_with_ocr function."""
    
    @patch('pytesseract.image_to_string')
    @patch('pdf2image.convert_from_path')
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_ocr_success(self, mock_exists, mock_convert, mock_ocr):
        """Test successful OCR extraction."""
        mock_exists.return_value = True
        
        # Mock images
        mock_image1 = Mock()
        mock_image2 = Mock()
        mock_convert.return_value = [mock_image1, mock_image2]
        
        # Mock OCR results
        mock_ocr.side_effect = ["OCR text page 1", "OCR text page 2"]
        
        text = extract_text_with_ocr("/path/to/scanned.pdf")
        
        assert "OCR text page 1" in text
        assert "OCR text page 2" in text
        mock_convert.assert_called_once()
        assert mock_ocr.call_count == 2
    
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_ocr_file_not_found(self, mock_exists):
        """Test OCR with non-existent file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            extract_text_with_ocr("/nonexistent/file.pdf")
    
    @patch('pdf2image.convert_from_path')
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_ocr_conversion_error(self, mock_exists, mock_convert):
        """Test handling of conversion errors."""
        mock_exists.return_value = True
        mock_convert.side_effect = Exception("Conversion failed")
        
        with pytest.raises(RuntimeError):
            extract_text_with_ocr("/path/to/bad.pdf")
    
    @patch('pytesseract.image_to_string')
    @patch('pdf2image.convert_from_path')
    @patch('congress_audit.pdf_utils.os.path.exists')
    def test_ocr_with_poppler_path(self, mock_exists, mock_convert, mock_ocr):
        """Test OCR with custom Poppler path."""
        mock_exists.return_value = True
        mock_convert.return_value = [Mock()]
        mock_ocr.return_value = "OCR text"
        
        extract_text_with_ocr("/path/to/file.pdf", poppler_path="/custom/poppler")
        
        # Verify poppler_path was passed to convert_from_path
        call_kwargs = mock_convert.call_args[1]
        assert 'poppler_path' in call_kwargs
        assert call_kwargs['poppler_path'] == "/custom/poppler"


class TestParseTradingDocument:
    """Tests for parse_trading_document function."""
    
    @patch('congress_audit.pdf_utils.extract_text_from_pdf')
    def test_parse_standard_method(self, mock_extract):
        """Test parsing with standard method."""
        mock_extract.return_value = "Sample trading document text"
        
        result = parse_trading_document("/path/to/doc.pdf")
        
        assert result['file'] == "/path/to/doc.pdf"
        assert result['extraction_method'] == "standard"
        assert result['text_length'] == len("Sample trading document text")
        assert 'raw_text' in result
        mock_extract.assert_called_once()
    
    @patch('congress_audit.pdf_utils.extract_text_with_ocr')
    def test_parse_ocr_method(self, mock_extract_ocr):
        """Test parsing with OCR method."""
        mock_extract_ocr.return_value = "OCR extracted text from scanned document"
        
        result = parse_trading_document("/path/to/scanned.pdf", use_ocr=True)
        
        assert result['file'] == "/path/to/scanned.pdf"
        assert result['extraction_method'] == "ocr"
        assert result['text_length'] > 0
        mock_extract_ocr.assert_called_once()
    
    @patch('congress_audit.pdf_utils.extract_text_from_pdf')
    def test_parse_with_poppler_path(self, mock_extract):
        """Test parsing with custom Poppler path."""
        mock_extract.return_value = "Text content"
        
        result = parse_trading_document(
            "/path/to/doc.pdf",
            poppler_path="/custom/poppler"
        )
        
        # Verify poppler_path was passed
        mock_extract.assert_called_once()
        call_args = mock_extract.call_args
        # Check if poppler_path is in the call (either as positional or keyword arg)
        assert len(call_args[0]) >= 2 or 'poppler_path' in call_args[1]
    
    @patch('congress_audit.pdf_utils.extract_text_from_pdf')
    def test_parse_error_handling(self, mock_extract):
        """Test error handling during parsing."""
        mock_extract.side_effect = RuntimeError("Extraction failed")
        
        with pytest.raises(RuntimeError):
            parse_trading_document("/path/to/bad.pdf")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
