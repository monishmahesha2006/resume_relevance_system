"""
System Startup Script
Provides easy commands to run different components of the system
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")
    
    required_packages = [
        'streamlit', 'fastapi', 'uvicorn', 'pandas', 'plotly',
        'sentence-transformers', 'spacy', 'nltk', 'fitz', 'pdfplumber'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install requirements: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def download_spacy_model():
    """Download spaCy model if not present"""
    print("🔍 Checking spaCy model...")
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy model is available")
        return True
    except OSError:
        print("📥 Downloading spaCy model...")
        return run_command("python -m spacy download en_core_web_sm", "Download spaCy model")

def setup_database():
    """Initialize database"""
    print("🗄️ Setting up database...")
    
    try:
        sys.path.append('backend')
        from utils.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        stats = db_manager.get_statistics()
        print(f"✅ Database initialized. Current stats: {stats}")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def run_pipeline():
    """Run the main processing pipeline"""
    print("🚀 Running main pipeline...")
    return run_command("python main.py", "Main pipeline processing")

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend API server...")
    
    # Change to backend directory
    os.chdir('backend')
    
    try:
        # Start the server in background
        process = subprocess.Popen([
            sys.executable, 'api.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Backend server started on http://localhost:8000")
        print("📚 API documentation available at http://localhost:8000/docs")
        
        # Wait a moment for server to start
        time.sleep(3)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print("🚀 Starting frontend dashboard...")
    
    # Change to frontend directory
    os.chdir('frontend')
    
    try:
        # Start Streamlit
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Frontend dashboard started on http://localhost:8501")
        
        # Wait a moment for server to start
        time.sleep(3)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("🎯 Resume Relevance System Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('data') or not os.path.exists('backend'):
        print("❌ Please run this script from the resume_relevance_system directory")
        return
    
    # Step 1: Check requirements
    if not check_requirements():
        return
    
    # Step 2: Download spaCy model
    if not download_spacy_model():
        return
    
    # Step 3: Setup database
    if not setup_database():
        return
    
    # Step 4: Run pipeline (optional)
    print("\n" + "="*50)
    print("PIPELINE OPTIONS")
    print("="*50)
    print("1. Run main pipeline (process existing data)")
    print("2. Skip pipeline and start servers only")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        if not run_pipeline():
            print("❌ Pipeline failed. You can still start the servers manually.")
    elif choice == "3":
        print("👋 Goodbye!")
        return
    
    # Step 5: Start servers
    print("\n" + "="*50)
    print("STARTING SERVERS")
    print("="*50)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Cannot start frontend without backend")
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Frontend failed to start")
        backend_process.terminate()
        return
    
    # Success message
    print("\n" + "="*50)
    print("🎉 SYSTEM STARTED SUCCESSFULLY!")
    print("="*50)
    print("📊 Dashboard: http://localhost:8501")
    print("🔧 API Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n💡 Tips:")
    print("- Use the dashboard to upload files and view results")
    print("- Use the API for programmatic access")
    print("- Press Ctrl+C to stop all servers")
    
    # Ask if user wants to open browser
    open_browser = input("\n🌐 Open dashboard in browser? (y/n): ").strip().lower()
    if open_browser in ['y', 'yes']:
        webbrowser.open('http://localhost:8501')
    
    try:
        # Keep the script running
        print("\n⏳ Servers are running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        
        if backend_process:
            backend_process.terminate()
            print("✅ Backend server stopped")
        
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend server stopped")
        
        print("👋 All servers stopped. Goodbye!")

if __name__ == "__main__":
    main()
