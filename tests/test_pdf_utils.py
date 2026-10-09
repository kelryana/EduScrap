import pytest
from unittest.mock import patch, MagicMock
import io
from datetime import datetime, timedelta
from io import BytesIO

from backend.pdf_utils import (
    extrair_data_de_texto,
    verificar_status,
    baixar_pdf,
    extrair_texto_pdf,
    extrair_data_vencimento_pdf,
    extrair_data_vencimento_hibrido,
    extrair_e_validar_data
)


class TestExtrairDataDeTexto:
    def test_extrair_data_de_texto_with_valid_date_formats(self):
        
        text = "O edital foi publicado em 15/03/2024 e as inscrições terminam em 30/04/2024."
        result = extrair_data_de_texto(text)
        assert result is not None
       
        assert result == "2024-03-15"

        text = "As inscrições começam em 15 de março de 2024 e terminam em 30 de abril de 2024."
        result = extrair_data_de_texto(text)
        assert result == "2024-03-15"

        text = "Inicio: 01/01/2024 | Término: 31 de dezembro de 2024"
        result = extrair_data_de_texto(text)
        assert result == "2024-01-01"

        text = "Evento em 25-12-2024 e 05.06.2024"
        result = extrair_data_de_texto(text)
        assert result == "2024-12-25"

        text = "Datas: 2024/03/15, 2025.04.30 e 2026-05-15"
        result = extrair_data_de_texto(text)
        assert result == "2024-03-15"

    def test_extrair_data_de_texto_with_no_dates(self):
        """Test that function returns None when no dates are present"""
        text = "Este texto não contém datas válidas."
        result = extrair_data_de_texto(text)
        assert result is None

    def test_extrair_data_de_texto_with_invalid_dates(self):
        """Test handling of invalid date strings"""
        text = "Datas inválidas como 99/99/9999 ou 30/02/2024."
        result = extrair_data_de_texto(text)
        # Invalid dates should be filtered out, returning None
        assert result is None

    def test_extrair_data_de_texto_edge_cases(self):
        """Test edge cases for date extraction"""
        # Very short text
        result = extrair_data_de_texto("Hi")
        assert result is None

        # Text with numbers but not dates
        result = extrair_data_de_texto("This has numbers 123 but no dates")
        assert result is None

        # Text with invalid dates that should be handled gracefully
        text = "Data inválida: 30/02/2024 e 99/99/9999"
        result = extrair_data_de_texto(text)
        assert result is None

        # Text with valid and invalid dates together
        text = "Data válida 15/03/2024 e inválida 99/99/9999"
        result = extrair_data_de_texto(text)
        assert result is not None  # Should extract valid date

        # Text with dates in different formats
        text = "Datas: 15/03/2024, 30 de abril de 2024, 2025-05-15"
        result = extrair_data_de_texto(text)
        assert result is not None  # Should extract one of the valid dates


class TestVerificarStatus:
    """Test cases for verificar_status function"""

    def test_verificar_status_future_date(self):
        """Test status verification with future date"""
        # Create a date in the future
        future_date = (datetime.now().replace(year=datetime.now().year + 1)).strftime('%Y-%m-%d')
        result = verificar_status(future_date)
        assert result == "vigente"

    def test_verificar_status_past_date(self):
        """Test status verification with past date"""
        # Create a date in the past
        past_date = (datetime.now().replace(year=datetime.now().year - 1)).strftime('%Y-%m-%d')
        result = verificar_status(past_date)
        assert result == "vencido"

    def test_verificar_status_current_date(self):
        """Test status verification with current date"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        result = verificar_status(current_date)
        assert result == "vigente"

        # Test current date with time component
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = verificar_status(current_datetime)
        assert result == "vigente"

    def test_verificar_status_none_input(self):
        """Test status verification with None input"""
        result = verificar_status(None)
        assert result == "vigente"

    def test_verificar_status_invalid_date_format(self):
        """Test status verification with invalid date format"""
        result = verificar_status("invalid-date-format")
        assert result == "vigente"


class TestBaixarPdf:
    """Test cases for baixar_pdf function using mocks"""

    @patch('backend.pdf_utils.requests.get')
    def test_baixar_pdf_success(self, mock_get):
        """Test successful PDF download"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'%PDF-1.4 fake pdf content'
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the function
        result = baixar_pdf('http://example.com/document.pdf')
        
        # Assertions
        mock_get.assert_called_once()
        assert result is not None
        assert isinstance(result, BytesIO)

    @patch('backend.pdf_utils.requests.get')
    def test_baixar_pdf_request_exception(self, mock_get):
        """Test PDF download with request exception"""
        # Mock a request exception
        mock_get.side_effect = Exception("Network error")

        # Test the function - should handle the exception gracefully
        result = baixar_pdf('http://example.com/document.pdf')
        assert result is None

    @patch('backend.pdf_utils.requests.get')
    def test_baixar_pdf_http_error(self, mock_get):
        """Test PDF download with HTTP error"""
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Test the function
        result = baixar_pdf('http://example.com/document.pdf')
        assert result is None

    @patch('backend.pdf_utils.requests.get')
    def test_baixar_pdf_non_pdf_content_type(self, mock_get):
        """Test PDF download with non-PDF content type"""
        # Mock a response with non-PDF content-type
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Not a PDF'
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        # Test the function
        result = baixar_pdf('http://example.com/document.html')
        assert result is None


class TestExtrairTextoPdf:
    """Test cases for extrair_texto_pdf function using mocks"""

    @patch('backend.pdf_utils.PDFMINER_AVAILABLE', True)
    @patch('backend.pdf_utils.extract_text')
    def test_extrair_texto_pdf_valid_content(self, mock_extract_text):
        """Test text extraction from a valid PDF"""
        # Mock the text extraction
        mock_extract_text.return_value = "Conteúdo do documento PDF de exemplo"
        
        # Create a BytesIO object to simulate PDF content
        pdf_content = BytesIO(b'%PDF-1.4 fake pdf content')

        # Test the function
        result = extrair_texto_pdf(pdf_content)
        
        # Assertions
        assert "Conteúdo do documento PDF de exemplo" in result
        assert isinstance(result, str)

    @patch('backend.pdf_utils.PDFMINER_AVAILABLE', True)
    @patch('backend.pdf_utils.extract_text')
    def test_extrair_texto_pdf_empty_content(self, mock_extract_text):
        """Test text extraction from an empty PDF"""
        # Mock empty text extraction
        mock_extract_text.return_value = ""
        
        pdf_content = BytesIO(b'%PDF-1.4 empty pdf content')

        # Test the function
        result = extrair_texto_pdf(pdf_content)
        
        # Should return empty string
        assert result == ""

    @patch('backend.pdf_utils.PDFMINER_AVAILABLE', False)
    def test_extrair_texto_pdf_pdfminer_not_available(self):
        """Test text extraction when pdfminer is not available"""
        pdf_content = BytesIO(b'%PDF-1.4 pdf content')
        
        # Test the function
        result = extrair_texto_pdf(pdf_content)
        
        # Should return empty string when pdfminer is not available
        assert result == ""

    @patch('backend.pdf_utils.extract_text')
    def test_extrair_texto_pdf_extraction_error(self, mock_extract_text):
        """Test handling of PDF text extraction errors"""
        # Mock an exception during text extraction
        mock_extract_text.side_effect = Exception("PDF parsing error")
        
        pdf_content = BytesIO(b'%PDF-1.4 problematic pdf content')

        # Test the function
        result = extrair_texto_pdf(pdf_content)
        
        # Should handle gracefully and return empty string
        assert result == ""


class TestExtrairDataVencimentoPdf:
    """Test cases for extrair_data_vencimento_pdf function"""

    @patch('backend.pdf_utils.baixar_pdf')
    @patch('backend.pdf_utils.extrair_texto_pdf')
    @patch('backend.pdf_utils.extrair_data_de_texto')
    def test_extrair_data_vencimento_pdf_success(self, mock_extrair_data, mock_extrair_texto, mock_baixar_pdf):
        """Test successful date extraction from PDF"""
        # Mock the PDF download
        mock_baixar_pdf.return_value = BytesIO(b'%PDF-1.4 test pdf')
        # Mock text extraction
        mock_extrair_texto.return_value = "Edital com data limite em 15/03/2024"
        # Mock date extraction
        mock_extrair_data.return_value = "2024-03-15"

        # Test the function
        result = extrair_data_vencimento_pdf('http://example.com/test.pdf')
        
        # Assertions
        assert result == "2024-03-15"
        mock_baixar_pdf.assert_called_once()
        mock_extrair_texto.assert_called_once()
        mock_extrair_data.assert_called_once()

    @patch('backend.pdf_utils.baixar_pdf')
    def test_extrair_data_vencimento_pdf_download_failure(self, mock_baixar_pdf):
        """Test date extraction when PDF download fails"""
        # Mock failed download
        mock_baixar_pdf.return_value = None

        # Test the function
        result = extrair_data_vencimento_pdf('http://example.com/test.pdf')
        
        # Should return None when download fails
        assert result is None


class TestExtrairDataVencimentoHibrido:
    """Test cases for extrair_data_vencimento_hibrido function"""

    @patch('backend.pdf_utils.extrair_data_de_texto')
    def test_extrair_data_vencimento_hibrido_html_priority(self, mock_extrair_data):
        """Test that HTML takes priority over PDF"""
        # Mock date extraction from HTML
        mock_extrair_data.return_value = "2024-05-20"

        # Test the function with both HTML and PDF
        result = extrair_data_vencimento_hibrido("HTML with date 20/05/2024", "http://example.com/test.pdf")
        
        # Should return date from HTML, not PDF
        assert result == "2024-05-20"

    @patch('backend.pdf_utils.extrair_data_de_texto')
    @patch('backend.pdf_utils.extrair_data_vencimento_pdf')
    def test_extrair_data_vencimento_hibrido_fallback_to_pdf(self, mock_extrair_pdf, mock_extrair_html):
        """Test fallback to PDF when HTML doesn't contain date"""
        # Mock HTML extraction to return None
        mock_extrair_html.return_value = None
        # Mock PDF extraction to return a date
        mock_extrair_pdf.return_value = "2024-06-15"

        # Test the function with both HTML and PDF
        result = extrair_data_vencimento_hibrido("HTML without date", "http://example.com/test.pdf")
        
        # Should return date from PDF since HTML didn't have one
        assert result == "2024-06-15"


class TestExtrairEValidarData:
    """Test cases for extrair_e_validar_data function"""

    @patch('backend.pdf_utils.extrair_data_vencimento_hibrido')
    def test_extrair_e_validar_data_success(self, mock_extrair_hibrido):
        """Test successful extraction and validation of date"""
        # Mock hybrid extraction to return a future date
        mock_extrair_hibrido.return_value = "2025-12-31"

        # Test the function
        data, status = extrair_e_validar_data("HTML content", "http://example.com/test.pdf")
        
        # Should return the extracted date and 'vigente' status
        assert data == "2025-12-31"
        assert status == "vigente"

    @patch('backend.pdf_utils.extrair_data_vencimento_hibrido')
    def test_extrair_e_validar_data_expired(self, mock_extrair_hibrido):
        """Test extraction and validation with expired date"""
        # Mock hybrid extraction to return a past date
        mock_extrair_hibrido.return_value = "2020-01-01"

        # Test the function
        data, status = extrair_e_validar_data("HTML content", "http://example.com/test.pdf")
        
        # Should return the extracted date and 'vencido' status
        assert data == "2020-01-01"
        assert status == "vencido"