# Certificate Metadata Extraction API

A FastAPI-based REST API that extracts metadata from certificate images and PDFs using OCR (EasyOCR) and AI (Google Gemini).

## Features

- 📄 Extract text from PDF and image files (JPG, PNG, TIFF, BMP)
- 🤖 AI-powered metadata extraction using Google Gemini
- 🔍 OCR support with EasyOCR
- 📊 Structured JSON output
- 🚀 Fast and efficient processing
- 🐳 Docker support

## Project Structure

```
certificate-ocr-api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── README.md           # Documentation
└── test_client.py      # Test client script
```

## Prerequisites

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Download Poppler from [here](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH.

## Installation

### Option 1: Local Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd certificate-ocr-api
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. **Run the application:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker Installation

1. **Build and run with Docker:**
```bash
docker build -t certificate-ocr-api .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here certificate-ocr-api
```

2. **Or use Docker Compose:**
```bash
docker-compose up --build
```

## API Endpoints

### 1. Root Endpoint
```
GET /
```
Returns API information and available endpoints.

### 2. Health Check
```
GET /health
```
Returns API health status and service availability.

### 3. Extract Metadata
```
POST /extract
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF or image file)

**Response:**
```json
{
  "status": "success",
  "filename": "certificate.jpg",
  "extracted_text_length": 450,
  "metadata": {
    "Student Name": "John Doe",
    "University Name": "Harvard University",
    "Degree Name": "Master of Arts",
    "Specialization": "History",
    "Grade": "A",
    "Certificate Id": "CERT123",
    "Registration Number": "REG456",
    "Date of Issue": "2023-05-15"
  }
}
```

## Usage Examples

### Python (requests)

```python
import requests

url = "http://localhost:8000/extract"
files = {"file": open("certificate.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### cURL

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@certificate.jpg"
```

### JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/extract', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Testing

Use the provided test client:

```bash
python test_client.py path/to/certificate.jpg
```

## Configuration

Edit `.env` file for configuration:

```env
GEMINI_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## Supported File Formats

- **Images:** JPG, JPEG, PNG, TIFF, BMP
- **Documents:** PDF (multi-page supported)
- **Max file size:** 10MB

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid file type, no text extracted)
- `500`: Internal server error

## Performance Considerations

- EasyOCR reader is initialized once at startup for better performance
- Temporary files are automatically cleaned up
- Large PDFs may take longer to process

## Troubleshooting

### "No text could be extracted"
- Ensure image is clear and readable
- Check if the image contains actual text
- Try increasing image resolution

### "poppler not found"
- Install poppler-utils as described in Prerequisites
- Ensure poppler is in your system PATH

### "Gemini API error"
- Verify your API key is correct
- Check if you have available API quota
- Ensure you have internet connectivity

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.