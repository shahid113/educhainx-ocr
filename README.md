---
title: Tesseract FastAPI (CPU Only)
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Tessaract + FastAPI (CPU-friendly OCR)

### ✔ Extract text from PDFs  
### ✔ Extract text from any image  
### ✔ Works on Hugging Face Free Tier  

---

## 🟩 Endpoint: `/extract`

### Upload image or PDF

```bash
curl -X POST "https://your-space-url/extract" \
  -F "file=@document.pdf"
