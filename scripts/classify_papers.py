#!/usr/bin/env python3
"""
AI-Era Education Paper Classification System
Classifies papers using Gemini 2.5 Flash API
"""

import os
import sys
import json
import time
import csv
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Paper:
    """Paper data structure"""
    sharer: str  # Contributor
    share_date: str  # Share date
    title: str  # Title
    date: str  # Publication date
    link: str  # Link
    tags: str  # Tags
    summary: str  # Summary/Comments
    attachment: str  # Attachment
    
    # Classification results
    is_education_related: bool = False
    main_category: str = ""  # ai, intersection, education
    sub_category: str = ""
    category_explanation: str = ""

class PaperClassifier:
    """Paper classifier using Gemini API"""
    
    def __init__(self, api_key: str, base_url: str = None):
        """Initialize classifier"""
        self.api_key = api_key
        
        # Initialize OpenAI client with custom base URL support
        if base_url:
            print(f"✓ Using custom base URL: {base_url}")
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            print("✓ Using default OpenAI endpoint")
            self.client = OpenAI(api_key=api_key)
        
        # Model name for Gemini 2.5 Flash
        self.model_name = "gemini-2.5-flash-preview-05-20"
        
        # Simplified category definitions (2-3 subcategories per main category)
        self.categories = {
            "ai": {
                "name": "AI-Focused",
                "description": "Technical AI research with potential educational applications",
                "subcategories": {
                    "ai_models": "Model Architecture & Training",
                    "ai_evaluation": "Evaluation & Benchmarks"
                }
            },
            "intersection": {
                "name": "AI+Education Intersection", 
                "description": "Deep integration of AI and education",
                "subcategories": {
                    "intersection_systems": "Intelligent Tutoring Systems",
                    "intersection_analytics": "Learning Analytics & Student Modeling",
                    "intersection_content": "Content Generation & Assessment"
                }
            },
            "education": {
                "name": "Education-Focused",
                "description": "Educational theory and pedagogy",
                "subcategories": {
                    "education_theory": "Learning Theory & Research",
                    "education_practice": "Teaching Methods & Practice"
                }
            }
        }

    def _create_classification_prompt(self, paper: Paper) -> str:
        """Create classification prompt"""
        return f"""
You are an expert in AI and Education research. Please analyze the following paper and classify it.

Paper Information:
Title: {paper.title}
Tags: {paper.tags}
Summary: {paper.summary}

Classification Task:
1. First, determine if this paper is STRONGLY related to education (not just mentioning it briefly)
2. If related, classify into one of these categories:

**AI-Focused (ai)**: Technical AI research with potential educational applications
- ai_models: Model Architecture & Training (LLMs, VLMs, multimodal models, training methods)
- ai_evaluation: Evaluation & Benchmarks (educational benchmarks, capability assessment)

**AI+Education Intersection (intersection)**: Deep integration of AI and education
- intersection_systems: Intelligent Tutoring Systems (personalized learning, adaptive teaching, AI tutors)
- intersection_analytics: Learning Analytics & Student Modeling (student behavior analysis, knowledge tracing)
- intersection_content: Content Generation & Assessment (question generation, automated grading)

**Education-Focused (education)**: Educational theory and pedagogy  
- education_theory: Learning Theory & Research (learning sciences, cognitive science, educational psychology)
- education_practice: Teaching Methods & Practice (classroom teaching, collaborative learning, teacher development)

Exclusion Criteria:
- Pure computer vision/NLP papers without educational context
- General AI safety/alignment papers without educational focus
- Papers that only briefly mention educational applications

IMPORTANT: Respond with ONLY valid JSON in this exact format:
{{
    "is_education_related": true,
    "main_category": "ai",
    "sub_category": "ai_models", 
    "explanation": "Brief reasoning for classification"
}}

Or for non-education papers:
{{
    "is_education_related": false,
    "main_category": null,
    "sub_category": null, 
    "explanation": "Brief reasoning for rejection"
}}

Do NOT include any text before or after the JSON. Do NOT wrap in markdown code blocks.
"""

    def classify_paper(self, paper: Paper) -> Tuple[bool, str, str, str]:
        """Classify a single paper with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                prompt = self._create_classification_prompt(paper)
                
                # Use OpenAI client for chat completion
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                # Check if response is valid
                if not response or not response.choices or len(response.choices) == 0:
                    raise ValueError("No response from API")
                
                message_content = response.choices[0].message.content
                if message_content is None:
                    raise ValueError("API returned null content")
                
                # Extract response text
                response_text = message_content.strip()
                if not response_text:
                    raise ValueError("API returned empty response")
                
                # Debug: Show raw response for first few papers
                if hasattr(self, '_debug_count'):
                    self._debug_count += 1
                else:
                    self._debug_count = 1
                
                if self._debug_count <= 3:
                    print(f"DEBUG - Raw API response: {response_text}")
                
                # Try to extract JSON from response (sometimes it's wrapped in markdown)
                json_text = response_text
                
                # Remove markdown code blocks if present
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    if json_end > json_start:
                        json_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    if json_end > json_start:
                        json_text = response_text[json_start:json_end].strip()
                
                # Parse JSON response
                try:
                    result = json.loads(json_text)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON response: {json_text[:300]}...")
                    
                    # Check if response was truncated and try to fix it
                    if "Unterminated string" in str(e) and json_text.count('"') % 2 != 0:
                        # Try to close the unterminated string and object
                        fixed_json = json_text + '"}'
                        try:
                            result = json.loads(fixed_json)
                            print("✓ Fixed truncated JSON response")
                        except:
                            # If still can't parse, create basic result
                            result = {
                                "is_education_related": False,
                                "main_category": "",
                                "sub_category": "",
                                "explanation": f"JSON parse error (truncated): {str(e)}"
                            }
                    else:
                        # Try to create a basic result from text analysis
                        result = {
                            "is_education_related": False,
                            "main_category": "",
                            "sub_category": "",
                            "explanation": f"JSON parse error: {str(e)}"
                        }
                
                is_related = result.get("is_education_related", False)
                main_cat = result.get("main_category", "")
                sub_cat = result.get("sub_category", "")
                explanation = result.get("explanation", "")
                
                return is_related, main_cat, sub_cat, explanation
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Error classifying paper '{paper.title}': {str(e)}")
                    return False, "", "", f"Classification error: {str(e)}"

    def load_papers_from_csv(self, csv_file: str) -> List[Paper]:
        """Load papers from CSV file"""
        papers = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                paper = Paper(
                    sharer=row.get('分享人', ''),
                    share_date=row.get('分享时间', ''),
                    title=row.get('标题', ''),
                    date=row.get('日期', ''),
                    link=row.get('链接', ''),
                    tags=row.get('标签', ''),
                    summary=row.get('总结/评论', ''),
                    attachment=row.get('附件', '')
                )
                papers.append(paper)
        
        return papers

    def classify_papers(self, papers: List[Paper], start_idx: int = 0) -> List[Paper]:
        """Classify multiple papers with progress saving"""
        classified_papers = papers.copy()
        
        for i, paper in enumerate(papers[start_idx:], start_idx):
            print(f"Processing paper {i+1}/{len(papers)}: {paper.title[:80]}...")
            
            try:
                is_related, main_cat, sub_cat, explanation = self.classify_paper(paper)
                
                classified_papers[i].is_education_related = is_related
                classified_papers[i].main_category = main_cat
                classified_papers[i].sub_category = sub_cat
                classified_papers[i].category_explanation = explanation
                
                # Save progress every 10 papers
                if (i + 1) % 10 == 0:
                    self.save_progress(classified_papers, "data/classification_progress.json")
                    print(f"Progress saved at paper {i+1}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing paper {i+1}: {str(e)}")
                classified_papers[i].category_explanation = f"Error: {str(e)}"
        
        return classified_papers

    def save_progress(self, papers: List[Paper], filename: str):
        """Save classification progress"""
        # Ensure data directory exists
        Path(filename).parent.mkdir(exist_ok=True)
        
        # Convert to serializable format
        papers_data = []
        for paper in papers:
            paper_dict = asdict(paper)
            papers_data.append(paper_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, ensure_ascii=False, indent=2)
        
        print(f"Progress saved to {filename}")

    def load_progress(self, filename: str) -> List[Paper]:
        """Load classification progress"""
        if not Path(filename).exists():
            return []
        
        with open(filename, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        papers = []
        for data in papers_data:
            paper = Paper(**data)
            papers.append(paper)
        
        return papers

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify AI education papers')
    parser.add_argument('--csv', default=os.getenv('CSV_FILE', 'data/papers.csv'),
                       help='CSV file path')
    parser.add_argument('--output', default='data/classified_papers.json',
                       help='Output JSON file path')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous progress')
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    base_url = os.getenv('GEMINI_BASE_URL')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please set it in .env file: GEMINI_API_KEY=your-api-key")
        return
    
    # Initialize classifier
    classifier = PaperClassifier(api_key, base_url)
    
    # Load or resume classification
    if args.resume:
        papers = classifier.load_progress("data/classification_progress.json")
        if papers:
            print(f"Resuming from {len(papers)} papers")
        else:
            papers = classifier.load_papers_from_csv(args.csv)
    else:
        papers = classifier.load_papers_from_csv(args.csv)
    
    print(f"Starting classification of {len(papers)} papers...")
    
    # Find starting index for resume
    start_idx = 0
    if args.resume:
        for i, paper in enumerate(papers):
            if not paper.is_education_related and not paper.category_explanation:
                start_idx = i
                break
        else:
            start_idx = len(papers)  # All papers already processed
    
    # Classify papers
    classified_papers = classifier.classify_papers(papers, start_idx)
    
    # Save final results
    classifier.save_progress(classified_papers, args.output)
    
    # Print summary
    education_related = [p for p in classified_papers if p.is_education_related]
    print(f"\nClassification complete!")
    print(f"Total papers: {len(classified_papers)}")
    print(f"Education-related: {len(education_related)}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main() 