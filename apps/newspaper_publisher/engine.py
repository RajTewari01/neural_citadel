"""
Neural Citadel Newspaper Engine
===============================
Core engine for fetching news from RSS feeds and generating PDF newspapers/magazines.
Patterned after apps.image_gen.engine.DiffusionEngine.
"""

import os
import time
import shutil
import requests
import uuid
import sys
import subprocess
import json
import newspaper
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from newspaper import Article

# Ensure project root is in path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import Config and Registry
from apps.newspaper_publisher.config_types import NewsConfig
from apps.newspaper_publisher.templates import get_template_class, get_substyles, MAG_STYLES
from apps.newspaper_publisher.templates.factory import TemplateClass  # Keep for backwards compat

# Configuration Paths
from configs.paths import NEWSPAPER_OUTPUT_DIR, NEWSPAPER_TEMP_DIR

class NewsEngine:
    """
    Production-grade News Engine.
    Handles fetching, parsing, and PDF generation with temp file management.
    Supports both legacy API and new NewsConfig-based API.
    """
    
    def __init__(self):
        """Initialize the NewsEngine."""
        self.articles = []
        self.temp_files = [] # Track temp images for cleanup
        self.config: Optional[NewsConfig] = None
        
        # Ensure temp dir exists
        NEWSPAPER_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # NEW CONFIG-BASED API (Recommended)
    # =========================================================================
    
    def fetch_with_config(self, config: NewsConfig, feeds_list: List[Dict]) -> List[Dict]:
        """
        Fetch articles using NewsConfig settings.
        
        Args:
            config: NewsConfig instance with fetch settings
            feeds_list: List of feed dicts with 'name', 'url', 'category'
            
        Returns:
            List of article dicts
        """
        self.config = config
        return self.fetch_parallel(
            feeds_list,
            limit_per_feed=config.limit_per_feed,
            max_workers=config.max_workers
        )
    
    def generate_with_config(self, config: NewsConfig, articles: List[Dict]) -> Path:
        """
        Generate PDF using NewsConfig settings.
        
        Args:
            config: NewsConfig instance with generation settings
            articles: List of article dicts
            
        Returns:
            Path to generated PDF
        """
        self.config = config
        
        print(f"[DEBUG] Engine Config Language: '{config.language}'")
        
        # TRANSLATION LAYER
        if config.language and config.language.lower() != "english":
            print(f"[Engine] Translation requested: {config.language} (mode: {config.translation_mode})")
            articles = self.translate_articles(articles, config.language, config.translation_mode)
        
        # Resolve substyle for Magazine
        style_name = config.style
        if config.style.lower() == 'magazine':
            if config.substyle and config.substyle in MAG_STYLES:
                style_name = config.substyle
            else:
                import random
                style_name = random.choice(list(MAG_STYLES.keys()))
                print(f"   -> Auto-selected Magazine Style: {style_name}")
        
        # Generate output filename
        safe_style = style_name.lower().replace(' ', '_')
        output_filename = config.output_dir / f"{safe_style}_{config.category}_ALL_{uuid.uuid4().hex[:8]}.pdf"
        
        return Path(self.generate_publication(articles, style_name, str(output_filename)))
    
    def translate_articles(self, articles: List[Dict], target_lang: str, mode: str = "online") -> List[Dict]:
        """
        Run translation subprocess using CoreAgentVenv (offline) or GlobalVenv (online).
        Handles dependency isolation by using temp files and subprocess.
        """
        # Define paths
        if mode == "offline":
            # Use CoreAgentVenv for NLLB model
            core_python = r"D:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"
        else:
            # Use global Python for deep-translator (online)
            core_python = sys.executable
            
        translator_script = PROJECT_ROOT / "apps/newspaper_publisher/language/translator.py"
        
        if mode == "offline" and not os.path.exists(core_python):
            print(f"[WARN] CoreAgent Python not found: {core_python}")
            return articles
            
        # Temp file for data transfer
        temp_json = NEWSPAPER_TEMP_DIR / f"trans_input_{uuid.uuid4().hex[:6]}.json"
        self.temp_files.append(temp_json) # Mark for cleanup just in case
        
        try:
            # 1. Dump articles (handle datetime serialization)
            def json_serial(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
                
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, default=json_serial)
                
            # 2. Call Subprocess
            print(f"[Engine] Calling Translator Subprocess ({target_lang}, {mode})...")
            cmd = [
                core_python, 
                str(translator_script),
                "--input", str(temp_json),
                "--lang", target_lang,
                "--mode", mode
            ]
            
            # Run - inherit stdout/stderr so user sees progress
            subprocess.run(cmd, check=True)
            
            # 3. Load back
            with open(temp_json, 'r', encoding='utf-8') as f:
                translated_articles = json.load(f)
                
            # Remove from temp_files tracking since we handled it (optional)
            return translated_articles
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Translation subprocess failed code {e.returncode}")
            return articles # Return original as fallback
        except Exception as e:
            print(f"[ERROR] Translation wrapper error: {e}")
            return articles
        finally:
            if temp_json.exists():
                try:
                    os.remove(temp_json)
                except: pass
        
    # =========================================================================
    # LEGACY API (Still supported)
    # =========================================================================
    
    def _download_image(self, url):
        """
        Download image to temp directory, resizing it for optimization.
        Returns Path to local file or None if failed.
        """
        if not url:
            return None
            
        try:
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                # Use Pillow to handle image processing
                from PIL import Image
                from io import BytesIO
                
                # Load image from bytes
                img = Image.open(BytesIO(response.content))
                
                # Convert to RGB (fixes RGBA/P palette issues for JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                    
                # Resize if too large (Optimization)
                max_width = 600
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Generate filename
                filename = f"img_{uuid.uuid4().hex[:8]}.jpg"
                save_path = NEWSPAPER_TEMP_DIR / filename
                
                # Save optimized JPEG
                img.save(save_path, "JPEG", quality=85, optimize=True)
                
                self.temp_files.append(save_path)
                return str(save_path)
                
        except Exception as e:
            # print(f"   [!] Image download failed: {e}")
            pass
            
        return None

    def cleanup(self):
        """Remove all temporary files created during this session."""
        print(f"[Engine] Cleaning up {len(self.temp_files)} temp files...")
        for path in self.temp_files:
            try:
                if isinstance(path, str): path = Path(path)
                if path.exists():
                    os.remove(path)
            except Exception as e:
                print(f"   [!] Failed to delete {path}: {e}")
        self.temp_files = []
        print("[Engine] Cleanup complete.")

    def fetch_parallel(self, feeds_list, limit_per_feed=5, max_workers=10):
        """
        Fetch from multiple feeds in parallel using ThreadPoolExecutor.
        Aggregates all found articles into a single list.
        """
        import concurrent.futures
        
        print(f"\n[Engine] [START] Starting Parallel Fetch from {len(feeds_list)} feeds...")
        print(f"         (Max Workers: {max_workers}, Limit/Feed: {limit_per_feed})")
        
        all_articles = []
        start_time = time.time()
        
        # Helper to wrap the fetch call
        def _job(feed_data):
            # feed_data is a dict: {'name':..., 'url':..., 'category':...}
            try:
                # We use a smaller limit per feed for aggregate runs
                res = self.fetch_from_feed(feed_data['url'], category=feed_data.get('category', 'General'), limit=limit_per_feed)
                print(f"   -> {feed_data['name']}: Found {len(res)} articles")
                return res
            except Exception as e:
                print(f"   [!] Error processing {feed_data.get('name')}: {e}")
                return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_feed = {executor.submit(_job, feed): feed for feed in feeds_list}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_feed):
                feed = future_to_feed[future]
                try:
                    data = future.result()
                    if data:
                        all_articles.extend(data)
                except Exception as exc:
                    print(f"   [!] Feed {feed['name']} generated an exception: {exc}")
        
        print(f"\n[Engine] [DONE] Parallel Fetch Complete!")
        print(f"         Total Articles: {len(all_articles)}")
        print(f"         Time Taken: {time.time() - start_time:.2f}s")
        
        return all_articles

    def fetch_from_feed(self, feed_url, category="General", limit=16):
        """
        Fetch and parse articles from an RSS feed URL.
        Downloads images to temp storage.
        """
        # print(f"\n[Engine] Building source: {feed_url}...")
        # start_time = time.time()
        
        # Build the source with custom Config to avoid blocking
        from newspaper import Config, Article
        import feedparser
        import requests
        
        # Browser-like User-Agent
        USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        config = Config()
        config.browser_user_agent = USER_AGENT
        config.request_timeout = 10
        
        try:
            # 1. Fetch RSS XML content manually using requests (to handle User-Agent)
            response = requests.get(feed_url, headers={'User-Agent': USER_AGENT}, timeout=10)
            response.raise_for_status()
            
            # 2. Parse content with feedparser
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                # print(f"   [!] feedparser found no entries for {feed_url}")
                return []
                
            entries = feed.entries
            # print(f"   -> Found {len(entries)} entries via feedparser")
            
        except Exception as e:
            # print(f"   [!] Failed to parse feed: {e}")
            return []
        
        parsed_articles = []
        count = 0
        
        # Prioritize articles to reach limit
        for entry in entries:
            if count >= limit:
                break
                
            try:
                url = entry.link
                article = Article(url, config=config)
                
                # Download and Parse
                try:
                    article.download()
                    article.parse()
                except:
                    # If parsing fails, we might still have data from RSS entry (title, summary)
                    pass
                
                # Try to get image if article parsed successfully
                image_path = None
                if hasattr(article, 'top_image') and article.top_image:
                    try:
                        image_path = self._download_image(article.top_image)
                    except:
                        pass
                
                # STRICT REQUIREMENT: "every news should have a image"
                if not image_path:
                    # Skip if no image found
                    # print(f"   [-] Skipped (No Image): {article.title[:30]}")
                    continue

                # Fallback content from RSS if newspaper failed to extract text
                rss_summary = entry.get('summary', '') or entry.get('description', '')
                
                # Clean up summary (sometimes it has HTML)
                import re
                if rss_summary:
                    rss_summary = re.sub('<[^<]+?>', '', rss_summary) # Basic strip tags
                
                final_content = article.text if (article.text and len(article.text) > 50) else rss_summary
                
                # Validation: Needs Title.
                if not article.title and not rss_summary:
                    continue
                    
                # Create Article Dict
                art_dict = {
                    'title': article.title if article.title else entry.get('title', 'Untitled'),
                    'author': str(article.authors[0]) if article.authors else "Staff Writer",
                    'category': category.upper(),
                    'image': image_path, # Local path to temp file
                    'content': final_content,
                    'date': article.publish_date if article.publish_date else datetime.now()
                }
                
                parsed_articles.append(art_dict)
                count += 1
                if count % 5 == 0:
                    print(f"   [+] Parsed ({count}/{limit}): {article.title[:30]}...")
                
            except Exception as e:
                print(f"   [!] Failed to parse article: {e}")
                continue
                
        # print(f"[Engine] Fetch complete. Retrieved {len(parsed_articles)} articles in {time.time() - start_time:.2f}s")
        return parsed_articles

    def generate_publication(self, articles, style_name, output_filename):
        """
        Generate the PDF publication using the Template engine.
        """
        print(f"\n[Engine] Generating Publication: {style_name}")
        print(f"   -> Output: {output_filename}")
        print(f"   -> Content: {len(articles)} articles")
        
        try:
            # Instantiate Template
            # TemplateClass factory handles style logic
            pub = TemplateClass(output_filename, style_name=style_name)
            
            # Build PDF
            start_time = time.time()
            pub.build(articles)
            
            print(f"[Engine] Generation complete in {time.time() - start_time:.2f}s")
            return output_filename
            
        except Exception as e:
            print(f"   [!] Generation logic failed: {e}")
            import traceback
            traceback.print_exc()
            raise e

