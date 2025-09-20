# Resume Relevance System

An automated end-to-end system for checking resume-JD relevance using advanced NLP, machine learning, and semantic analysis.

## 🚀 Features

- **PDF Text Extraction**: Robust extraction using PyMuPDF and pdfplumber
- **Intelligent Preprocessing**: Section parsing, skill extraction, and text normalization
- **Dual Matching System**: 
  - Hard Match: Keyword, skills, education, and experience matching
  - Soft Match: Semantic similarity using sentence transformers
- **Weighted Scoring**: 60% hard match + 40% soft match for final relevance score
- **Comprehensive Analysis**: Missing skills, education gaps, experience analysis
- **LLM Integration**: AI-powered feedback generation (optional)
- **Web Dashboard**: Interactive Streamlit interface for placement teams
- **REST API**: FastAPI backend for programmatic access
- **Database Storage**: SQLite database with comprehensive schema

## 📁 Project Structure

```
resume_relevance_system/
├── data/                          # Dataset folder (copied from your datasets)
│   ├── JD/                        # Job descriptions
│   └── Resumes/                   # Resumes
├── backend/
│   ├── api.py                     # FastAPI application
│   ├── models/
│   │   ├── feature_engineering.py # Hard/soft matching algorithms
│   │   └── relevance_scorer.py    # Scoring and feedback generation
│   └── utils/
│       ├── pdf_extractor.py       # PDF text extraction
│       ├── text_preprocessor.py   # Text cleaning and section parsing
│       ├── text_preprocessor_simple.py # Simplified preprocessor
│       └── database_manager.py    # Database operations
├── frontend/
│   └── app.py                     # Streamlit dashboard
├── database/
│   └── schema.sql                 # Database schema
├── main_simple.py                 # Simplified pipeline script
├── test_simple.py                 # Simple test script
├── start_system.py                # System startup script
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🛠️ Complete Setup Instructions

### Prerequisites

- **Python 3.8 or higher** (Python 3.9+ recommended)
- **pip package manager** (comes with Python)
- **Git** (optional, for version control)

### Step 1: Download and Extract the Project

1. **Download the project files** to your desired location
2. **Navigate to the project directory:**
   ```bash
   cd resume_relevance_system
   ```

### Step 2: Create Virtual Environment

**Why use a virtual environment?**
- Isolates project dependencies
- Prevents conflicts with other Python projects
- Makes the project portable and reproducible

#### For Windows:

1. **Open Command Prompt or PowerShell** in the project directory
2. **Create virtual environment:**
   ```cmd
   python -m venv venv
   ```
3. **Activate virtual environment:**
   ```cmd
   # For Command Prompt
   venv\Scripts\activate
   
   # For PowerShell (if execution policy allows)
   venv\Scripts\Activate.ps1
   
   # If PowerShell execution policy error, run this first:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

#### For macOS/Linux:

1. **Open Terminal** in the project directory
2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   ```
3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

**Verify activation:** You should see `(venv)` at the beginning of your command prompt.

### Step 3: Install Dependencies

1. **Upgrade pip (recommended):**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Install core dependencies:**
   ```bash
   pip install pdfplumber python-docx docx2txt requests pandas
   ```

3. **Install NLP and ML dependencies:**
   ```bash
   pip install nltk scikit-learn fuzzywuzzy
   ```

4. **Install web framework dependencies:**
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

5. **Install frontend dependencies:**
   ```bash
   pip install streamlit plotly
   ```

6. **Install optional dependencies (for advanced features):**
   ```bash
   # For sentence transformers (semantic matching)
   pip install sentence-transformers
   
   # For vector database
   pip install faiss-cpu
   
   # For OpenAI integration (optional)
   pip install openai
   ```

### Step 4: Download NLTK Data

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

### Step 5: Download spaCy Model (Optional)

```bash
python -m spacy download en_core_web_sm
```

**Note:** If this fails, the system will work with the simplified text preprocessor.

### Step 6: Verify Installation

Run the test script to verify everything is working:

```bash
python test_simple.py
```

You should see all tests passing.

## 🚀 Running the System

### Method 1: Quick Start (Recommended)

1. **Run the simplified pipeline:**
   ```bash
   python main_simple.py
   ```
   This will process all your existing PDFs and create matching results.

2. **Start the backend API server:**
   ```bash
   cd backend
   python api.py
   ```
   Keep this terminal open. The API will be available at `http://localhost:8000`

3. **In a new terminal, start the frontend:**
   ```bash
   cd frontend
   streamlit run app.py
   ```
   The dashboard will be available at `http://localhost:8501`

### Method 2: Using the Startup Script

```bash
python start_system.py
```

This script will guide you through the entire process.

### Method 3: Manual Step-by-Step

#### Step 1: Process Your Data

```bash
python main_simple.py
```

This will:
- Extract text from all PDFs in `data/JD/` and `data/Resumes/`
- Process and clean the text
- Store everything in the database
- Run matching algorithms
- Generate a detailed report

#### Step 2: Start Backend API

```bash
cd backend
python api.py
```

**Expected output:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### Step 3: Start Frontend Dashboard

**Open a new terminal/command prompt** and run:

```bash
cd frontend
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local:        http://localhost:8501
Network:      http://192.168.x.x:8501
```

## 🌐 Accessing the System

### Web Dashboard
- **URL:** `http://localhost:8501`
- **Features:** Upload files, view results, analytics, search

### API Documentation
- **URL:** `http://localhost:8000/docs`
- **Features:** Interactive API documentation, test endpoints

### API Endpoints
- **Base URL:** `http://localhost:8000`
- **Health Check:** `http://localhost:8000/health`
- **Statistics:** `http://localhost:8000/statistics`

## 📊 Usage Guide

### Using the Web Dashboard

1. **Upload Files**: Go to "Upload Files" page
   - Upload job descriptions (PDF/DOCX)
   - Upload resumes (PDF/DOCX)
   - Run bulk matching

2. **View Results**: Go to "Matching Results" page
   - Filter by verdict (High/Medium/Low)
   - View detailed scores and feedback
   - Download results as CSV

3. **Analytics**: Go to "Statistics" page
   - View overall statistics
   - Analyze score distributions
   - Identify top performers

4. **Search**: Go to "Search" page
   - Search by resume or JD name
   - Apply advanced filters

### Using the API

#### Upload a Job Description
```bash
curl -X POST "http://localhost:8000/upload/job-description" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_jd.pdf"
```

#### Upload a Resume
```bash
curl -X POST "http://localhost:8000/upload/resume" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@resume.pdf"
```

#### Run Matching
```bash
curl -X POST "http://localhost:8000/match/all"
```

#### Get Results
```bash
curl -X GET "http://localhost:8000/matching-results"
```

## 🔧 Configuration

### Scoring Weights

The system uses weighted scoring:
- **Hard Match (60%)**: Skills, education, experience, keywords
- **Soft Match (40%)**: Semantic similarity using embeddings

### Thresholds

- **High Match**: ≥ 75%
- **Medium Match**: 50-74%
- **Low Match**: < 50%

### Supported File Formats

- **PDF**: .pdf
- **Word Documents**: .docx, .doc

## 📈 Algorithm Details

### Hard Matching Components

1. **Skills Matching**: Fuzzy string matching with 80% similarity threshold
2. **Education Matching**: Degree and institution matching
3. **Experience Matching**: Years of experience comparison
4. **Keyword Matching**: TF-IDF cosine similarity

### Soft Matching Components

1. **Semantic Similarity**: Sentence transformer embeddings (all-MiniLM-L6-v2)
2. **Section-wise Matching**: Individual section similarity scores
3. **Overall Text Similarity**: Full document embedding comparison

### Feature Engineering

- **Text Preprocessing**: Cleaning, normalization, section extraction
- **Entity Recognition**: Skills, education, experience extraction
- **Embedding Generation**: Cached for performance
- **Fuzzy Matching**: Handles variations in skill names

## 🗄️ Database Schema

The system uses SQLite with the following main tables:

- **job_descriptions**: Store JD files and processed data
- **resumes**: Store resume files and processed data
- **matching_results**: Store all matching results and analysis
- **Views**: Pre-computed views for common queries

## 🔍 API Endpoints

### File Management
- `POST /upload/job-description` - Upload job description
- `POST /upload/resume` - Upload resume
- `GET /job-descriptions` - List all job descriptions
- `GET /resumes` - List all resumes

### Matching
- `POST /match/{resume_id}/{jd_id}` - Match specific resume with JD
- `POST /match/all` - Match all resumes with all JDs
- `GET /matching-results` - Get matching results
- `GET /matching-summary` - Get summary view
- `GET /top-matches` - Get top matches

### Analytics
- `GET /statistics` - Get database statistics
- `GET /search` - Search matches
- `DELETE /job-description/{id}` - Delete job description
- `DELETE /resume/{id}` - Delete resume

## 🧪 Testing

### Test with Sample Data

The system comes with sample data in the `data/` folder:
- `data/JD/` - Sample job descriptions
- `data/Resumes/` - Sample resumes

### Run Individual Components

```bash
# Test PDF extraction
python backend/utils/pdf_extractor.py

# Test text preprocessing
python backend/utils/text_preprocessor_simple.py

# Test feature engineering
python backend/models/feature_engineering.py

# Test relevance scoring
python backend/models/relevance_scorer.py

# Test database operations
python backend/utils/database_manager.py
```

## 🚨 Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **PDF extraction fails**:
   - Ensure PDFs are not password-protected
   - Check if PDFs contain text (not just images)

3. **API connection fails**:
   - Ensure backend server is running on port 8000
   - Check firewall settings

4. **Memory issues with large files**:
   - Process files in smaller batches
   - Increase system memory

5. **Streamlit not starting**:
   - Make sure you're in the virtual environment
   - Check if port 8501 is available
   - Try: `streamlit run app.py --server.port 8502`

6. **Module not found errors**:
   - Ensure virtual environment is activated
   - Reinstall missing packages: `pip install package_name`

### Performance Optimization

- **Embedding Cache**: Embeddings are cached for faster processing
- **Database Indexing**: Proper indexes for fast queries
- **Batch Processing**: Bulk operations for efficiency

## 📋 Quick Reference Commands

### Setup Commands
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install pdfplumber python-docx docx2txt requests pandas nltk scikit-learn fuzzywuzzy fastapi uvicorn python-multipart streamlit plotly

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

### Running Commands
```bash
# Process data
python main_simple.py

# Start backend
cd backend && python api.py

# Start frontend
cd frontend && streamlit run app.py

# Test system
python test_simple.py
```

### URLs
- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔮 Future Enhancements

- [ ] Support for more file formats (RTF, TXT)
- [ ] Advanced NLP models (BERT, GPT-based)
- [ ] Real-time matching updates
- [ ] Integration with ATS systems
- [ ] Multi-language support
- [ ] Advanced analytics and reporting
- [ ] Machine learning model training on historical data

## 📝 License

This project is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📞 Support

For support and questions, please create an issue in the project repository.

---

**Note**: This system is designed to work with the existing dataset structure. The `data/` folder contains your original datasets (JD/ and Resumes/ folders) and will be used for processing.