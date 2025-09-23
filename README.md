# Persian Voice Survey Application

A modern Persian voice survey application that allows users to answer employment-related questions using either text input or voice recording. The application uses AI-powered processing to extract structured data from responses and includes comprehensive validation.

## Features

- **Bilingual Interface**: Persian (Farsi) RTL support with Bootstrap 5
- **Voice & Text Input**: Users can respond via text typing or audio recording
- **AI Processing**: Google Gemini API integration for speech-to-text and data extraction
- **Real-time Validation**: Smart validation for job titles and age ranges
- **Edit Functionality**: Users can edit their answers after confirmation
- **Structured Data Output**: Clean JSON format with processed survey results

## Prerequisites

- Python 3.7 or higher
- Google Gemini API key
- Modern web browser with microphone support

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voice-survey
   ```

2. **Install required packages**
   ```bash
   pip install flask google-generativeai werkzeug
   ```

3. **Configure API Key**
   - Open `app.py`
   - Replace the `GEMINI_API_KEY` with your Google Gemini API key:
     ```python
     GEMINI_API_KEY = "your-api-key-here"
     ```

4. **Create uploads directory**
   ```bash
   mkdir uploads
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Access the application**
   - Open your web browser
   - Navigate to: `http://127.0.0.1:5000` or `http://localhost:5000`

3. **Stop the server**
   - Press `Ctrl+C` in the terminal

## Usage

1. **Answer Questions**: The survey asks three questions about employment:
   - Employment status (Yes/No)
   - Job title (if employed)
   - Work age range (if employed)

2. **Input Methods**: For each question, choose:
   - **Text Tab**: Type your answer in Persian
   - **Voice Tab**: Record your answer using the microphone

3. **Validation**: The system validates responses and asks for corrections if needed

4. **Edit Answers**: Click "ویرایش پاسخ" (Edit Answer) to modify any response

5. **Results**: View processed data in the final success page

## File Structure

```
voice-survey/
├── app.py                      # Main Flask application
├── templates/
│   ├── survey.html            # Main survey page
│   ├── success.html           # Success page showing results
│   └── error.html             # Error page
├── uploads/
│   └── survey_results.json    # Stored survey results
├── tests/
│   ├── test_validation.py     # Age validation tests
│   └── test_job_validation.py # Job title validation tests
└── documentation/
    ├── EDIT_FUNCTIONALITY.md
    ├── AGE_VALIDATION_GUIDE.md
    └── JOB_TITLE_VALIDATION.md
```

## Output Format

Survey results are saved in JSON format:

```json
{
  "answers": {
    "has_job": "user text or audio_filename.webm",
    "job_title": "user text or audio_filename.webm",
    "from_to_age": "user text or audio_filename.webm"
  },
  "transcriptions": {
    "has_job": "transcribed text from audio",
    "job_title": "transcribed text from audio",
    "from_to_age": "transcribed text from audio"
  },
  "processed_data": {
    "has_job": true,
    "job_title": "مهندس",
    "from_age": "25",
    "to_age": "35"
  }
}
```

## Testing

Run the validation tests:

```bash
# Test age validation
python test_validation.py

# Test job title validation
python test_job_validation.py
```

## Configuration

### Environment Variables (Optional)
You can set the API key as an environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Flask Configuration
- **Debug Mode**: Enabled by default for development
- **Upload Folder**: `uploads/` directory
- **Max File Size**: 16MB for audio uploads

## Browser Requirements

- **Microphone Access**: Required for voice recording
- **Modern Browser**: Chrome, Firefox, Safari, Edge (latest versions)
- **JavaScript**: Must be enabled
- **WebRTC Support**: For audio recording functionality

## Troubleshooting

### Common Issues:

1. **Microphone Not Working**
   - Check browser permissions
   - Ensure microphone is connected and working
   - Try refreshing the page

2. **API Errors**
   - Verify your Gemini API key is correct
   - Check internet connection
   - Ensure API quota is not exceeded

3. **File Upload Errors**
   - Check `uploads/` directory exists and is writable
   - Verify disk space availability

4. **Port Already in Use**
   - Change the port in `app.py`:
     ```python
     app.run(debug=True, host='0.0.0.0', port=5001)
     ```

## Development

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development
python app.py
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please open an issue in the GitHub repository.