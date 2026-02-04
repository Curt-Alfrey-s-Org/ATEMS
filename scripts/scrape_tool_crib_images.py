#!/usr/bin/env python3
"""
Scrape tool crib images from web for splash screen and UI.
Downloads professional tool crib/tool room images.
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Create images directory
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'tool_cribs')
os.makedirs(IMAGES_DIR, exist_ok=True)

# Search terms for tool crib images
SEARCH_TERMS = [
    "professional tool crib",
    "industrial tool room",
    "tool storage system",
    "manufacturing tool crib",
    "organized tool storage",
]

# Unsplash API (free, no key needed for basic use)
UNSPLASH_SEARCH_URL = "https://unsplash.com/napi/search/photos"

def download_image(url, filename):
    """Download an image from URL."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            filepath = os.path.join(IMAGES_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ Downloaded: {filename}")
            return True
    except Exception as e:
        print(f"  ✗ Failed to download {filename}: {e}")
    return False


def scrape_unsplash(query, limit=5):
    """Scrape images from Unsplash."""
    print(f"\nSearching Unsplash for: {query}")
    try:
        params = {
            'query': query,
            'per_page': limit,
        }
        response = requests.get(UNSPLASH_SEARCH_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            for i, photo in enumerate(results):
                url = photo['urls']['regular']  # High quality
                filename = f"unsplash_{query.replace(' ', '_')}_{i+1}.jpg"
                download_image(url, filename)
                time.sleep(1)  # Be respectful
            return len(results)
    except Exception as e:
        print(f"  Error scraping Unsplash: {e}")
    return 0


def create_placeholder_images():
    """Create placeholder images if scraping fails."""
    from PIL import Image, ImageDraw, ImageFont
    
    placeholders = [
        ("tool_crib_1.jpg", "Professional Tool Crib", (44, 62, 80)),
        ("tool_crib_2.jpg", "Organized Storage", (52, 73, 94)),
        ("tool_crib_3.jpg", "Industrial Tools", (41, 128, 185)),
    ]
    
    for filename, text, color in placeholders:
        filepath = os.path.join(IMAGES_DIR, filename)
        if os.path.exists(filepath):
            continue
        
        # Create 1920x1080 image
        img = Image.new('RGB', (1920, 1080), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        img.save(filepath, 'JPEG', quality=90)
        print(f"  ✓ Created placeholder: {filename}")


def main():
    print("=" * 60)
    print("ATEMS Tool Crib Image Scraper")
    print("=" * 60)
    
    total_downloaded = 0
    
    # Try Unsplash (free, high quality)
    for term in SEARCH_TERMS[:2]:  # Limit to avoid rate limiting
        count = scrape_unsplash(term, limit=3)
        total_downloaded += count
        time.sleep(2)
    
    # Create placeholders if needed
    if total_downloaded == 0:
        print("\nNo images downloaded, creating placeholders...")
        create_placeholder_images()
    
    print(f"\n✓ Complete: {total_downloaded} images downloaded")
    print(f"  Images saved to: {IMAGES_DIR}")


if __name__ == "__main__":
    main()
