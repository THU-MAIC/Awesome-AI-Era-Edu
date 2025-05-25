#!/usr/bin/env python3
"""
One-Stop README Sync Script
Automatically classifies papers from CSV and updates README
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add scripts to path
sys.path.append('scripts')
from classify_papers import PaperClassifier, Paper
from update_readme import ReadmeUpdater

class ReadmeSync:
    """One-stop CSV to README synchronization"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.classifier = PaperClassifier(api_key, base_url)
        self.readme_updater = ReadmeUpdater()
        
        # File paths
        self.csv_file = os.getenv('CSV_FILE', "data/papers.csv")
        self.classified_file = "data/classified_papers.json"
        self.progress_file = "data/classification_progress.json"
        
    def load_existing_papers(self):
        """Load existing classified papers"""
        if not Path(self.classified_file).exists():
            return [], set()
        
        try:
            with open(self.classified_file, 'r', encoding='utf-8') as f:
                papers_data = json.load(f)
            
            papers = []
            titles = set()
            
            for data in papers_data:
                try:
                    # Handle both old and new format
                    paper = Paper(**data)
                    papers.append(paper)
                    titles.add(paper.title)
                except TypeError:
                    # Handle dict format
                    paper_dict = {
                        'sharer': data.get('sharer', ''),
                        'share_date': data.get('share_date', ''),
                        'title': data.get('title', ''),
                        'date': data.get('date', ''),
                        'link': data.get('link', ''),
                        'tags': data.get('tags', ''),
                        'summary': data.get('summary', ''),
                        'attachment': data.get('attachment', ''),
                        'is_education_related': data.get('is_education_related', False),
                        'main_category': data.get('main_category', ''),
                        'sub_category': data.get('sub_category', ''),
                        'category_explanation': data.get('category_explanation', '')
                    }
                    paper = Paper(**paper_dict)
                    papers.append(paper)
                    titles.add(paper.title)
            
            return papers, titles
            
        except Exception as e:
            print(f"Warning: Error loading existing papers: {e}")
            return [], set()
    
    def get_new_papers(self, csv_file: str, existing_titles: set):
        """Get papers from CSV that haven't been classified yet"""
        if not Path(csv_file).exists():
            print(f"Error: CSV file not found: {csv_file}")
            return []
        
        # Load all papers from CSV
        all_papers = self.classifier.load_papers_from_csv(csv_file)
        
        # Filter out already processed papers and papers with insufficient context
        new_papers = []
        skipped_papers = []
        
        for paper in all_papers:
            if paper.title in existing_titles:
                continue
            
            # Check if paper has sufficient context for classification
            title = paper.title.strip()
            tags = paper.tags.strip()
            summary = paper.summary.strip()
            
            # Skip papers with insufficient context
            if not title or (not tags and not summary):
                skipped_papers.append({
                    'title': title or 'No title',
                    'reason': 'Missing title, tags, and summary'
                })
                continue
            
            # Skip papers with very minimal content
            total_content_length = len(title) + len(tags) + len(summary)
            if total_content_length < 20:  # Minimum threshold
                skipped_papers.append({
                    'title': title,
                    'reason': f'Too little content ({total_content_length} chars)'
                })
                continue
            
            new_papers.append(paper)
        
        # Report skipped papers
        if skipped_papers:
            print(f"⚠️  Skipped {len(skipped_papers)} papers with insufficient context:")
            for i, skipped in enumerate(skipped_papers[:5]):  # Show first 5
                print(f"   {i+1}. {skipped['title'][:50]}... - {skipped['reason']}")
            if len(skipped_papers) > 5:
                print(f"   ... and {len(skipped_papers) - 5} more")
        
        return new_papers
    
    def classify_new_papers(self, new_papers):
        """Classify new papers with progress display and caching"""
        if not new_papers:
            return []
        
        print(f"📊 Classifying {len(new_papers)} new papers...")
        print("-" * 50)
        
        # Load existing progress
        progress_file = "data/sync_progress.json"
        processed_titles = set()
        classified_papers = []
        
        if Path(progress_file).exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    processed_titles = set(progress_data.get('processed_titles', []))
                    
                    # Load already classified papers
                    for paper_data in progress_data.get('classified_papers', []):
                        paper = Paper(
                            sharer=paper_data['sharer'],
                            share_date=paper_data['share_date'],
                            title=paper_data['title'],
                            date=paper_data['date'],
                            link=paper_data['link'],
                            tags=paper_data['tags'],
                            summary=paper_data['summary'],
                            attachment=paper_data['attachment']
                        )
                        paper.is_education_related = paper_data['is_education_related']
                        paper.main_category = paper_data['main_category']
                        paper.sub_category = paper_data['sub_category']
                        paper.category_explanation = paper_data['category_explanation']
                        classified_papers.append(paper)
                        
                print(f"📁 Resuming from progress: {len(processed_titles)} papers already processed")
            except Exception as e:
                print(f"⚠️  Could not load progress: {e}")
                processed_titles = set()
                classified_papers = []
        
        # Filter out already processed papers
        remaining_papers = [p for p in new_papers if p.title not in processed_titles]
        
        if not remaining_papers:
            print("✅ All papers already processed!")
            return classified_papers
        
        print(f"🔄 Processing {len(remaining_papers)} remaining papers...")
        
        for i, paper in enumerate(remaining_papers):
            current_remaining = i + 1
            total_remaining = len(remaining_papers)
            total_processed = len(processed_titles) + current_remaining
            total_new = len(new_papers)
            
            print(f"[{current_remaining}/{total_remaining}] {paper.title[:60]}...")
            
            try:
                is_related, main_cat, sub_cat, explanation = self.classifier.classify_paper(paper)
                
                paper.is_education_related = is_related
                paper.main_category = main_cat
                paper.sub_category = sub_cat
                paper.category_explanation = explanation
                
                classified_papers.append(paper)
                processed_titles.add(paper.title)
                
                # Show result
                if is_related:
                    print(f"    ✓ {main_cat} > {sub_cat}")
                else:
                    print(f"    ✗ Not education-related")
                
                # Save progress every 5 papers
                if (i + 1) % 5 == 0:
                    self._save_progress(classified_papers, processed_titles, progress_file)
                    print(f"    💾 Progress saved ({total_processed}/{total_new} total)")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                paper.category_explanation = f"Error: {str(e)}"
                classified_papers.append(paper)
                processed_titles.add(paper.title)
        
        # Save final progress
        self._save_progress(classified_papers, processed_titles, progress_file)
        print(f"💾 Final progress saved!")
        
        return classified_papers
    
    def _save_progress(self, classified_papers, processed_titles, progress_file):
        """Save classification progress"""
        Path("data").mkdir(exist_ok=True)
        
        progress_data = {
            'processed_titles': list(processed_titles),
            'classified_papers': []
        }
        
        for paper in classified_papers:
            paper_data = {
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
            progress_data['classified_papers'].append(paper_data)
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def save_all_papers(self, papers):
        """Save all papers to classified_papers.json"""
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Convert to serializable format
        papers_data = []
        for paper in papers:
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
        
        with open(self.classified_file, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved {len(papers)} papers to {self.classified_file}")
    
    def update_readme(self):
        """Update README with classified papers"""
        print("\n📝 Updating README...")
        print("-" * 30)
        
        try:
            self.readme_updater.update_readme(self.classified_file)
            print("✅ README updated successfully!")
        except Exception as e:
            print(f"❌ Error updating README: {e}")
            return False
        
        return True
    
    def print_summary(self, all_papers, new_papers):
        """Print summary of the sync operation"""
        print("\n" + "="*60)
        print("📋 SYNC SUMMARY")
        print("="*60)
        
        # Count education-related papers
        education_papers = [p for p in all_papers if p.is_education_related]
        new_education_papers = [p for p in new_papers if p.is_education_related]
        
        print(f"📊 Total papers in database: {len(all_papers)}")
        print(f"🎓 Education-related papers: {len(education_papers)}")
        print(f"🆕 New papers processed: {len(new_papers)}")
        print(f"📚 New education papers: {len(new_education_papers)}")
        
        # Category breakdown
        if education_papers:
            print(f"\n📈 Category Distribution:")
            from collections import Counter
            category_counts = Counter()
            
            for paper in education_papers:
                if paper.sub_category in self.readme_updater.category_mapping:
                    main_cat, sub_name = self.readme_updater.category_mapping[paper.sub_category]
                    category_counts[f"{main_cat} > {sub_name}"] += 1
            
            for category, count in category_counts.most_common():
                print(f"  {category}: {count} papers")
        
        print(f"\n⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
    
    def sync(self, csv_file: str = None):
        """Main sync function"""
        # Use default CSV file if not specified
        if csv_file is None:
            csv_file = self.csv_file
        
        print("🚀 Starting README Sync...")
        print("="*60)
        print(f"📁 CSV file: {csv_file}")
        print(f"📄 Output: {self.classified_file}")
        print(f"📖 README: README.md")
        
        # Check if CSV file exists
        if not Path(csv_file).exists():
            print(f"❌ Error: CSV file not found: {csv_file}")
            return False
        
        # Load existing papers
        print(f"\n📚 Loading existing papers...")
        existing_papers, existing_titles = self.load_existing_papers()
        print(f"✓ Found {len(existing_papers)} existing papers")
        
        # Get new papers from CSV
        print(f"\n🔍 Checking for new papers...")
        new_papers = self.get_new_papers(csv_file, existing_titles)
        
        if new_papers:
            print(f"✓ Found {len(new_papers)} new papers to classify")
            
            # Classify new papers
            classified_new_papers = self.classify_new_papers(new_papers)
            
            # Combine all papers
            all_papers = existing_papers + classified_new_papers
        else:
            print(f"✓ No new papers found - all papers already classified")
            all_papers = existing_papers
            classified_new_papers = []
        
        # Save all papers
        if new_papers:
            self.save_all_papers(all_papers)
        
        # Update README
        success = self.update_readme()
        
        # Print summary
        self.print_summary(all_papers, classified_new_papers)
        
        return success

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='One-stop CSV to README sync',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync_readme.py                           # Use default CSV file (resumes from cache)
  python sync_readme.py --csv my_papers.csv      # Use custom CSV file
  python sync_readme.py --force                  # Force re-classification of all papers
  python sync_readme.py --clear-cache            # Clear progress cache and start fresh
  
Features:
  • Automatic progress caching - resumes from interruptions
  • Saves progress every 5 papers
  • Progress file: data/sync_progress.json
        """
    )
    
    parser.add_argument('--csv', 
                       help='CSV file path (default: data/papers.csv)')
    parser.add_argument('--force', action='store_true',
                       help='Force re-classification of all papers')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear progress cache and start fresh')
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    base_url = os.getenv('GEMINI_BASE_URL')
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found")
        print("Set it in .env file: GEMINI_API_KEY=your-api-key")
        return 1
    
    # Initialize syncer
    syncer = ReadmeSync(api_key, base_url)
    
    # Handle clear cache
    if args.clear_cache:
        progress_file = "data/sync_progress.json"
        if Path(progress_file).exists():
            backup_file = f"{progress_file}.backup.{int(time.time())}"
            Path(progress_file).rename(backup_file)
            print(f"🧹 Progress cache cleared (backup: {backup_file})")
        else:
            print("🧹 No progress cache to clear")
    
    # Handle force re-classification
    if args.force:
        print("🔄 Force mode: Will re-classify all papers")
        if Path(syncer.classified_file).exists():
            backup_file = f"{syncer.classified_file}.backup.{int(time.time())}"
            Path(syncer.classified_file).rename(backup_file)
            print(f"📦 Backup created: {backup_file}")
        # Also clear progress cache in force mode
        progress_file = "data/sync_progress.json"
        if Path(progress_file).exists():
            Path(progress_file).unlink()
            print(f"🧹 Progress cache cleared")
    
    # Run sync
    success = syncer.sync(args.csv)
    
    if success:
        print("\n🎉 Sync completed successfully!")
        return 0
    else:
        print("\n💥 Sync failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 