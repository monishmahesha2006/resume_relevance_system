"""
Streamlit Frontend Dashboard for Resume Relevance System
Interactive dashboard for placement team
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Resume Relevance System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: dict = None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Please ensure the backend server is running.")
        return None
    except Exception as e:
        st.error(f"Error making API request: {e}")
        return None

def upload_file(file, file_type: str):
    """Upload file to API"""
    if file is not None:
        files = {"file": (file.name, file.getvalue(), file.type)}
        endpoint = f"/upload/{file_type}"
        
        try:
            response = requests.post(f"{API_BASE_URL}{endpoint}", files=files)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Upload failed: {response.text}")
                return None
        except Exception as e:
            st.error(f"Upload error: {e}")
            return None
    return None

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Resume Relevance System</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Upload Files", "Matching Results", "Statistics", "Search"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Upload Files":
        show_upload_page()
    elif page == "Matching Results":
        show_matching_results()
    elif page == "Statistics":
        show_statistics()
    elif page == "Search":
        show_search_page()

def show_dashboard():
    """Show main dashboard"""
    st.header("📈 Dashboard Overview")
    
    # Get statistics
    stats_data = make_api_request("/statistics")
    if not stats_data:
        st.warning("Unable to load statistics. Please check API connection.")
        return
    
    stats = stats_data.get("statistics", {})
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Job Descriptions", stats.get("job_descriptions", 0))
    
    with col2:
        st.metric("Resumes", stats.get("resumes", 0))
    
    with col3:
        st.metric("Total Matches", stats.get("matching_results", 0))
    
    with col4:
        st.metric("Avg Score", f"{stats.get('average_score', 0):.1f}%")
    
    # Verdict distribution
    st.subheader("Match Quality Distribution")
    verdict_dist = stats.get("verdict_distribution", {})
    
    if verdict_dist:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=list(verdict_dist.values()),
                names=list(verdict_dist.keys()),
                title="Match Quality Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=list(verdict_dist.keys()),
                y=list(verdict_dist.values()),
                title="Match Quality Count",
                labels={"x": "Verdict", "y": "Count"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Recent top matches
    st.subheader("🏆 Recent Top Matches")
    top_matches_data = make_api_request("/top-matches?limit=5")
    
    if top_matches_data:
        top_matches = top_matches_data.get("top_matches", [])
        if top_matches:
            df = pd.DataFrame(top_matches)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No matches found. Upload files and run matching to see results.")
    else:
        st.warning("Unable to load top matches.")

def show_upload_page():
    """Show file upload page"""
    st.header("📁 Upload Files")
    
    # File upload tabs
    tab1, tab2 = st.tabs(["Upload Job Description", "Upload Resume"])
    
    with tab1:
        st.subheader("Upload Job Description")
        jd_file = st.file_uploader(
            "Choose a job description file",
            type=['pdf', 'docx', 'doc'],
            key="jd_upload"
        )
        
        if st.button("Upload Job Description", key="upload_jd"):
            if jd_file:
                with st.spinner("Uploading and processing job description..."):
                    result = upload_file(jd_file, "job-description")
                    if result:
                        st.success(f"✅ Job description uploaded successfully!")
                        st.json(result)
            else:
                st.warning("Please select a file to upload.")
    
    with tab2:
        st.subheader("Upload Resume")
        resume_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx', 'doc'],
            key="resume_upload"
        )
        
        if st.button("Upload Resume", key="upload_resume"):
            if resume_file:
                with st.spinner("Uploading and processing resume..."):
                    result = upload_file(resume_file, "resume")
                    if result:
                        st.success(f"✅ Resume uploaded successfully!")
                        st.json(result)
            else:
                st.warning("Please select a file to upload.")
    
    # Bulk matching section
    st.subheader("🔄 Run Matching")
    st.write("Match all uploaded resumes with all job descriptions")
    
    if st.button("Run Bulk Matching", type="primary"):
        with st.spinner("Running bulk matching..."):
            result = make_api_request("/match/all", method="POST")
            if result:
                st.success("✅ Bulk matching completed!")
                st.json(result)
            else:
                st.error("❌ Bulk matching failed.")

def show_matching_results():
    """Show matching results page"""
    st.header("📋 Matching Results")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        verdict_filter = st.selectbox(
            "Filter by Verdict",
            ["All", "High", "Medium", "Low"],
            key="verdict_filter"
        )
    
    with col2:
        limit = st.number_input("Limit Results", min_value=10, max_value=1000, value=50)
    
    # Get results
    if verdict_filter == "All":
        results_data = make_api_request(f"/matching-results?limit={limit}")
    else:
        results_data = make_api_request(f"/matching-results?verdict={verdict_filter}&limit={limit}")
    
    if results_data:
        results = results_data.get("matching_results", [])
        
        if results:
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Display results
            st.subheader(f"📊 Results ({len(results)} matches)")
            
            # Score distribution
            if 'relevance_score' in df.columns:
                fig = px.histogram(
                    df, 
                    x='relevance_score',
                    title="Score Distribution",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Results table
            st.dataframe(df, use_container_width=True)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"matching_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No matching results found.")
    else:
        st.warning("Unable to load matching results.")

def show_statistics():
    """Show statistics page"""
    st.header("📊 Statistics & Analytics")
    
    # Get statistics
    stats_data = make_api_request("/statistics")
    if not stats_data:
        st.warning("Unable to load statistics.")
        return
    
    stats = stats_data.get("statistics", {})
    
    # Overall statistics
    st.subheader("📈 Overall Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Job Descriptions", stats.get("job_descriptions", 0))
        st.metric("Total Resumes", stats.get("resumes", 0))
    
    with col2:
        st.metric("Total Matches", stats.get("matching_results", 0))
        st.metric("Average Score", f"{stats.get('average_score', 0):.1f}%")
    
    with col3:
        verdict_dist = stats.get("verdict_distribution", {})
        for verdict, count in verdict_dist.items():
            st.metric(f"{verdict} Matches", count)
    
    # Detailed analytics
    st.subheader("📊 Detailed Analytics")
    
    # Get matching summary for detailed analysis
    summary_data = make_api_request("/matching-summary")
    if summary_data:
        summary = summary_data.get("matching_summary", [])
        
        if summary:
            df = pd.DataFrame(summary)
            
            # Score trends
            if 'relevance_score' in df.columns:
                fig = px.box(
                    df,
                    y='relevance_score',
                    title="Score Distribution by Verdict",
                    color='verdict'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top performers
            st.subheader("🏆 Top Performers")
            top_performers = df.nlargest(10, 'relevance_score')
            st.dataframe(top_performers, use_container_width=True)

def show_search_page():
    """Show search page"""
    st.header("🔍 Search Matches")
    
    # Search input
    search_query = st.text_input("Search by resume or job description name")
    
    if search_query:
        with st.spinner("Searching..."):
            results = make_api_request(f"/search?query={search_query}")
            
            if results:
                search_results = results.get("search_results", [])
                
                if search_results:
                    st.subheader(f"🔍 Search Results for '{search_query}'")
                    df = pd.DataFrame(search_results)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(f"No results found for '{search_query}'")
            else:
                st.warning("Search failed.")
    
    # Advanced search options
    st.subheader("🔧 Advanced Search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_score = st.slider("Minimum Score", 0, 100, 0)
    
    with col2:
        verdict_filter = st.selectbox("Verdict Filter", ["All", "High", "Medium", "Low"])
    
    if st.button("Apply Filters"):
        # This would require additional API endpoints for advanced filtering
        st.info("Advanced filtering feature coming soon!")

if __name__ == "__main__":
    main()
