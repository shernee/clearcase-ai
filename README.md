# Notice Explainer

A web application that helps people understand their immigration notices by providing clear, anxiety-aware explanations in plain English. Users can paste notice text or upload photos/PDFs of their immigration documents to receive structured explanations.

## Features

- **Text & File Upload**: Accept pasted text or uploaded JPG/PNG/PDF files
- **AI-Powered Analysis**: Uses OpenRouter API with Claude to analyze notices
- **Structured Output**: Returns explanations in four clear sections:
  - What happened (plain English summary)
  - What you need to do (actionable items)
  - Items for your attorney (legal strategy items)
  - Notice type classification
- **Responsive Design**: Clean, minimal interface optimized for anxious users
- **Example Notices**: Pre-loaded examples for testing (H-1B RFE, NOID, Interview Notice)

## Tech Stack

- **Backend**: FastAPI with Pydantic for type safety
- **Frontend**: Single HTML file with embedded CSS and vanilla JavaScript
- **AI**: OpenRouter API (Claude Haiku) for text and vision processing
- **PDF Processing**: PyMuPDF for text extraction
- **Image Processing**: Base64 encoding for vision API

## Quick Start

### Prerequisites

- Python 3.11+
- OpenRouter API key ([get one here](https://openrouter.ai/))

### Local Development

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd 01_glade_demo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variable**
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```

4. **Run the application**
   ```bash
   cd app
   python main.py
   ```

5. **Open browser**
   Navigate to `http://localhost:8000`

### Using Docker Compose (Recommended)

1. **Add your API key to .env file**
   ```bash
   echo "OPENROUTER_API_KEY=your-api-key-here" > .env
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Open browser**
   Navigate to `http://localhost:8000`

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Using Docker (Alternative)

1. **Build the image**
   ```bash
   docker build -t immigration-explainer .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env immigration-explainer
   ```

3. **Open browser**
   Navigate to `http://localhost:8000`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key for accessing Claude models |

## API Endpoints

### `POST /explain`

Analyzes an immigration notice and returns a structured explanation.

**Request Format:**
- **Form Data**: `multipart/form-data`
- **Fields**:
  - `notice_text` (optional): Plain text of the notice
  - `file` (optional): Uploaded file (JPG/PNG/PDF)

**Response Format:**
```json
{
  "what_happened": "Plain English explanation...",
  "what_they_need": ["Action item 1", "Action item 2"],
  "attorney_items": ["Legal item 1", "Legal item 2"],
  "notice_type": "RFE" // One of: RFE, NOID, interview_notice, approval, denial, I-94, unknown
}
```

**Supported File Types:**
- **Images**: JPG, PNG (processed via Claude's vision API)
- **PDFs**: Text extracted using PyMuPDF
- **Text**: Direct paste into textarea

**File Priority**: If both text and file are provided, the file takes precedence.

## Project Structure

```
01_glade_demo/
├── app/
│   └── main.py          # FastAPI backend with type-safe endpoints
├── static/
│   └── index.html       # Single-file frontend with embedded CSS/JS
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md           # This file
```

## Usage Examples

### Text Input
Paste any USCIS notice text into the textarea and click "Explain Notice".

### File Upload
1. Click "Choose File" and select a JPG, PNG, or PDF of your notice
2. Click "Explain Notice"
3. The system will extract text (PDF) or use vision AI (images)

### Pre-loaded Examples
Click any of the example buttons to test with realistic notices:
- **H-1B RFE**: Request for Evidence regarding specialty occupation
- **Intent to Deny**: Marriage fraud investigation notice
- **Interview Notice**: I-485 adjustment of status interview

## Security Considerations

- No data persistence - notices are processed in memory only
- HTTPS recommended for production deployments
- API key should be kept secure and not logged
- File uploads are validated for type and size

## Legal Disclaimer

This application provides informational explanations only and does not constitute legal advice. Users should consult with qualified immigration attorneys for specific legal guidance about their cases.

## Development Notes

### Adding New Notice Types

To add support for new notice classifications:

1. Update the `notice_type` options in the system prompt (app/main.py:107)
2. Add the new type to the frontend notice type display logic if special styling is needed

### Customizing the AI Prompt

The system prompt is designed to be anxiety-aware and non-technical. Key principles:
- Never say "I cannot help" - route complex items to attorney_items instead
- Use encouraging but honest language
- Separate actionable items from legal strategy items
- Always return valid JSON

### Error Handling

The application includes comprehensive error handling for:
- Invalid file types
- Empty/corrupted PDFs
- API failures
- JSON parsing errors
- Network connectivity issues

## Deployment

For production deployment:

1. Set up environment variables securely
2. Use a reverse proxy (nginx) for HTTPS
3. Configure proper logging and monitoring
4. Consider rate limiting on the API endpoints
5. Ensure OpenRouter API key has appropriate usage limits

## Contributing

1. Follow the existing code style and type hints
2. Test with various real immigration notices
3. Ensure mobile responsiveness for any UI changes
4. Update this README for any new features or configuration changes