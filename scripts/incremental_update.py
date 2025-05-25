#!/usr/bin/env python3
"""
Incremental Update System for AI-Era Education Repository
Handles incremental classification and README updates
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, Set, List
from datetime import datetime

# Import other modules
import sys
sys.path.append(str(Path(__file__).parent))

from classify_papers import PaperClassifier, Paper
from update_readme import ReadmeUpdater

class IncrementalUpdater:
    """Incremental update system"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.classifier = PaperClassifier(api_key, base_url)
        self.readme_updater = ReadmeUpdater()
        self.state_file = "data/update_state.json"

    def load_state(self) -> Dict:
        """Load processing state"""
        if Path(self.state_file).exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "last_processed": 0,
            "processed_titles": [],
            "last_update": None,
            "total_papers": 0
        }

    def save_state(self, state: Dict):
        """Save processing state"""
        # Ensure data directory exists
        Path(self.state_file).parent.mkdir(exist_ok=True)
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def get_new_papers(self, csv_file: str) -> List[Paper]:
        """Get new papers that haven't been processed"""
        # Load current state
        state = self.load_state()
        processed_titles = set(state.get("processed_titles", []))
        
        # Load all papers from CSV
        all_papers = self.classifier.load_papers_from_csv(csv_file)
        
        # Filter out already processed papers
        new_papers = []
        for paper in all_papers:
            if paper.title not in processed_titles:
                new_papers.append(paper)
        
        return new_papers

    def process_new_papers(self, csv_file: str, batch_size: int = 10) -> bool:
        """Process new papers incrementally"""
        print(f"Starting incremental update from {csv_file}...")
        
        # Get new papers
        new_papers = self.get_new_papers(csv_file)
        
        if not new_papers:
            print("No new papers to process")
            return True
        
        print(f"Found {len(new_papers)} new papers to process")
        
        # Load existing classified papers
        classified_file = "data/classified_papers.json"
        if Path(classified_file).exists():
            with open(classified_file, 'r', encoding='utf-8') as f:
                classified_papers = []
                existing_data = json.load(f)
                for data in existing_data:
                    try:
                        paper = Paper(**data)
                        classified_papers.append(paper)
                    except TypeError:
                        # Handle old format
                        paper = Paper(
                            sharer=data.get('sharer', ''),
                            share_date=data.get('share_date', ''),
                            title=data.get('title', ''),
                            date=data.get('date', ''),
                            link=data.get('link', ''),
                            tags=data.get('tags', ''),
                            summary=data.get('summary', ''),
                            attachment=data.get('attachment', ''),
                            is_education_related=data.get('is_education_related', False),
                            main_category=data.get('main_category', ''),
                            sub_category=data.get('sub_category', ''),
                            category_explanation=data.get('category_explanation', '')
                        )
                        classified_papers.append(paper)
        else:
            classified_papers = []
        
        # Load state
        state = self.load_state()
        processed_titles = set(state.get("processed_titles", []))
        
        # Process papers in batches
        for i in range(0, len(new_papers), batch_size):
            batch = new_papers[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(new_papers)-1)//batch_size + 1}")
            
            for j, paper in enumerate(batch):
                print(f"  Classifying paper {i+j+1}/{len(new_papers)}: {paper.title[:60]}...")
                
                try:
                    is_related, main_cat, sub_cat, explanation = self.classifier.classify_paper(paper)
                    
                    paper.is_education_related = is_related
                    paper.main_category = main_cat
                    paper.sub_category = sub_cat
                    paper.category_explanation = explanation
                    
                    classified_papers.append(paper)
                    processed_titles.add(paper.title)
                    
                except Exception as e:
                    print(f"    Error: {str(e)}")
                    paper.category_explanation = f"Error: {str(e)}"
                    classified_papers.append(paper)
                    processed_titles.add(paper.title)
            
            # Save batch progress
            self._save_batch_progress(classified_papers, state, processed_titles)
            print(f"  Batch completed, progress saved")
        
        # Save final results
        self._save_final_results(classified_papers, state, processed_titles)
        print(f"\nIncremental update completed!")
        print(f"Processed {len(new_papers)} new papers")
        
        return True

    def _save_batch_progress(self, classified_papers: List[Paper], state: Dict, processed_titles: Set[str]):
        """Save batch processing progress"""
        # Save classified papers
        papers_data = []
        for paper in classified_papers:
            paper_dict = {
                'sharer': paper.sharer,
                'share_date': paper.share_date,
                'title': paper.title,
                'date': paper.date,
                'link': paper.link,
                'tags': paper.tags,
                'summary': paper.summary,
                'attachment': paper.attachment,
                'is_education_related': paper.is_education_related,
                'main_category': paper.main_category,
                'sub_category': paper.sub_category,
                'category_explanation': paper.category_explanation
            }
            papers_data.append(paper_dict)
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        with open("data/classified_papers.json", 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, ensure_ascii=False, indent=2)
        
        # Update state
        state["processed_titles"] = list(processed_titles)
        state["total_papers"] = len(classified_papers)
        state["last_update"] = datetime.now().isoformat()
        self.save_state(state)

    def _save_final_results(self, classified_papers: List[Paper], state: Dict, processed_titles: Set[str]):
        """Save final processing results"""
        # Save classified papers
        self._save_batch_progress(classified_papers, state, processed_titles)
        
        # Update README
        print("Updating README...")
        try:
            self.readme_updater.update_readme("data/classified_papers.json")
            print("README updated successfully")
        except Exception as e:
            print(f"Error updating README: {str(e)}")
        
        # Print summary
        education_related = [p for p in classified_papers if p.is_education_related]
        print(f"\nFinal Summary:")
        print(f"Total papers in database: {len(classified_papers)}")
        print(f"Education-related papers: {len(education_related)}")
        
        # Category breakdown
        from collections import Counter
        category_counts = Counter()
        for paper in education_related:
            if paper.sub_category and paper.sub_category in self.readme_updater.category_mapping:
                main_cat, _ = self.readme_updater.category_mapping[paper.sub_category]
                category_counts[main_cat] += 1
        
        for category, count in category_counts.most_common():
            print(f"  {category}: {count} papers")

    def reset_state(self):
        """Reset processing state"""
        if Path(self.state_file).exists():
            Path(self.state_file).unlink()
            print("Processing state reset")
        else:
            print("No state file found")

    def show_status(self):
        """Show current processing status"""
        state = self.load_state()
        
        print("Processing Status")
        print("-" * 30)
        print(f"Last update: {state.get('last_update', 'Never')}")
        print(f"Total papers in database: {state.get('total_papers', 0)}")
        print(f"Processed titles: {len(state.get('processed_titles', []))}")
        
        # Check for new papers
        csv_file = os.getenv('CSV_FILE', "data/papers.csv")
        if Path(csv_file).exists():
            new_papers = self.get_new_papers(csv_file)
            print(f"New papers available: {len(new_papers)}")
        else:
            print("CSV file not found")

    def quick_update(self, csv_file: str = None):
        """Quick update workflow"""
        print("Starting quick update...")
        
        # Use default CSV file if not specified
        if csv_file is None:
            csv_file = os.getenv('CSV_FILE', "data/papers.csv")
        
        # Check if CSV file exists
        if not Path(csv_file).exists():
            print(f"Error: CSV file not found: {csv_file}")
            return False
        
        # Process new papers
        success = self.process_new_papers(csv_file)
        
        if success:
            print("Quick update completed successfully!")
        else:
            print("Quick update failed")
        
        return success

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Incremental update system')
    parser.add_argument('command', 
                       choices=['quick', 'status', 'reset'],
                       help='Command to execute')
    parser.add_argument('--csv', 
                       default=os.getenv('CSV_FILE', 'data/papers.csv'),
                       help='CSV file path')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    base_url = os.getenv('GEMINI_BASE_URL')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please set it in .env file: GEMINI_API_KEY=your-api-key")
        return
    
    # Initialize updater
    updater = IncrementalUpdater(api_key, base_url)
    
    if args.command == 'quick':
        updater.quick_update(args.csv)
    elif args.command == 'status':
        updater.show_status()
    elif args.command == 'reset':
        updater.reset_state()

if __name__ == "__main__":
    main() 