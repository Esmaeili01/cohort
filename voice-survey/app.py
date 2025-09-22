import os
import json
import base64
from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
from werkzeug.utils import secure_filename
import tempfile
import mimetypes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure Gemini API
# GEMINI_API_KEY = "AIzaSyBjDlIqfwbwidmutAm-o0vBsxxpx10Qyqc"
GEMINI_API_KEY = "AIzaSyC7Yx8Nn1KPHU_BEi3Iua8jULtPqmhJQbI"
# GEMINI_API_KEY = "AIzaSyBjDlIqfwbwidmutAm-o0vBsxxpx10Qyqc"
# GEMINI_API_KEY = "AIzaSyBjDlIqfwbwidmutAm-o0vBsxxpx10Qyqc"

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Survey questions in Persian
QUESTIONS = [
    "آیا شاغل هستید؟",
    "شغل شما چیست؟", 
    "از چه سنی و تا چه سنی مشغول به این کار هستید؟"
]

def allowed_file(filename):
    """Check if the uploaded file is an allowed audio format"""
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a', 'aac'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def transcribe_audio_with_gemini(audio_path):
    """Use Gemini API to transcribe audio to text"""
    try:
        # Read the audio file
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(audio_path)
        if not mime_type or not mime_type.startswith('audio/'):
            mime_type = 'audio/wav'  # default fallback
        
        # Create the audio part for Gemini
        audio_part = {
            "mime_type": mime_type,
            "data": audio_data
        }
        
        # Create prompt for transcription
        prompt = """
        لطفاً این فایل صوتی را به متن فارسی تبدیل کنید. فقط متن صحبت‌های گفته شده را بنویسید، بدون توضیحات اضافی.
        """
        
        # Generate content with audio
        response = model.generate_content([prompt, audio_part])
        
        return response.text.strip()
        
    except Exception as e:
        app.logger.error(f"Error transcribing audio: {str(e)}")
        return f"خطا در تبدیل صوت به متن: {str(e)}"

def extract_structured_data_with_gemini(question, answer_text):
    """Use Gemini to extract structured data from answers"""
    try:
        if "شاغل هستید" in question:
            prompt = f"""
            سوال: {question}
            پاسخ: {answer_text}
            
            لطفاً از پاسخ مشخص کنید که آیا این شخص شاغل است یا نه.
            
            مثال‌های پاسخ مثبت:
            - "بله من شاغلم" -> true
            - "آره، کار دارم" -> true
            - "بلی هستم" -> true
            
            مثال‌های پاسخ منفی:
            - "نه، شاغل نیستم" -> false
            - "خیر، بیکارم" -> false
            
            فقط یکی از کلمات true یا false را برگردانید.
            """
            
        elif "شغل شما چیست" in question:
            prompt = f"""
            سوال: {question}
            پاسخ: {answer_text}
            
            لطفاً نام شغل را از پاسخ استخراج کنید و به صورت مختصر و واضح بنویسید.
            مثال: مهندس، معلم، پزشک، فروشنده، و غیره
            فقط نام شغل را بنویسید.
            """
            
        elif "چه سنی" in question:
            prompt = f"""
            سوال: {question}
            پاسخ: {answer_text}
            
            لطفاً از پاسخ، سن شروع کار و سن فعلی یا سن پایان کار را استخراج کنید.
            پاسخ را به این فرمت بدهید:
            سن شروع: [عدد]
            سن پایان: [عدد یا فعلی]
            
            اگر سن پایان مشخص نیست، "فعلی" بنویسید.
            """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        app.logger.error(f"Error extracting structured data: {str(e)}")
        return answer_text

@app.route('/')
def index():
    """Main survey page"""
    return render_template('survey.html', questions=QUESTIONS)

def parse_structured_response(question, structured_answer):
    """Parse structured response into database format"""
    if "شاغل هستید" in question:
        # Parse employment status
        has_job = "true" in structured_answer.lower()
        return {"has_job": has_job}
        
    elif "شغل شما چیست" in question:
        # Parse job title
        return {"job_title": structured_answer.strip()}
        
    elif "چه سنی" in question:
        # Parse age range
        result = {"from_age": None, "to_age": None}
        
        lines = structured_answer.split('\n')
        for line in lines:
            if "سن شروع" in line:
                try:
                    age = int(''.join(filter(str.isdigit, line)))
                    result["from_age"] = age
                except:
                    pass
            elif "سن پایان" in line:
                if "فعلی" in line:
                    result["to_age"] = "current"
                else:
                    try:
                        age = int(''.join(filter(str.isdigit, line)))
                        result["to_age"] = age
                    except:
                        result["to_age"] = "current"
        
        return result
    
    return {}

@app.route('/process_question', methods=['POST'])
def process_question():
    """Process individual question with Gemini API"""
    try:
        question_num = request.form.get('question_num')
        question_text = request.form.get('question_text')
        text_answer = request.form.get('text_answer')
        audio_file = request.files.get('audio_file')
        
        final_answer = None
        transcription = None
        
        if text_answer and text_answer.strip():
            final_answer = text_answer.strip()
        elif audio_file and audio_file.filename:
            # Process audio file
            filename = secure_filename(audio_file.filename)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            audio_file.save(temp_path)
            
            try:
                # Transcribe audio
                transcription = transcribe_audio_with_gemini(temp_path)
                final_answer = transcription
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        if not final_answer:
            return jsonify({'success': False, 'error': 'No answer provided'})
        
        # Extract structured data using Gemini
        structured_answer = extract_structured_data_with_gemini(question_text, final_answer)
        
        # Parse structured data
        parsed_data = parse_structured_response(question_text, structured_answer)
        
        response_data = {
            'success': True,
            'original_answer': final_answer,
            'processed_answer': structured_answer,
            'structured_data': parsed_data,
            'transcription': transcription
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error processing question: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/submit', methods=['POST'])
def submit_survey():
    """Handle survey submission with pre-processed data"""
    try:
        # Get pre-processed data from frontend
        processed_data_str = request.form.get('processed_data')
        
        if processed_data_str:
            # Use pre-processed data from immediate processing
            try:
                processed_data = json.loads(processed_data_str)
                
                # Initialize result structure with your specified format
                survey_results = {
                    'answers': {},
                    'transcriptions': {},
                    'processed_data': {}
                }
                
                # Process question 1 (employment status)
                if processed_data.get('question1'):
                    q1_data = processed_data['question1']
                    survey_results['answers']['has_job'] = q1_data.get('original_answer', '')
                    if q1_data.get('transcription'):
                        survey_results['transcriptions']['has_job'] = q1_data.get('transcription', '')
                    if q1_data.get('structured_data', {}).get('has_job') is not None:
                        survey_results['processed_data']['has_job'] = q1_data['structured_data']['has_job']
                
                # Process question 2 (job title)
                if processed_data.get('question2'):
                    q2_data = processed_data['question2']
                    survey_results['answers']['job_title'] = q2_data.get('original_answer', '')
                    if q2_data.get('transcription'):
                        survey_results['transcriptions']['job_title'] = q2_data.get('transcription', '')
                    if q2_data.get('structured_data', {}).get('job_title'):
                        survey_results['processed_data']['job_title'] = q2_data['structured_data']['job_title']
                
                # Process question 3 (work duration)
                if processed_data.get('question3'):
                    q3_data = processed_data['question3']
                    survey_results['answers']['from_to_age'] = q3_data.get('original_answer', '')
                    if q3_data.get('transcription'):
                        survey_results['transcriptions']['from_to_age'] = q3_data.get('transcription', '')
                    if q3_data.get('structured_data'):
                        sd = q3_data['structured_data']
                        if sd.get('from_age'):
                            survey_results['processed_data']['from_age'] = str(sd['from_age'])
                        if sd.get('to_age'):
                            survey_results['processed_data']['to_age'] = str(sd['to_age'])
                
            except json.JSONDecodeError:
                # Fallback to old processing method
                return process_survey_fallback()
                
        else:
            # Fallback to old processing method if no pre-processed data
            return process_survey_fallback()
        
        # Save results to file (in a real app, you'd save to database)
        results_file = os.path.join(app.config['UPLOAD_FOLDER'], 'survey_results.json')
        
        # Load existing results if file exists
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
        else:
            all_results = []
        
        # Add new result
        all_results.append(survey_results)
        
        # Save updated results
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        return render_template('success.html', results=survey_results)
        
    except Exception as e:
        app.logger.error(f"Error processing survey: {str(e)}")
        return render_template('error.html', error=str(e)), 500

def process_survey_fallback():
    """Fallback method for processing survey without pre-processed data"""
    survey_results = {
        'answers': {},
        'transcriptions': {},
        'processed_data': {}
    }
    
    # Map question numbers to keys
    question_keys = ['has_job', 'job_title', 'from_to_age']
    
    # Process each question's answer the old way
    for i in range(1, len(QUESTIONS) + 1):
        question = QUESTIONS[i-1]
        question_key = question_keys[i-1]
        text_answer = request.form.get(f'answer_{i}')
        audio_file = request.files.get(f'audio_{i}')
        
        final_answer = None
        transcription = None
        
        if text_answer and text_answer.strip():
            final_answer = text_answer.strip()
            survey_results['answers'][question_key] = final_answer
            
        elif audio_file and audio_file.filename and allowed_file(audio_file.filename):
            filename = secure_filename(audio_file.filename)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            audio_file.save(temp_path)
            
            try:
                transcription = transcribe_audio_with_gemini(temp_path)
                survey_results['transcriptions'][question_key] = transcription
                final_answer = transcription
                survey_results['answers'][question_key] = transcription
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        if final_answer:
            structured_answer = extract_structured_data_with_gemini(question, final_answer)
            
            parsed_data = parse_structured_response(question, structured_answer)
            
            # Map parsed data to the correct format
            if question_key == 'has_job' and 'has_job' in parsed_data:
                survey_results['processed_data']['has_job'] = parsed_data['has_job']
            elif question_key == 'job_title' and 'job_title' in parsed_data:
                survey_results['processed_data']['job_title'] = parsed_data['job_title']
            elif question_key == 'from_to_age':
                if 'from_age' in parsed_data:
                    survey_results['processed_data']['from_age'] = str(parsed_data['from_age'])
                if 'to_age' in parsed_data:
                    survey_results['processed_data']['to_age'] = str(parsed_data['to_age'])
    
    return survey_results

@app.route('/results')
def view_results():
    """View all survey results (admin function)"""
    try:
        results_file = os.path.join(app.config['UPLOAD_FOLDER'], 'survey_results.json')
        
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
        else:
            all_results = []
        
        return render_template('results.html', results=all_results, questions=QUESTIONS)
        
    except Exception as e:
        app.logger.error(f"Error loading results: {str(e)}")
        return render_template('error.html', error=str(e)), 500

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)