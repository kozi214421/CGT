"""
Unit tests for congress_audit.pdf_utils module.
"""
import os
import pytest
from unittest.mock import Mock, patch
from congress_audit.pdf_utils import (
    discover_poppler_path,
    _validate_poppler_path,
    parse_pdf,
    _parse_with_pdfplumber,
    _parse_with_ocr
)


class TestDiscoverPopplerPath:
    """Tests for discover_poppler_path function."""

    def test_cli_arg_priority(self):
        """Test that CLI argument has highest priority."""
        with patch('congress_audit.pdf_utils._validate_poppler_path') as mock_validate:
            mock_validate.side_effect = lambda path: path == "/cli/path"

            result = discover_poppler_path(
                cli_arg="/cli/path",
                env_var_name="POPLER_BIN"
            )
            assert result == "/cli/path"

    def test_env_var_fallback(self):
        """Test fallback to environment variable."""
        with patch.dict(os.environ, {'POPLER_BIN': '/env/path'}):
            with patch('congress_audit.pdf_utils._validate_poppler_path') as mock_validate:
                mock_validate.side_effect = lambda path: path == "/env/path"

                result = discover_poppler_path(
                    cli_arg=None,
                    env_var_name="POPLER_BIN"
                )
                assert result == "/env/path"

    def test_common_location_fallback(self):
        """Test fallback to common system locations."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('congress_audit.pdf_utils._validate_poppler_path') as mock_validate:
                # Only /usr/bin is valid
                mock_validate.side_effect = lambda path: path == "/usr/bin"

                result = discover_poppler_path(
                    cli_arg=None,
                    env_var_name="POPLER_BIN"
                )
                assert result == "/usr/bin"

    def test_no_poppler_found(self):
        """Test when Poppler is not found anywhere."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('congress_audit.pdf_utils._validate_poppler_path') as mock_validate:
                mock_validate.return_value = False

                result = discover_poppler_path(
                    cli_arg=None,
                    env_var_name="POPLER_BIN"
                )
                assert result is None

    def test_invalid_cli_arg_tries_env(self):
        """Test that invalid CLI arg falls back to env var."""
        with patch.dict(os.environ, {'POPLER_BIN': '/env/path'}):
            with patch('congress_audit.pdf_utils._validate_poppler_path') as mock_validate:
                # CLI arg is invalid, env path is valid
                mock_validate.side_effect = lambda path: path == "/env/path"

                result = discover_poppler_path(
                    cli_arg="/invalid/path",
                    env_var_name="POPLER_BIN"
                )
                assert result == "/env/path"


class TestValidatePopplerPath:
    """Tests for _validate_poppler_path function."""

    def test_valid_path_with_pdfinfo(self):
        """Test validation with pdfinfo utility present."""
        with patch('os.path.isdir') as mock_isdir:
            with patch('os.path.isfile') as mock_isfile:
                mock_isdir.return_value = True
                mock_isfile.side_effect = lambda p: 'pdfinfo' in p

                assert _validate_poppler_path("/usr/bin") is True

    def test_valid_path_with_pdftoppm(self):
        """Test validation with pdftoppm utility present."""
        with patch('os.path.isdir') as mock_isdir:
            with patch('os.path.isfile') as mock_isfile:
                mock_isdir.return_value = True
                mock_isfile.side_effect = lambda p: 'pdftoppm' in p

                assert _validate_poppler_path("/usr/bin") is True

    def test_invalid_path_not_directory(self):
        """Test validation fails when path is not a directory."""
        with patch('os.path.isdir') as mock_isdir:
            mock_isdir.return_value = False

            assert _validate_poppler_path("/not/a/dir") is False

    def test_invalid_path_no_utilities(self):
        """Test validation fails when no Poppler utilities found."""
        with patch('os.path.isdir') as mock_isdir:
            with patch('os.path.isfile') as mock_isfile:
                mock_isdir.return_value = True
                mock_isfile.return_value = False

                assert _validate_poppler_path("/usr/bin") is False

    def test_none_path(self):
        """Test validation with None path."""
        assert _validate_poppler_path(None) is False

    def test_empty_path(self):
        """Test validation with empty string path."""
        assert _validate_poppler_path("") is False


class TestParsePdf:
    """Tests for parse_pdf function."""

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_pdf("/nonexistent/file.pdf")

    def test_successful_pdfplumber_parse(self):
        """Test successful parsing with pdfplumber."""
        with patch('os.path.isfile') as mock_isfile:
            with patch('congress_audit.pdf_utils._parse_with_pdfplumber') as mock_parse:
                mock_isfile.return_value = True
                mock_parse.return_value = {
                    'success': True,
                    'text': 'Sample text content',
                    'method': 'pdfplumber',
                    'pages': 1
                }

                result = parse_pdf("/path/to/file.pdf")

                assert result['success'] is True
                assert result['method'] == 'pdfplumber'
                assert 'text' in result

    def test_fallback_to_ocr(self):
        """Test fallback to OCR when pdfplumber fails."""
        with patch('os.path.isfile') as mock_isfile:
            with patch('congress_audit.pdf_utils._parse_with_pdfplumber') as mock_plumber:
                with patch('congress_audit.pdf_utils._parse_with_ocr') as mock_ocr:
                    mock_isfile.return_value = True

                    # pdfplumber fails
                    mock_plumber.return_value = {
                        'success': False,
                        'text': '',
                        'method': 'pdfplumber',
                        'pages': 0
                    }

                    # OCR succeeds
                    mock_ocr.return_value = {
                        'success': True,
                        'text': 'OCR extracted text',
                        'method': 'ocr',
                        'pages': 1
                    }

                    result = parse_pdf("/path/to/file.pdf")

                    assert result['success'] is True
                    assert result['method'] == 'ocr'

    def test_all_methods_fail(self):
        """Test that ValueError is raised when all methods fail."""
        with patch('os.path.isfile') as mock_isfile:
            with patch('congress_audit.pdf_utils._parse_with_pdfplumber') as mock_plumber:
                with patch('congress_audit.pdf_utils._parse_with_ocr') as mock_ocr:
                    mock_isfile.return_value = True

                    # Both methods fail
                    mock_plumber.return_value = {
                        'success': False,
                        'text': '',
                        'method': 'pdfplumber',
                        'pages': 0
                    }
                    mock_ocr.return_value = {
                        'success': False,
                        'text': '',
                        'method': 'ocr',
                        'pages': 0
                    }

                    with pytest.raises(ValueError):
                        parse_pdf("/path/to/file.pdf")

    def test_poppler_path_passed_to_ocr(self):
        """Test that poppler_path is passed to OCR method."""
        with patch('os.path.isfile') as mock_isfile:
            with patch('congress_audit.pdf_utils._parse_with_pdfplumber') as mock_plumber:
                with patch('congress_audit.pdf_utils._parse_with_ocr') as mock_ocr:
                    mock_isfile.return_value = True
                    mock_plumber.return_value = {'success': False, 'text': '', 'method': 'pdfplumber', 'pages': 0}
                    mock_ocr.return_value = {'success': True, 'text': 'text', 'method': 'ocr', 'pages': 1}

                    parse_pdf("/path/to/file.pdf", poppler_path="/custom/path")

                    # Check that OCR was called with poppler_path
                    mock_ocr.assert_called_once_with("/path/to/file.pdf", "/custom/path")

    def test_disable_fallback(self):
        """Test that fallback can be disabled."""
        with patch('os.path.isfile') as mock_isfile:
            with patch('congress_audit.pdf_utils._parse_with_pdfplumber') as mock_plumber:
                with patch('congress_audit.pdf_utils._parse_with_ocr') as mock_ocr:
                    mock_isfile.return_value = True
                    mock_plumber.return_value = {'success': False, 'text': '', 'method': 'pdfplumber', 'pages': 0}

                    with pytest.raises(ValueError):
                        parse_pdf("/path/to/file.pdf", use_fallback=False)

                    # OCR should not be called
                    mock_ocr.assert_not_called()


class TestParseWithPdfplumber:
    """Tests for _parse_with_pdfplumber function."""

    def test_successful_parse(self):
        """Test successful PDF parsing with pdfplumber."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page 1 text"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        with patch('pdfplumber.open') as mock_open:
            mock_open.return_value = mock_pdf

            result = _parse_with_pdfplumber("/path/to/file.pdf")

            assert result['success'] is True
            assert result['text'] == "Page 1 text"
            assert result['method'] == 'pdfplumber'
            assert result['pages'] == 1

    def test_multiple_pages(self):
        """Test parsing PDF with multiple pages."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        with patch('pdfplumber.open') as mock_open:
            mock_open.return_value = mock_pdf

            result = _parse_with_pdfplumber("/path/to/file.pdf")

            assert result['success'] is True
            assert "Page 1" in result['text']
            assert "Page 2" in result['text']
            assert result['pages'] == 2

    def test_import_error(self):
        """Test handling when pdfplumber is not installed."""
        with patch.dict('sys.modules', {'pdfplumber': None}):
            result = _parse_with_pdfplumber("/path/to/file.pdf")

            assert result['success'] is False
            assert result['method'] == 'pdfplumber'


class TestParseWithOcr:
    """Tests for _parse_with_ocr function."""

    def test_successful_ocr(self):
        """Test successful OCR parsing."""
        mock_image = Mock()

        with patch('pdf2image.convert_from_path') as mock_convert:
            with patch('pytesseract.image_to_string') as mock_tesseract:
                mock_convert.return_value = [mock_image]
                mock_tesseract.return_value = "OCR text"

                result = _parse_with_ocr("/path/to/file.pdf")

                assert result['success'] is True
                assert result['text'] == "OCR text"
                assert result['method'] == 'ocr'
                assert result['pages'] == 1

    def test_multiple_pages_ocr(self):
        """Test OCR with multiple pages."""
        mock_image1 = Mock()
        mock_image2 = Mock()

        with patch('pdf2image.convert_from_path') as mock_convert:
            with patch('pytesseract.image_to_string') as mock_tesseract:
                mock_convert.return_value = [mock_image1, mock_image2]
                mock_tesseract.side_effect = ["Page 1", "Page 2"]

                result = _parse_with_ocr("/path/to/file.pdf")

                assert result['success'] is True
                assert "Page 1" in result['text']
                assert "Page 2" in result['text']
                assert result['pages'] == 2

    def test_poppler_path_used(self):
        """Test that poppler_path is passed to convert_from_path."""
        mock_image = Mock()

        with patch('pdf2image.convert_from_path') as mock_convert:
            with patch('pytesseract.image_to_string') as mock_tesseract:
                mock_convert.return_value = [mock_image]
                mock_tesseract.return_value = "text"

                _parse_with_ocr("/path/to/file.pdf", poppler_path="/custom/path")

                mock_convert.assert_called_once_with(
                    "/path/to/file.pdf",
                    poppler_path="/custom/path"
                )

    def test_import_error(self):
        """Test handling when OCR dependencies not installed."""
        with patch.dict('sys.modules', {'pytesseract': None}):
            result = _parse_with_ocr("/path/to/file.pdf")

            assert result['success'] is False
            assert result['method'] == 'ocr'
