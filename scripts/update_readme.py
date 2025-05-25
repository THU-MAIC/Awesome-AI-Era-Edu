#!/usr/bin/env python3
"""
README Updater for AI-Era Education Repository
Automatically updates README with classified papers
"""

import json
import re
from datetime import datetime
from typing import Dict, List
from collections import defaultdict, Counter
from pathlib import Path

class ReadmeUpdater:
    """README updater with automatic content generation"""
    
    def __init__(self):
        # Simplified category mapping (2-3 subcategories per main category)
        self.category_mapping = {
            # AI-Focused
            "ai_models": ("AI-Focused", "Model Architecture & Training"),
            "ai_evaluation": ("AI-Focused", "Evaluation & Benchmarks"),
            
            # AI+Education Intersection  
            "intersection_systems": ("AI+Education Intersection", "Intelligent Tutoring Systems"),
            "intersection_analytics": ("AI+Education Intersection", "Learning Analytics & Student Modeling"),
            "intersection_content": ("AI+Education Intersection", "Content Generation & Assessment"),
            
            # Education-Focused
            "education_theory": ("Education-Focused", "Learning Theory & Research"),
            "education_practice": ("Education-Focused", "Teaching Methods & Practice")
        }

    def load_papers(self, json_file: str) -> List[Dict]:
        """Load papers from JSON file"""
        with open(json_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        # Filter education-related papers only
        return [p for p in papers if p.get('is_education_related', False)]

    def format_paper_entry(self, paper: Dict) -> str:
        """Format paper entry with only title and link"""
        title = paper.get('title', 'Untitled')
        link = paper.get('link', '#')
        
        # Create markdown entry with just title and link
        if link and link != '#':
            entry = f"- **[{title}]({link})**"
        else:
            entry = f"- **{title}**"
        
        return entry

    def group_papers_by_category(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """Group papers by category"""
        grouped = defaultdict(list)
        
        for paper in papers:
            sub_category = paper.get('sub_category', '')
            if sub_category in self.category_mapping:
                grouped[sub_category].append(paper)
        
        return grouped

    def update_statistics(self, content: str, papers: List[Dict]) -> str:
        """Update statistics in README"""
        # Total paper count
        total_count = len(papers)
        
        # Count by main category
        category_counts = Counter()
        for paper in papers:
            sub_category = paper.get('sub_category', '')
            if sub_category in self.category_mapping:
                main_category, _ = self.category_mapping[sub_category]
                category_counts[main_category] += 1
        
        # Count by subcategory
        sub_category_counts = Counter()
        for paper in papers:
            sub_category = paper.get('sub_category', '')
            if sub_category in self.category_mapping:
                sub_category_counts[sub_category] += 1
        
        # Update total count
        content = re.sub(
            r'- \*\*Total Papers\*\*: \d+',
            f'- **Total Papers**: {total_count}',
            content
        )
        
        # Update last updated date
        current_date = datetime.now().strftime('%Y-%m-%d')
        content = re.sub(
            r'- \*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}',
            f'- **Last Updated**: {current_date}',
            content
        )
        
        # Update category counts in table of contents
        for sub_category, count in sub_category_counts.items():
            if sub_category in self.category_mapping:
                _, sub_name = self.category_mapping[sub_category]
                pattern = f'- \\*\\*{re.escape(sub_name)}\\*\\*: \\d+ papers'
                replacement = f'- **{sub_name}**: {count} papers'
                content = re.sub(pattern, replacement, content)
        
        return content

    def update_paper_sections(self, content: str, grouped_papers: Dict[str, List[Dict]]) -> str:
        """Update paper sections with content"""
        for sub_category, papers in grouped_papers.items():
            if sub_category not in self.category_mapping:
                continue
                
            # Create content for this category
            paper_entries = []
            for paper in papers:
                entry = self.format_paper_entry(paper)
                paper_entries.append(entry)
            
            papers_content = '\n'.join(paper_entries)
            
            # Update the section
            start_marker = f"<!-- PAPERS_START:{sub_category} -->"
            end_marker = f"<!-- PAPERS_END:{sub_category} -->"
            
            pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
            replacement = f"{start_marker}\n{papers_content}\n{end_marker}"
            
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        return content

    def update_readme(self, papers_file: str, readme_file: str = "README.md"):
        """Update README with classified papers"""
        print(f"Updating README from {papers_file}...")
        
        # Load papers
        papers = self.load_papers(papers_file)
        print(f"Loaded {len(papers)} education-related papers")
        
        # Group by category
        grouped_papers = self.group_papers_by_category(papers)
        
        # Read current README
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update statistics
        content = self.update_statistics(content, papers)
        
        # Update paper sections
        content = self.update_paper_sections(content, grouped_papers)
        
        # Write updated README
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"README updated successfully!")
        
        # Print summary
        print(f"\nSummary:")
        print(f"Total papers: {len(papers)}")
        for category, paper_list in grouped_papers.items():
            if category in self.category_mapping:
                _, name = self.category_mapping[category]
                print(f"  {name}: {len(paper_list)} papers")

    def add_new_papers(self, new_papers_file: str, existing_papers_file: str = "data/classified_papers.json"):
        """Add new papers to existing collection"""
        # Load existing papers
        if Path(existing_papers_file).exists():
            with open(existing_papers_file, 'r', encoding='utf-8') as f:
                existing_papers = json.load(f)
        else:
            existing_papers = []
        
        # Load new papers
        with open(new_papers_file, 'r', encoding='utf-8') as f:
            new_papers = json.load(f)
        
        # Get existing titles to avoid duplicates
        existing_titles = {p.get('title', '') for p in existing_papers}
        
        # Add new papers that don't exist
        added_count = 0
        for paper in new_papers:
            if paper.get('title', '') not in existing_titles:
                existing_papers.append(paper)
                added_count += 1
        
        # Save updated collection
        with open(existing_papers_file, 'w', encoding='utf-8') as f:
            json.dump(existing_papers, f, ensure_ascii=False, indent=2)
        
        print(f"Added {added_count} new papers to {existing_papers_file}")

    def generate_category_summary(self, papers_file: str):
        """Generate summary report by category"""
        papers = self.load_papers(papers_file)
        grouped = self.group_papers_by_category(papers)
        
        print("Category Summary Report")
        print("=" * 50)
        
        total_papers = len(papers)
        print(f"Total Education-Related Papers: {total_papers}\n")
        
        # Summary by main category
        main_category_counts = Counter()
        for paper in papers:
            sub_category = paper.get('sub_category', '')
            if sub_category in self.category_mapping:
                main_category, _ = self.category_mapping[sub_category]
                main_category_counts[main_category] += 1
        
        for main_cat, count in main_category_counts.most_common():
            percentage = (count / total_papers) * 100 if total_papers > 0 else 0
            print(f"{main_cat}: {count} papers ({percentage:.1f}%)")
        
        print("\nDetailed Breakdown:")
        print("-" * 30)
        
        for sub_category, paper_list in sorted(grouped.items()):
            if sub_category in self.category_mapping:
                main_cat, sub_name = self.category_mapping[sub_category]
                count = len(paper_list)
                percentage = (count / total_papers) * 100 if total_papers > 0 else 0
                print(f"{main_cat} > {sub_name}: {count} papers ({percentage:.1f}%)")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update README with classified papers')
    parser.add_argument('command', choices=['update', 'add', 'summary'],
                       help='Command to execute')
    parser.add_argument('--papers', default='data/classified_papers.json',
                       help='Papers JSON file path')
    parser.add_argument('--readme', default='README.md',
                       help='README file path')
    parser.add_argument('--new-papers', 
                       help='New papers file for add command')
    
    args = parser.parse_args()
    
    updater = ReadmeUpdater()
    
    if args.command == 'update':
        updater.update_readme(args.papers, args.readme)
    elif args.command == 'add':
        if not args.new_papers:
            print("Error: --new-papers required for add command")
            return
        updater.add_new_papers(args.new_papers, args.papers)
        updater.update_readme(args.papers, args.readme)
    elif args.command == 'summary':
        updater.generate_category_summary(args.papers)

if __name__ == "__main__":
    main() 