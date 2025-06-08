#!/usr/bin/env python3
"""
Quick test script for the PDF extractor service.
"""

from app.services.extractor import create_extractor

def test_extractor():
    # Create extractor instance
    extractor = create_extractor()
    
    # Test with a sample PDF (you'll need to provide a path)
    pdf_path = "sample.pdf"  # Replace with actual PDF path
    
    try:
        result = extractor.extract_from_file(pdf_path)
        
        print(f"Extraction Method: {result['extraction_method']}")
        print(f"Page Count: {result['metadata']['page_count']}")
        print(f"Text Length: {len(result['raw_text'])}")
        print(f"First 200 chars: {result['raw_text'][:200]}...")
        
        # Test chunking
        chunks = extractor.get_text_chunks(result, max_chunk_size=500)
        print(f"Number of chunks: {len(chunks)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extractor()