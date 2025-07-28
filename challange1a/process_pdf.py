#!/usr/bin/env python3
"""
PDF Outline Extractor

A lightweight, rule-based extractor that takes a PDF and produces a JSON outline
containing the document title and headings with their respective page numbers.
"""
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 not found. Please install: pip install PyPDF2", file=sys.stderr)
    sys.exit(1)

try:
    from pdfminer.high_level import extract_text
except ImportError:
    print("pdfminer.six not found. Please install: pip install pdfminer.six", file=sys.stderr)
    sys.exit(1)


class PDFOutlineExtractor:
    """PDF outline extractor using rule-based pattern matching."""
    
    def __init__(self):
        # Regex patterns for heading detection
        self.num_pat = re.compile(r"^\d+(\.\d+)*[\.\s]+.+")  # "1. Introduction", "2.1 Methodology"
        self.up_pat = re.compile(r"^(?=.*[A-Z])[A-Z0-9. ]+$")  # "BACKGROUND", "RESULTS AND DISCUSSION"
        self.title_pat = re.compile(r"^[A-Z][a-zA-Z0-9 ,\-\:]{4,}$")  # "Experimental Setup"
        
        # Patterns to filter out noise (dates, footers, etc.)
        self.noise_patterns = [
            re.compile(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$"),
            re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$"),
            re.compile(r"^page\s+\d+$", re.IGNORECASE),
            re.compile(r"^copyright.*$", re.IGNORECASE),
            re.compile(r"^\d+$"),
            re.compile(r"^[^\w\s]+$"),
        ]
        
        # Store detected title to filter it out from headings
        self._detected_title = None
    
    def extract_text_pypdf2(self, pdf_path: str) -> List[Tuple[str, int]]:
        """Extract text using PyPDF2, returns list of (text, page_number) tuples."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                pages_text = []
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        pages_text.append((text, page_num))
                return pages_text
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}", file=sys.stderr)
            return []
    
    def extract_text_pdfminer(self, pdf_path: str) -> List[Tuple[str, int]]:
        """Extract text using pdfminer as fallback, returns list of (text, page_number) tuples."""
        try:
            full_text = extract_text(pdf_path)
            # Split by form feed character to separate pages
            pages = full_text.split('\x0c')
            pages_text = []
            for page_num, page_text in enumerate(pages, 1):
                if page_text.strip():
                    pages_text.append((page_text, page_num))
            return pages_text
        except Exception as e:
            print(f"pdfminer extraction failed: {e}", file=sys.stderr)
            return []
    
    def extract_title_from_metadata(self, pdf_path: str) -> Optional[str]:
        """Extract title from PDF metadata."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title.strip()
                    if title and len(title) > 2:
                        return title
        except Exception as e:
            print(f"Metadata extraction failed: {e}", file=sys.stderr)
        
        return None
    
    def extract_title_from_content(self, pages_text: List[Tuple[str, int]]) -> str:
        """Extract title from document content (first non-blank line)."""
        for text, _ in pages_text:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 3 and not self.is_noise(line):
                    return line
        
        return "Untitled Document"
    
    def is_noise(self, line: str) -> bool:
        """Check if a line matches noise patterns."""
        line = line.strip()
        if len(line) < 3:
            return True
        
        for pattern in self.noise_patterns:
            if pattern.match(line):
                return True
        
        return False
    
    def is_heading(self, line: str) -> bool:
        """Check if a line matches heading patterns."""
        line = line.strip()
        
        # Skip if it's noise
        if self.is_noise(line):
            return False
        
        # Skip if it's the document title
        if hasattr(self, '_detected_title') and self._detected_title and line == self._detected_title:
            return False
        
        # Skip if it's too long (likely content text)
        if len(line) > 100:
            return False
        
        # Skip if it contains repeated phrases (indicates wrapped content)
        if '. This is the content for section:' in line:
            return False
        
        # Skip if it contains too much lowercase text (likely content)
        if len(line) > 50 and sum(1 for c in line if c.islower()) > len(line) * 0.7:
            return False
        
        # Skip if it ends with punctuation that suggests it's part of a sentence
        if line.endswith(('.', ',', ';', '!', '?')) and not line.endswith('...'):
            return False
        
        # Check numbered headings
        if self.num_pat.match(line):
            return True
        
        # Check uppercase headings (but not too long)
        if len(line) <= 100 and self.up_pat.match(line):
            return True
        
        # Check title case headings
        if self.title_pat.match(line):
            return True

        return False
    
    def extract_headings(self, pages_text: List[Tuple[str, int]]) -> List[Dict[str, any]]:
        """Extract headings from all pages."""
        headings = []
        
        for text, page_num in pages_text:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if self.is_heading(line):
                    level = self.determine_heading_level(line)
                    headings.append({
                        "level": level,
                        "text": line,
                        "page": page_num
                    })
        
        return headings
    
    def determine_heading_level(self, line: str) -> str:
        """Determine the heading level (H1, H2, H3) based on patterns."""
        line = line.strip()
        
        # H1: Major numbered sections (1., 2., 3.) or long uppercase
        if re.match(r"^\d+\.\s+", line) or (len(line) > 15 and self.up_pat.match(line)):
            return "H1"
        
        # H2: Subsections (1.1, 2.1) or short uppercase or title case
        elif re.match(r"^\d+\.\d+\s+", line) or (len(line) <= 15 and self.up_pat.match(line)) or self.title_pat.match(line):
            return "H2"
        
        # H3: Sub-subsections (1.1.1) or other patterns
        else:
            return "H3"
    
    def extract_outline(self, pdf_path: str) -> Dict[str, any]:
        """Extract complete outline from PDF."""
        # Try to extract text using PyPDF2 first
        pages_text = self.extract_text_pypdf2(pdf_path)
        
        # If PyPDF2 fails or returns empty, use pdfminer as fallback
        if not pages_text:
            print("PyPDF2 failed, trying pdfminer...", file=sys.stderr)
            pages_text = self.extract_text_pdfminer(pdf_path)
        
        if not pages_text:
            raise ValueError("Could not extract text from PDF")
        
        # Extract title
        title = self.extract_title_from_metadata(pdf_path)
        if not title:
            title = self.extract_title_from_content(pages_text)
        
        self._detected_title = title
        
        # Extract headings
        headings = self.extract_headings(pages_text)
        
        return {
            "title": title,
            "outline": headings
        }


def main():
    """Main function for batch processing PDFs from input directory."""
    # For backward compatibility, check if CLI arguments are provided
    if len(sys.argv) > 1 and ('-i' in sys.argv or '--input' in sys.argv or '-h' in sys.argv or '--help' in sys.argv):
        main_cli()
        return
    
    # Batch processing mode for Docker container
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        print(f"Input directory {input_dir} not found!", file=sys.stderr)
        sys.exit(1)
    
    # Find all PDF files in input directory
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in input directory!", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    extractor = PDFOutlineExtractor()
    success_count = 0
    
    for pdf_path in pdf_files:
        try:
            print(f"Processing: {pdf_path.name}")
            outline = extractor.extract_outline(str(pdf_path))
            
            # Generate output filename
            output_filename = pdf_path.stem + ".json"
            output_path = output_dir / output_filename
            
            # Save outline to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(outline, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Generated: {output_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Failed to process {pdf_path.name}: {e}", file=sys.stderr)
    
    print(f"\nProcessing complete: {success_count}/{len(pdf_files)} files successful")
    
    if success_count == 0:
        sys.exit(1)


def main_cli():
    """CLI function for single file processing (backward compatibility)."""
    parser = argparse.ArgumentParser(
        description="Extract outline from PDF file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_pdf.py -i document.pdf -o outline.json
  python process_pdf.py --input report.pdf --output results.json
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input PDF file path"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found!", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.pdf':
        print(f"Error: Input file '{input_path}' is not a PDF!", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract outline
    try:
        extractor = PDFOutlineExtractor()
        outline = extractor.extract_outline(str(input_path))
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Outline extracted to: {output_path}")
        
    except Exception as e:
        print(f"✗ Error processing PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
