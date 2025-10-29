"""
Test client for Certificate OCR API
Usage: python test_client.py <path_to_file>
"""

import requests
import sys
import json
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}\n")
        return False

def test_extract(file_path):
    """Test extract endpoint"""
    print(f"Testing extract endpoint with file: {file_path}")
    
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            response = requests.post(f"{API_URL}/extract", files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nExtraction Results:")
            print("=" * 50)
            print(f"Filename: {result['filename']}")
            print(f"Extracted Text Length: {result['extracted_text_length']} characters")
            print("\nMetadata:")
            print("-" * 50)
            for key, value in result['metadata'].items():
                print(f"{key}: {value}")
            print("=" * 50)
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <path_to_certificate_file>")
        print("Example: python test_client.py certificate.jpg")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Test health first
    if not test_health():
        print("Health check failed. Is the API running?")
        sys.exit(1)
    
    # Test extraction
    if test_extract(file_path):
        print("\n✓ Test completed successfully!")
    else:
        print("\n✗ Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()