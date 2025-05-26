#!/usr/bin/env python3
"""
ArXiv MCP Client for AI-Era Education Paper Classification
Extracts and classifies papers from arXiv URLs using arXiv API with MCP cache support
"""

import asyncio
import os
import sys
import re
import json
import time
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

# Classification imports
from openai import OpenAI
from dotenv import load_dotenv

# Import existing Paper class and PaperClassifier
from classify_papers import Paper, PaperClassifier
from update_readme import ReadmeUpdater

# Load environment variables
load_dotenv()

@dataclass
class ArxivPaperInfo:
    """ArXiv paper information"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: str
    url: str
    pdf_url: str

class ArxivMCPClient:
    """ArXiv client for paper extraction and classification with MCP cache support"""
    
    def __init__(self, cache_file: str = "data/arxiv_cache.json"):
        """Initialize the client"""
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
        # Initialize classifier
        api_key = os.getenv('GEMINI_API_KEY')
        base_url = os.getenv('GEMINI_BASE_URL')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.classifier = PaperClassifier(api_key, base_url)
        print("✓ ArXiv client initialized with cache support")
    
    def _load_cache(self) -> Dict[str, Dict]:
        """Load cached paper data"""
        if Path(self.cache_file).exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                print(f"✓ Loaded cache with {len(cache)} papers from {self.cache_file}")
                return cache
            except Exception as e:
                print(f"⚠ Error loading cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print(f"✓ Cache saved with {len(self.cache)} papers")
        except Exception as e:
            print(f"⚠ Error saving cache: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean text by replacing newlines with spaces and normalizing whitespace"""
        if not text:
            return text
        # Replace newlines with spaces, then normalize multiple spaces to single space
        return ' '.join(text.replace('\n', ' ').split())
    
    def extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from URL"""
        patterns = [
            r'arxiv\.org/abs/(\d+\.\d+)',
            r'arxiv\.org/pdf/(\d+\.\d+)',
            r'arxiv\.org/html/(\d+\.\d+)',
            r'(\d{4}\.\d{4,5})',  # Direct ID pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_paper_from_cache(self, arxiv_id: str) -> Optional[ArxivPaperInfo]:
        """Get paper from cache if available"""
        clean_id = arxiv_id.split('v')[0]
        if clean_id in self.cache:
            data = self.cache[clean_id]
            print(f"✓ Found paper in cache: {data.get('title', '')[:50]}...")
            return ArxivPaperInfo(
                paper_id=data.get('paper_id', clean_id),
                title=data.get('title', ''),
                authors=data.get('authors', []),
                abstract=data.get('abstract', ''),
                categories=data.get('categories', []),
                published=data.get('published', ''),
                url=data.get('url', ''),
                pdf_url=data.get('pdf_url', '')
            )
        return None
    
    def fetch_from_arxiv_api(self, arxiv_id: str) -> Optional[ArxivPaperInfo]:
        """Fetch paper from arXiv API"""
        try:
            print(f"🌐 Fetching from arXiv API: {arxiv_id}")
            
            clean_id = arxiv_id.split('v')[0]
            api_url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
            
            with urllib.request.urlopen(api_url) as response:
                if response.status == 200:
                    xml_content = response.read().decode('utf-8')
                    root = ET.fromstring(xml_content)
                    
                    entry = root.find('{http://www.w3.org/2005/Atom}entry')
                    if entry is not None:
                        # Extract information
                        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                        title = self._clean_text(title_elem.text) if title_elem is not None else f"Paper {arxiv_id}"
                        
                        # Authors
                        authors = []
                        for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                            name_elem = author.find('{http://www.w3.org/2005/Atom}name')
                            if name_elem is not None:
                                authors.append(self._clean_text(name_elem.text))
                        
                        # Abstract
                        summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                        abstract = self._clean_text(summary_elem.text) if summary_elem is not None else "Abstract not available"
                        
                        # Categories
                        categories = []
                        primary_cat = entry.find('{http://arxiv.org/schemas/atom}primary_category')
                        if primary_cat is not None:
                            categories.append(primary_cat.get('term', ''))
                        
                        for category in entry.findall('{http://arxiv.org/schemas/atom}category'):
                            term = category.get('term')
                            if term and term not in categories:
                                categories.append(term)
                        
                        # Published date
                        published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                        published = published_elem.text.strip() if published_elem is not None else ""
                        
                        # URLs
                        url = f"https://arxiv.org/abs/{clean_id}"
                        pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
                        
                        print(f"✓ Successfully fetched from arXiv API: {title[:50]}...")
                        
                        paper_info = ArxivPaperInfo(
                            paper_id=clean_id,
                            title=title,
                            authors=authors,
                            abstract=abstract,
                            categories=categories,
                            published=published,
                            url=url,
                            pdf_url=pdf_url
                        )
                        
                        # Cache the result
                        self.cache[clean_id] = asdict(paper_info)
                        self._save_cache()
                        
                        return paper_info
                    else:
                        print("✗ No entry found in arXiv API response")
                else:
                    print(f"✗ arXiv API returned status {response.status}")
                    
        except Exception as e:
            print(f"⚠ arXiv API error: {e}")
        
        return None
    
    def get_paper_info(self, arxiv_id: str) -> Optional[ArxivPaperInfo]:
        """Get paper info from cache or arXiv API"""
        # Try cache first
        paper_info = self.get_paper_from_cache(arxiv_id)
        if paper_info:
            return paper_info
        
        # Fetch from arXiv API
        return self.fetch_from_arxiv_api(arxiv_id)
    
    def convert_to_paper_object(self, arxiv_info: ArxivPaperInfo) -> Paper:
        """Convert ArxivPaperInfo to Paper object for classification"""
        tags = ", ".join(arxiv_info.categories) if arxiv_info.categories else ""
        
        paper = Paper(
            sharer="ArXiv MCP Client",
            share_date=time.strftime("%Y-%m-%d"),
            title=arxiv_info.title,
            date=arxiv_info.published,
            link=arxiv_info.url,
            tags=tags,
            summary=arxiv_info.abstract,
            attachment=arxiv_info.pdf_url
        )
        
        return paper
    
    def process_arxiv_url(self, url: str) -> Optional[Paper]:
        """Process an arXiv URL: extract info and classify"""
        print(f"\n🔍 Processing arXiv URL: {url}")
        
        # Extract arXiv ID
        arxiv_id = self.extract_arxiv_id(url)
        if not arxiv_id:
            print(f"✗ Could not extract arXiv ID from URL: {url}")
            return None
        
        print(f"📄 Extracted arXiv ID: {arxiv_id}")
        
        # Get paper information
        arxiv_info = self.get_paper_info(arxiv_id)
        if not arxiv_info:
            print(f"✗ Could not find paper information for ID: {arxiv_id}")
            return None
        
        print(f"✓ Found paper: {arxiv_info.title}")
        
        # Convert to Paper object
        paper = self.convert_to_paper_object(arxiv_info)
        
        # Classify the paper
        print("🤖 Classifying paper...")
        is_related, main_cat, sub_cat, explanation = self.classifier.classify_paper(paper)
        
        # Update paper with classification results
        paper.is_education_related = is_related
        paper.main_category = main_cat
        paper.sub_category = sub_cat
        paper.category_explanation = explanation
        
        # Print classification results
        print(f"\n📊 Classification Results:")
        print(f"   Education Related: {is_related}")
        if is_related:
            print(f"   Main Category: {main_cat}")
            print(f"   Sub Category: {sub_cat}")
        print(f"   Explanation: {explanation}")
        
        return paper
    
    def process_multiple_urls(self, urls: List[str]) -> List[Paper]:
        """Process multiple arXiv URLs"""
        papers = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"Processing paper {i}/{len(urls)}")
            print(f"{'='*60}")
            
            try:
                paper = self.process_arxiv_url(url)
                if paper:
                    papers.append(paper)
                    print(f"✓ Successfully processed paper {i}")
                else:
                    print(f"✗ Failed to process paper {i}")
                
                # Rate limiting
                if i < len(urls):
                    print("⏳ Waiting 1 second before next paper...")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"✗ Error processing paper {i}: {str(e)}")
        
        return papers
    
    def load_mcp_results(self, mcp_file: str) -> List[Paper]:
        """Load papers from MCP results file and add to cache"""
        try:
            with open(mcp_file, 'r', encoding='utf-8') as f:
                mcp_data = json.load(f)
            
            papers = []
            added_to_cache = 0
            
            # Handle different MCP result formats
            if isinstance(mcp_data, dict) and 'papers' in mcp_data:
                papers_data = mcp_data['papers']
            elif isinstance(mcp_data, list):
                papers_data = mcp_data
            else:
                print(f"⚠ Unknown MCP file format")
                return []
            
            for paper_data in papers_data:
                # Add to cache if not already present
                paper_id = paper_data.get('id', '')
                if paper_id and paper_id not in self.cache:
                    self.cache[paper_id] = {
                        'paper_id': paper_id,
                        'title': paper_data.get('title', ''),
                        'authors': paper_data.get('authors', []),
                        'abstract': paper_data.get('summary', ''),
                        'categories': paper_data.get('categories', []),
                        'published': paper_data.get('published', ''),
                        'url': paper_data.get('url', f"https://arxiv.org/abs/{paper_id}"),
                        'pdf_url': paper_data.get('pdf_url', f"https://arxiv.org/pdf/{paper_id}.pdf")
                    }
                    added_to_cache += 1
                
                # Convert to Paper object if it has classification info
                if 'is_education_related' in paper_data:
                    paper = Paper(
                        sharer="MCP Results",
                        share_date=paper_data.get('share_date', time.strftime("%Y-%m-%d")),
                        title=paper_data.get('title', ''),
                        date=paper_data.get('date', ''),
                        link=paper_data.get('link', ''),
                        tags=paper_data.get('tags', ''),
                        summary=paper_data.get('summary', ''),
                        attachment=paper_data.get('attachment', ''),
                        is_education_related=paper_data.get('is_education_related', False),
                        main_category=paper_data.get('main_category', ''),
                        sub_category=paper_data.get('sub_category', ''),
                        category_explanation=paper_data.get('category_explanation', '')
                    )
                    papers.append(paper)
            
            if added_to_cache > 0:
                self._save_cache()
                print(f"✓ Added {added_to_cache} papers to cache from MCP results")
            
            print(f"✓ Loaded {len(papers)} classified papers from MCP results")
            return papers
            
        except Exception as e:
            print(f"✗ Error loading MCP results: {e}")
            return []
    
    def save_results(self, papers: List[Paper], output_file: str):
        """Save classification results to JSON file"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        papers_data = []
        for paper in papers:
            paper_dict = asdict(paper)
            papers_data.append(paper_dict)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def print_summary(self, papers: List[Paper]):
        """Print summary of classification results"""
        if not papers:
            print("\n📊 No papers processed.")
            return
        
        total = len(papers)
        education_related = [p for p in papers if p.is_education_related]
        
        print(f"\n📊 Classification Summary:")
        print(f"   Total papers processed: {total}")
        print(f"   Education-related papers: {len(education_related)}")
        print(f"   Non-education papers: {total - len(education_related)}")
        
        if education_related:
            categories = {}
            for paper in education_related:
                cat = paper.main_category
                if cat in categories:
                    categories[cat] += 1
                else:
                    categories[cat] = 1
            
            print(f"\n   By category:")
            for cat, count in categories.items():
                print(f"     {cat}: {count}")
    
    def update_readme_with_papers(self, papers: List[Paper], existing_papers_file: str = "data/classified_papers.json"):
        """Update README with new papers, avoiding duplicates"""
        if not papers:
            print("\n⚠ No papers to add to README")
            return
        
        education_related = [p for p in papers if p.is_education_related]
        if not education_related:
            print("\n⚠ No education-related papers to add to README")
            return
        
        print(f"\n📝 Checking for duplicates and updating README...")
        
        try:
            # Load existing papers to check for duplicates
            existing_papers = []
            if Path(existing_papers_file).exists():
                with open(existing_papers_file, 'r', encoding='utf-8') as f:
                    existing_papers = json.load(f)
            
            # Create sets of existing titles and links for fast lookup
            existing_titles = {p.get('title', '').strip().lower() for p in existing_papers}
            existing_links = {p.get('link', '').strip() for p in existing_papers}
            
            # Filter out duplicates
            new_papers = []
            duplicates_found = 0
            
            for paper in education_related:
                title_lower = paper.title.strip().lower()
                link = paper.link.strip()
                
                # Check for duplicates by title or link
                is_duplicate = (
                    title_lower in existing_titles or 
                    link in existing_links or
                    any(title_lower in existing_title or existing_title in title_lower 
                        for existing_title in existing_titles if len(existing_title) > 10)
                )
                
                if not is_duplicate:
                    new_papers.append(paper)
                else:
                    duplicates_found += 1
                    print(f"⚠ Skipping duplicate: {paper.title[:50]}...")
            
            if duplicates_found > 0:
                print(f"📋 Found {duplicates_found} duplicate papers, skipping them")
            
            if not new_papers:
                print("✓ No new papers to add (all were duplicates)")
                return
            
            print(f"📝 Adding {len(new_papers)} new education-related papers to README...")
            
            updater = ReadmeUpdater()
            
            # Convert only new papers to the format expected by update_readme
            papers_data = []
            for paper in papers:  # Include all papers (not just education-related) for completeness
                paper_dict = asdict(paper)
                papers_data.append(paper_dict)
            
            # Filter papers_data to only include new ones
            new_papers_data = []
            new_titles = {p.title.strip().lower() for p in new_papers}
            for paper_dict in papers_data:
                if paper_dict.get('title', '').strip().lower() in new_titles:
                    new_papers_data.append(paper_dict)
            
            if not new_papers_data:
                print("✓ No new papers to add after duplicate filtering")
                return
            
            temp_file = "data/temp_arxiv_papers.json"
            Path(temp_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(new_papers_data, f, ensure_ascii=False, indent=2)
            
            updater.add_new_papers(temp_file, existing_papers_file)
            updater.update_readme(existing_papers_file)
            
            Path(temp_file).unlink(missing_ok=True)
            
            print(f"✓ README updated successfully with {len(new_papers)} new papers!")
            
        except Exception as e:
            print(f"✗ Error updating README: {str(e)}")
            print("💡 You can manually update the README using:")
            print(f"   python scripts/update_readme.py add --new-papers {temp_file if 'temp_file' in locals() else 'your_results_file.json'}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract and classify arXiv papers with cache support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single arXiv URL
  python arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345"
  
  # Process multiple URLs from a file
  python arxiv_mcp_client.py --urls-file urls.txt
  
  # Process and automatically update README
  python arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345" --update-readme
  
  # Load MCP results and update README
  python arxiv_mcp_client.py --mcp-results results.json --update-readme
  
  # Use custom cache file
  python arxiv_mcp_client.py --url "https://arxiv.org/abs/2401.12345" --cache-file my_cache.json
        """
    )
    
    parser.add_argument('--url', help='Single arXiv URL to process')
    parser.add_argument('--urls-file', help='File containing arXiv URLs (one per line)')
    parser.add_argument('--mcp-results', help='Load papers from MCP results file')
    parser.add_argument('--cache-file', default='data/arxiv_cache.json',
                       help='Cache file for arXiv paper data')
    parser.add_argument('--output', default='data/arxiv_mcp_results.json',
                       help='Output file for results')
    parser.add_argument('--update-readme', action='store_true',
                       help='Automatically update README with classified papers')
    parser.add_argument('--existing-papers', default='data/classified_papers.json',
                       help='Existing papers file for README update')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.url and not args.urls_file and not args.mcp_results:
        parser.error("Either --url, --urls-file, or --mcp-results must be specified")
    
    print(f"🚀 Starting ArXiv MCP Client")
    print(f"💾 Cache file: {args.cache_file}")
    
    # Initialize client
    client = ArxivMCPClient(args.cache_file)
    
    try:
        papers = []
        
        # Load from MCP results if specified
        if args.mcp_results:
            if not Path(args.mcp_results).exists():
                print(f"✗ MCP results file not found: {args.mcp_results}")
                return
            papers.extend(client.load_mcp_results(args.mcp_results))
        
        # Collect URLs to process
        urls = []
        if args.url:
            urls.append(args.url)
        
        if args.urls_file:
            if not Path(args.urls_file).exists():
                print(f"✗ URLs file not found: {args.urls_file}")
                return
            
            with open(args.urls_file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                urls.extend(file_urls)
        
        # Process URLs
        if urls:
            print(f"📋 URLs to process: {len(urls)}")
            new_papers = client.process_multiple_urls(urls)
            papers.extend(new_papers)
        
        # Save results
        if papers:
            client.save_results(papers, args.output)
            client.print_summary(papers)
            
            # Update README if requested
            if args.update_readme:
                client.update_readme_with_papers(papers, args.existing_papers)
        else:
            print("✗ No papers were processed")
    
    except KeyboardInterrupt:
        print("\n⚠ Process interrupted by user")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 