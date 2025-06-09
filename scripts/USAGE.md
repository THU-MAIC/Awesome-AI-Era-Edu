 # AI-Era Education Scripts Usage Guide

This directory contains automated scripts for managing and classifying AI education-related papers. This guide provides comprehensive documentation for all available scripts.

## Table of Contents

- [Quick Start](#quick-start)
- [Setup and Configuration](#setup-and-configuration)
- [Core Scripts](#core-scripts)
- [Workflow Examples](#workflow-examples)
- [Configuration Files](#configuration-files)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Quick Start

### 1. Initial Setup
```bash
# Initialize the project environment
python scripts/setup.py

# Activate virtual environment (if created)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 2. One-Command Sync (Recommended)
```bash
# Sync papers from CSV to README (with caching and resume support)
python scripts/sync_readme.py --csv data/papers.csv
```

### 3. Process ArXiv URLs
```bash
# Process single ArXiv URL and update README
python scripts/arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345" --update-readme
```

## Setup and Configuration

### Environment Setup Script

**File**: `setup.py`

**Purpose**: Initialize the project environment with all dependencies and configurations.

**Usage**:
```bash
python scripts/setup.py
```

**Features**:
- ✅ Python version validation (3.9+ required)
- ✅ UV package manager installation and configuration
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ API key configuration
- ✅ Directory structure creation
- ✅ Git hooks setup

**What it creates**:
- `.venv/` - Virtual environment
- `data/` - Data storage directory
- `.env` - Environment variables file
- `.python-version` - Python version specification
- Git hooks for automatic README updates

## Core Scripts

### 1. Paper Classification Engine

**File**: `classify_papers.py`

**Purpose**: Core AI-powered paper classification system using Gemini API.

**Usage**:
```bash
# Basic classification
python scripts/classify_papers.py --csv data/papers.csv

# Resume from interrupted classification
python scripts/classify_papers.py --csv data/papers.csv --resume

# Custom output file
python scripts/classify_papers.py --csv data/papers.csv --output data/my_results.json
```

**Parameters**:
- `--csv`: Input CSV file path (default: from CSV_FILE env var)
- `--output`: Output JSON file path (default: `data/classified_papers.json`)
- `--resume`: Resume from previous progress

**Classification Categories**:

| Main Category | Subcategories |
|---------------|---------------|
| **AI-Focused** | `ai_models` (Model Architecture & Training)<br/>`ai_evaluation` (Evaluation & Benchmarks) |
| **AI+Education Intersection** | `intersection_systems` (Intelligent Tutoring Systems)<br/>`intersection_analytics` (Learning Analytics & Student Modeling)<br/>`intersection_content` (Content Generation & Assessment) |
| **Education-Focused** | `education_theory` (Learning Theory & Research)<br/>`education_practice` (Teaching Methods & Practice) |

**Output Format**:
```json
[
  {
    "title": "Paper Title",
    "is_education_related": true,
    "main_category": "intersection",
    "sub_category": "intersection_systems",
    "category_explanation": "This paper presents an intelligent tutoring system...",
    "sharer": "Contributor Name",
    "link": "https://arxiv.org/abs/2401.12345"
  }
]
```

### 2. ArXiv Paper Extraction Client

**File**: `arxiv_mcp_client.py`

**Purpose**: Extract and classify papers from ArXiv URLs with intelligent caching.

**Usage**:
```bash
# Process single ArXiv URL
python scripts/arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345"

# Process multiple URLs from file
python scripts/arxiv_mcp_client.py --urls-file urls.txt

# Process and automatically update README
python scripts/arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345" --update-readme

# Custom cache file
python scripts/arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345" --cache-file my_cache.json
```

**Parameters**:
- `--url`: Single ArXiv URL to process
- `--urls-file`: File containing ArXiv URLs (one per line)
- `--cache-file`: Cache file for ArXiv data (default: `data/arxiv_cache.json`)
- `--output`: Output file for results (default: `data/arxiv_mcp_results.json`)
- `--update-readme`: Automatically update README with results
- `--existing-papers`: Existing papers file for duplicate detection

**Supported URL Formats**:
- `https://arxiv.org/abs/2401.12345`
- `https://arxiv.org/pdf/2401.12345.pdf`
- `https://arxiv.org/html/2401.12345`
- Direct ID: `2401.12345`

**Features**:
- 🔄 **Smart Caching**: Avoids re-fetching already processed papers
- 🚫 **Duplicate Detection**: Automatically skips duplicate papers
- 📊 **Automatic Classification**: Integrates with classification engine
- 🔗 **Batch Processing**: Handle multiple URLs efficiently

### 3. One-Stop README Synchronization

**File**: `sync_readme.py` ⭐ **Most Important Script**

**Purpose**: Complete workflow from CSV papers to updated README with intelligent caching.

**Usage**:
```bash
# Basic sync (uses default CSV file, resumes from cache)
python scripts/sync_readme.py

# Custom CSV file
python scripts/sync_readme.py --csv my_papers.csv

# Force re-classification of all papers
python scripts/sync_readme.py --force

# Clear progress cache and start fresh
python scripts/sync_readme.py --clear-cache
```

**Parameters**:
- `--csv`: CSV file path (default: from CSV_FILE env var)
- `--force`: Force re-classification of all papers
- `--clear-cache`: Clear progress cache and start fresh

**Features**:
- 💾 **Automatic Progress Caching**: Resumes from interruptions
- 🔄 **Intelligent Duplicate Detection**: Only processes new papers
- 📈 **Progress Tracking**: Saves progress every 5 papers
- 🎯 **Content Quality Filtering**: Skips papers with insufficient context
- 📊 **Comprehensive Reporting**: Detailed classification summary

**Workflow**:
1. Load existing classified papers from cache
2. Identify new papers from CSV (not in cache)
3. Filter papers with insufficient content
4. Classify new papers using AI
5. Save progress incrementally
6. Update README with all papers
7. Generate comprehensive summary report

### 4. README Document Updater

**File**: `update_readme.py`

**Purpose**: Update README.md with classified papers and statistics.

**Usage**:
```bash
# Update README with classified papers
python scripts/update_readme.py update --papers data/classified_papers.json

# Add new papers to existing collection
python scripts/update_readme.py add --new-papers data/new_papers.json

# Generate category summary report
python scripts/update_readme.py summary --papers data/classified_papers.json
```

**Parameters**:
- `command`: Action to perform (`update`, `add`, `summary`)
- `--papers`: Papers JSON file path (default: `data/classified_papers.json`)
- `--readme`: README file path (default: `README.md`)
- `--new-papers`: New papers file for add command

**Features**:
- 📊 **Automatic Statistics**: Updates paper counts and percentages
- 📅 **Date Tracking**: Updates last modified date
- 🏷️ **Category Organization**: Groups papers by classification
- 🔗 **Clean Formatting**: Maintains consistent markdown format

### 5. Incremental Update System

**File**: `incremental_update.py`

**Purpose**: Handle incremental updates with state management and batch processing.

**Usage**:
```bash
# Quick incremental update
python scripts/incremental_update.py quick --csv data/papers.csv

# Check processing status
python scripts/incremental_update.py status

# Reset processing state
python scripts/incremental_update.py reset
```

**Parameters**:
- `command`: Action to perform (`quick`, `status`, `reset`)
- `--csv`: CSV file path (default: from CSV_FILE env var)
- `--batch-size`: Batch size for processing (default: 10)

**Features**:
- 🏃 **Batch Processing**: Process papers in configurable batches
- 💾 **State Management**: Track processed papers and resume capability
- 📈 **Progress Monitoring**: Real-time progress updates
- 🔄 **Automatic README Update**: Updates README after processing

## Workflow Examples

### Scenario 1: New Project Setup
```bash
# 1. Initialize project
python scripts/setup.py

# 2. Configure API key in .env file
echo "GEMINI_API_KEY=your-api-key" >> .env

# 3. Prepare your papers CSV file
# Place your CSV file at data/papers.csv

# 4. Run complete sync
python scripts/sync_readme.py
```

### Scenario 2: Adding New Papers from ArXiv
```bash
# 1. Create a text file with ArXiv URLs
echo "https://arxiv.org/abs/2401.12345" > new_urls.txt
echo "https://arxiv.org/abs/2401.12346" >> new_urls.txt

# 2. Process URLs and update README
python scripts/arxiv_mcp_client.py --urls-file new_urls.txt --update-readme
```

### Scenario 3: Regular Maintenance
```bash
# 1. Check status
python scripts/incremental_update.py status

# 2. Process new papers only
python scripts/incremental_update.py quick

# 3. Generate summary report
python scripts/update_readme.py summary
```

### Scenario 4: Recovering from Interruption
```bash
# If sync_readme.py was interrupted, simply run it again
python scripts/sync_readme.py
# It will automatically resume from where it left off

# If you want to start completely fresh
python scripts/sync_readme.py --clear-cache --force
```

## Configuration Files

### Environment Variables (.env)
```bash
# Required: Gemini API configuration
GEMINI_API_KEY=your-gemini-api-key

# Optional: Custom Gemini endpoint
GEMINI_BASE_URL=https://custom-endpoint.com

# Optional: Default CSV file path
CSV_FILE=data/papers.csv
```

### CSV Input Format
Your CSV file should have these columns (Chinese headers are also supported):

| Column | Chinese | Description |
|--------|---------|-------------|
| Contributor | 分享人 | Person who shared the paper |
| Share Date | 分享时间 | Date when paper was shared |
| Title | 标题 | Paper title |
| Date | 日期 | Publication date |
| Link | 链接 | Paper URL |
| Tags | 标签 | Paper tags/keywords |
| Summary | 总结/评论 | Summary or comments |
| Attachment | 附件 | Additional attachments |

### Cache Files Structure
```
data/
├── arxiv_cache.json          # ArXiv API cache
├── classified_papers.json    # Final classified papers
├── sync_progress.json        # Sync progress cache
├── update_state.json         # Incremental update state
└── classification_progress.json # Classification progress
```

## Troubleshooting

### Common Issues

#### 1. API Key Not Found
```
Error: GEMINI_API_KEY not found in environment variables
```
**Solution**: Add your API key to `.env` file:
```bash
echo "GEMINI_API_KEY=your-api-key" >> .env
```

#### 2. CSV File Not Found
```
Error: CSV file not found: data/papers.csv
```
**Solution**: Either place your CSV file at the specified path or use custom path:
```bash
python scripts/sync_readme.py --csv /path/to/your/papers.csv
```

#### 3. JSON Parse Errors
If you see JSON parsing errors during classification, the script will:
- Automatically retry up to 3 times
- Create fallback results for failed classifications
- Continue processing remaining papers

#### 4. Rate Limiting
The scripts include built-in rate limiting (1 second delay between requests) to respect API limits.

#### 5. Memory Issues with Large Datasets
For very large CSV files (>1000 papers):
- Use incremental update: `python scripts/incremental_update.py quick`
- Process in smaller batches: `--batch-size 5`
- Clear cache periodically: `--clear-cache`

### Recovery Procedures

#### Reset All Progress
```bash
# Clear all caches and start fresh
python scripts/sync_readme.py --clear-cache --force
```

#### Backup and Restore
```bash
# Backup current data
cp -r data/ data_backup/

# Restore from backup
rm -rf data/
cp -r data_backup/ data/
```

## API Reference

### PaperClassifier Class
```python
from classify_papers import PaperClassifier

classifier = PaperClassifier(api_key, base_url)
is_related, main_cat, sub_cat, explanation = classifier.classify_paper(paper)
```

### ReadmeUpdater Class
```python
from update_readme import ReadmeUpdater

updater = ReadmeUpdater()
updater.update_readme("data/classified_papers.json")
```

### ArxivMCPClient Class
```python
from arxiv_mcp_client import ArxivMCPClient

client = ArxivMCPClient("data/arxiv_cache.json")
paper = client.process_arxiv_url("https://arxiv.org/abs/2401.12345")
```

---

## Support

For issues and questions:
1. Check this documentation first
2. Review error messages and try suggested solutions
3. Check the project's issue tracker
4. Ensure your API key and dependencies are properly configured

**Happy paper organizing! 📚🤖**