# Challenge 1a: PDF Outline Extractor

## Overview
This is a solution for Challenge 1a of the Adobe India Hackathon 2025. The challenge requires implementing a PDF processing solution that extracts structured outline data from PDF documents and outputs JSON files. The solution must be containerized using Docker and meet specific performance and resource constraints.

## Features

- **Dual extraction engines**: Primary PyPDF2 with pdfminer.six fallback
- **Smart title detection**: PDF metadata first, then content-based extraction
- **Hierarchical heading detection**: Automatically classifies H1, H2, H3 levels
- **Rule-based patterns**: Supports numbered, uppercase, and title-case headings
- **Noise filtering**: Filters out dates, page numbers, footers, and other irrelevant content
- **Batch processing**: Processes all PDFs in input directory automatically
- **Containerized**: Ready-to-use Docker container for AMD64 architecture
- **Performance optimized**: Handles large PDFs efficiently within time constraints

## Project Structure

```
AdoView/
├── README.md                      # This file
└── challange1a/
    ├── Dockerfile                 # Container configuration
    ├── process_pdf.py             # Main processing script
    ├── requirements.txt           # Python dependencies
    ├── output/                    # Generated output files
    │   ├── file01.json
    │   ├── file02.json
    │   ├── file03.json
    │   └── file04.json
    └── sample_dataset/
        ├── output/                # Sample output files
        ├── pdfs/                  # Sample PDF files
        └── schema/                # JSON schema for output format
            └── output_schema.json
```

## Official Challenge Requirements

### Build Command
```bash
cd challange1a
docker build --platform linux/amd64 -t adoview.pdfprocessor .
```

### Run Command
```bash
cd challange1a
docker run --rm \
  -v $(pwd)/sample_dataset/pdfs:/app/input:ro \
  -v $(pwd)/output:/app/output \
  --network none \
  adoview.pdfprocessor
```

### Critical Constraints
- **Execution Time**: ≤ 10 seconds for a 50-page PDF
- **Model Size**: ≤ 200MB (if using ML models)
- **Network**: No internet access allowed during runtime execution
- **Runtime**: Must run on CPU (amd64) with 8 CPUs and 16 GB RAM
- **Architecture**: Must work on AMD64, not ARM-specific

### Key Requirements
- **Automatic Processing**: Process all PDFs from `/app/input` directory
- **Output Format**: Generate `filename.json` for each `filename.pdf`
- **Input Directory**: Read-only access only
- **Open Source**: All libraries, models, and tools must be open source
- **Cross-Platform**: Test on both simple and complex PDFs

## Output Format

The extractor produces JSON files with the following schema:

```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

## Usage

### Docker Processing (Recommended)

```bash
# Build the container
cd challange1a
docker build --platform linux/amd64 -t adoview.pdfprocessor .

# Run the container (batch processing)
docker run --rm \
  -v $(pwd)/sample_dataset/pdfs:/app/input:ro \
  -v $(pwd)/output:/app/output \
  --network none \
  adoview.pdfprocessor
```

### Local Processing

```bash
# Install dependencies
cd challange1a
pip install -r requirements.txt

# Process a single PDF
python process_pdf.py -i input.pdf -o output.json
```

## Sample Data

- `challange1a/sample_dataset/pdfs/`: Contains sample PDF files for testing
- `challange1a/sample_dataset/output/`: Contains example output JSON files
- `challange1a/sample_dataset/schema/`: Contains JSON schema for validation

## Libraries Used

- **PyPDF2 (3.0.1)**: Primary PDF text extraction
- **pdfminer.six (20231228)**: Fallback text extraction for complex layouts

## Performance

- **Target**: ≤ 10 seconds on 50-page PDF (8 CPU cores, 16 GB RAM)
- **Docker image size**: Optimized to stay under 200 MB
- **Memory usage**: Efficient, processes pages sequentially
- **Rule-based approach**: Fast processing without heavy ML models

## Testing

### Local Testing
```bash
# Test with sample data
cd challange1a
docker run --rm \
  -v $(pwd)/sample_dataset/pdfs:/app/input:ro \
  -v $(pwd)/test_output:/app/output \
  --network none \
  adoview.pdfprocessor
```

### Validation Checklist
- [x] All PDFs in input directory are processed
- [x] JSON output files are generated for each PDF
- [x] Output format matches required structure
- [x] Output conforms to schema in `challange1a/sample_dataset/schema/output_schema.json`
- [x] Solution works without internet access
- [x] Compatible with AMD64 architecture
- [x] Uses only open source libraries

## Implementation Details

The solution uses a rule-based approach for heading detection with patterns for:
- Numbered headings (1., 1.1, 1.1.1)
- Uppercase headings (INTRODUCTION, BACKGROUND)
- Title case headings (Experimental Setup)

Noise filtering removes common non-content elements like dates, page numbers, and footers.

The dual extraction engine ensures compatibility with various PDF formats by falling back to pdfminer.six when PyPDF2 fails.
