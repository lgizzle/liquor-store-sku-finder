import asyncio
import aiohttp
import requests
import json
import os
import csv
import time
import re
from urllib.parse import quote, urljoin
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
from PIL import Image
import logging
from dotenv import load_dotenv
import config

# Load environment variables
load_dotenv()


@dataclass
class ImageResult:
    """Data class to store image search results"""

    sku: str
    source: str
    image_url: str
    title: str
    price: Optional[str] = None
    description: Optional[str] = None
    local_path: Optional[str] = None
    confidence: float = 0.0


class SKUPictureFinder:
    """Main class for finding product images using SKU numbers"""

    def __init__(self, output_dir: str = "./images", max_images: int = 5, min_resolution: Optional[tuple] = None):
        self.output_dir = Path(output_dir)
        self.max_images = max_images
        # Set minimum resolution with fallback strategy
        if min_resolution:
            self.min_width, self.min_height = min_resolution
        else:
            self.min_width = getattr(config, 'MINIMUM_IMAGE_WIDTH', 300)
            self.min_height = getattr(config, 'MINIMUM_IMAGE_HEIGHT', 300)
        self.session = requests.Session()
        self.results = []

        # Setup logging
        self.setup_logging()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # User agent string for web requests
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "sku_finder.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def find_images(self, sku: str) -> List[ImageResult]:
        """
        Main method to find product images for a given SKU using only Go-UPC API.
        """
        self.logger.info(f"Starting image search for SKU: {sku}")

        # Only use Go-UPC as the image source
        search_methods = [
            self._search_go_upc
        ]

        all_results = []
        for method in search_methods:
            try:
                method_results = method(sku)
                if method_results:
                    all_results.extend(method_results)
                    self.logger.info(f"{method.__name__} found {len(method_results)} images")
                if len(all_results) >= self.max_images:
                    break
            except Exception as e:
                self.logger.warning(f"Error in {method.__name__}: {str(e)}")
                continue

        # Sort by confidence (not really needed with one source, but kept for compatibility)
        all_results.sort(key=lambda x: -x.confidence)

        # Download images
        downloaded_results = []
        for result in all_results[:self.max_images]:
            downloaded_path = self._download_image(result.image_url, sku, result.source)
            if downloaded_path:
                result.local_path = str(downloaded_path)
                downloaded_results.append(result)
                self.logger.info(f"Downloaded image from {result.source}: {downloaded_path}")

        self.results.extend(downloaded_results)
        self.logger.info(f"Successfully found {len(downloaded_results)} images for SKU {sku}")
        return downloaded_results

    def _get_source_priority(self, source: str) -> int:
        """Return priority for source (lower number = higher priority)"""
        priorities = {
            'UPC Database': 1,
            'Open Food Facts': 2,
            'Walmart': 3,
            'Target': 4,
            'Total Wine': 5,
            'BevMo': 6,
            'Amazon Marketplace': 7,
            'Google Images': 8,
            'Bing Images': 9
        }
        return priorities.get(source, 10)

    def _search_go_upc(self, sku: str) -> List[ImageResult]:
        """Search Go-UPC API for product images by UPC/SKU"""
        results = []
        api_key = os.getenv('GO_UPC_API_KEY')
        if not api_key:
            self.logger.warning("GO_UPC_API_KEY not found in environment.")
            return results
        url = f"https://go-upc.com/api/v1/code/{sku}"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                product = data.get('product', {})
                image_url = product.get('image')
                title = product.get('name', f"Product {sku}")
                if image_url:
                    results.append(ImageResult(
                        sku=sku,
                        source="Go-UPC",
                        image_url=image_url,
                        title=title,
                        confidence=1.0
                    ))
            else:
                self.logger.info(f"Go-UPC API returned status {response.status_code} for {sku}")
        except Exception as e:
            self.logger.warning(f"Go-UPC API error for {sku}: {str(e)}")
        return results

    def _search_upc_database(self, sku: str) -> List[ImageResult]:
        """Search UPC Database for product images"""
        results = []
        try:
            # First try the API endpoint
            api_url = f"https://api.upcdatabase.org/product/{sku}"
            headers = {"Authorization": f"Bearer {os.getenv('UPC_DATABASE_API_KEY', '')}"}

            response = self.session.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('images') and len(data['images']) > 0:
                    for img_url in data['images'][:3]:
                        results.append(ImageResult(
                            sku=sku,
                            source="UPC Database",
                            image_url=img_url,
                            title=data.get('title', f"Product {sku}"),
                            confidence=0.9
                        ))

            # Fallback to web scraping
            if not results:
                web_url = f"https://www.upcdatabase.org/item/{sku}"
                response = self.session.get(web_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    img_tags = soup.find_all('img')

                    for img in img_tags:
                        img_url = img.get('src')
                        if img_url and ('product' in img_url.lower() or 'item' in img_url.lower()):
                            if not img_url.startswith('http'):
                                img_url = urljoin(web_url, img_url)
                            results.append(ImageResult(
                                sku=sku,
                                source="UPC Database",
                                image_url=img_url,
                                title=f"Product {sku}",
                                confidence=0.8
                            ))

        except Exception as e:
            self.logger.warning(f"Error in UPC Database search: {str(e)}")

        return results[:self.max_images]

    def _search_open_food_facts(self, sku: str) -> List[ImageResult]:
        """Search Open Food Facts for product images"""
        results = []
        try:
            api_url = f"https://world.openfoodfacts.org/api/v0/product/{sku}.json"
            response = self.session.get(api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1 and 'product' in data:
                    product = data['product']

                    # Get various image fields
                    image_fields = ['image_url', 'image_front_url', 'image_front_small_url']
                    for field in image_fields:
                        img_url = product.get(field)
                        if img_url:
                            results.append(ImageResult(
                                sku=sku,
                                source="Open Food Facts",
                                image_url=img_url,
                                title=product.get('product_name', f"Product {sku}"),
                                confidence=0.85
                            ))

        except Exception as e:
            self.logger.warning(f"Error in Open Food Facts search: {str(e)}")

        return results[:self.max_images]

    def _search_walmart(self, sku: str) -> List[ImageResult]:
        """Search Walmart for product images"""
        results = []
        try:
            search_url = f"https://www.walmart.com/search?q={sku}"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for product images
                img_containers = soup.find_all('div', {'data-testid': re.compile('item-stack|product-title')})
                for container in img_containers[:5]:
                    img_tags = container.find_all('img')
                    for img in img_tags:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url and 'i5.walmartimages.com' in img_url:
                            # Get higher resolution version
                            if '?' in img_url:
                                img_url = img_url.split('?')[0] + '?odnHeight=768&odnWidth=768'

                            title = img.get('alt', f'Walmart Product {sku}')
                            results.append(ImageResult(
                                sku=sku,
                                source="Walmart",
                                image_url=img_url,
                                title=title,
                                confidence=0.8
                            ))

        except Exception as e:
            self.logger.warning(f"Error in Walmart search: {str(e)}")

        return results[:self.max_images]

    def _search_target(self, sku: str) -> List[ImageResult]:
        """Search Target for product images"""
        results = []
        try:
            search_url = f"https://www.target.com/s?searchTerm={sku}"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for product images
                img_tags = soup.find_all('img', {'src': re.compile('target.scene7.com')})
                for img in img_tags[:5]:
                    img_url = img.get('src')
                    if img_url:
                        title = img.get('alt', f'Target Product {sku}')
                        results.append(ImageResult(
                            sku=sku,
                            source="Target",
                            image_url=img_url,
                            title=title,
                            confidence=0.8
                        ))

        except Exception as e:
            self.logger.warning(f"Error in Target search: {str(e)}")

        return results[:self.max_images]

    def _search_amazon_like(self, sku: str) -> List[ImageResult]:
        """Search barcode lookup marketplace sites"""
        results = []
        try:
            # Try barcode lookup site
            search_url = f"https://www.barcodelookup.com/{sku}"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                img_tags = soup.find_all('img', {'src': True})
                for img in img_tags[:5]:
                    img_url = img.get('src') or img.get('data-src')
                    if img_url and ('product' in img_url.lower() or 'item' in img_url.lower()):
                        title = img.get('alt', f'Marketplace Product {sku}')
                        if not img_url.startswith('http'):
                            img_url = urljoin(search_url, img_url)
                        results.append(ImageResult(
                            sku=sku,
                            source="Amazon Marketplace",
                            image_url=img_url,
                            title=title,
                            confidence=0.7
                        ))

        except Exception as e:
            self.logger.warning(f"Error in marketplace search: {str(e)}")

        return results[:self.max_images]

    def _search_total_wine(self, sku: str) -> List[ImageResult]:
        """Search Total Wine for liquor product images"""
        results = []
        try:
            search_url = f"https://www.totalwine.com/search/all?text={sku}"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for product images
                img_tags = soup.find_all('img', {'src': re.compile('totalwine')})
                for img in img_tags[:5]:
                    img_url = img.get('src')
                    if img_url and 'product' in img_url.lower():
                        title = img.get('alt', f'Total Wine Product {sku}')
                        results.append(ImageResult(
                            sku=sku,
                            source="Total Wine",
                            image_url=img_url,
                            title=title,
                            confidence=0.85
                        ))

        except Exception as e:
            self.logger.warning(f"Error in Total Wine search: {str(e)}")

        return results[:self.max_images]

    def _search_bevmo(self, sku: str) -> List[ImageResult]:
        """Search BevMo for liquor product images"""
        results = []
        try:
            search_url = f"https://www.bevmo.com/search?q={sku}"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                img_tags = soup.find_all('img', {'src': True})
                for img in img_tags[:5]:
                    img_url = img.get('src') or img.get('data-src')
                    if img_url and 'bevmo' in img_url.lower():
                        title = img.get('alt', f'BevMo Product {sku}')
                        if not img_url.startswith('http'):
                            img_url = urljoin(search_url, img_url)
                        results.append(ImageResult(
                            sku=sku,
                            source="BevMo",
                            image_url=img_url,
                            title=title,
                            confidence=0.8
                        ))

        except Exception as e:
            self.logger.warning(f"Error in BevMo search: {str(e)}")

        return results[:self.max_images]

    def _search_google_images(self, sku: str) -> List[ImageResult]:
        """Search Google Images for product images"""
        results = []
        try:
            query = f"{sku} product"
            search_url = f"https://www.google.com/search?q={quote(query)}&tbm=isch&tbs=isz:l"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for image data
                img_tags = soup.find_all('img', {'src': True})
                for img in img_tags[:10]:
                    img_url = img.get('src')
                    if img_url and img_url.startswith('http') and 'gstatic' not in img_url:
                        if 'encrypted-tbn' not in img_url:
                            results.append(ImageResult(
                                sku=sku,
                                source="Google Images",
                                image_url=img_url,
                                title=img.get('alt', f"Product {sku}"),
                                confidence=0.6
                            ))

        except Exception as e:
            self.logger.warning(f"Error in Google Images search: {str(e)}")

        return results[:self.max_images]

    def _search_bing_images(self, sku: str) -> List[ImageResult]:
        """Search Bing Images for product images"""
        results = []
        try:
            query = f"{sku} product"
            search_url = f"https://www.bing.com/images/search?q={quote(query)}&qft=+filterui:imagesize-large"
            headers = {'User-Agent': self.user_agent}

            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for Bing image containers
                containers = soup.find_all('div', {'class': re.compile('imgpt')})
                for container in containers[:10]:
                    m_attr = container.get('m')
                    if m_attr:
                        try:
                            data = json.loads(m_attr)
                            img_url = data.get('murl') or data.get('turl')
                            if img_url:
                                results.append(ImageResult(
                                    sku=sku,
                                    source="Bing Images",
                                    image_url=img_url,
                                    title=data.get('t', f"Product {sku}"),
                                    confidence=0.6
                                ))
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.logger.warning(f"Error in Bing Images search: {str(e)}")

        return results[:self.max_images]

    def _download_image(self, url: str, sku: str, source: str) -> Optional[Path]:
        """Download image with resolution filtering"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            if response.status_code == 200:
                # Check image dimensions before saving
                try:
                    img = Image.open(response.raw)
                    width, height = img.size

                    # Apply minimum resolution filter
                    if width < self.min_width or height < self.min_height:
                        self.logger.debug(f"Image {url} too small: {width}x{height}, minimum: {self.min_width}x{self.min_height}")
                        return None

                except Exception as e:
                    self.logger.debug(f"Could not check image dimensions for {url}: {str(e)}")
                    return None

                # Generate filename
                timestamp = int(time.time())
                source_clean = source.lower().replace(' ', '_')
                filename = f"{sku}-{source_clean}-{timestamp}.jpg"
                file_path = self.output_dir / filename

                # Reset stream and save
                response = self.session.get(url, timeout=30)
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                return file_path

        except Exception as e:
            self.logger.warning(f"Error downloading image from {url}: {str(e)}")

        return None

    def _download_image_relaxed(self, url: str, sku: str, source: str) -> Optional[Path]:
        """Download image with relaxed resolution requirements"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            if response.status_code == 200:
                # Check if it's a valid image but don't enforce resolution
                try:
                    img = Image.open(response.raw)
                    width, height = img.size

                    # Very minimal requirements for fallback
                    if width < 100 or height < 100:
                        return None

                except Exception as e:
                    return None

                # Generate filename
                timestamp = int(time.time())
                source_clean = source.lower().replace(' ', '_')
                filename = f"{sku}-{source_clean}-{timestamp}.jpg"
                file_path = self.output_dir / filename

                # Reset stream and save
                response = self.session.get(url, timeout=30)
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                return file_path

        except Exception as e:
            self.logger.warning(f"Error downloading image (relaxed) from {url}: {str(e)}")

        return None

    def batch_process(self, skus: List[str]) -> Dict[str, List[ImageResult]]:
        """Process multiple SKUs in batch"""
        batch_results = {}
        total_skus = len(skus)

        for i, sku in enumerate(skus, 1):
            self.logger.info(f"Processing SKU {i}/{total_skus}: {sku}")
            try:
                results = self.find_images(sku)
                batch_results[sku] = results

                # Brief pause between requests
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error processing SKU {sku}: {str(e)}")
                batch_results[sku] = []

        return batch_results

    def export_results(self, filename: Optional[str] = None) -> str:
        """Export results to CSV file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"sku_results_{timestamp}.csv"

        export_path = self.output_dir / filename

        with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['sku', 'source', 'image_url', 'title', 'price', 'description', 'local_path', 'confidence']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'sku': result.sku,
                    'source': result.source,
                    'image_url': result.image_url,
                    'title': result.title,
                    'price': result.price or '',
                    'description': result.description or '',
                    'local_path': result.local_path or '',
                    'confidence': result.confidence
                })

        return str(export_path)

    def get_stats(self) -> Dict:
        """Get statistics about the search results"""
        if not self.results:
            return {}

        stats = {
            'total_results': len(self.results),
            'sources': {},
            'skus_processed': len(set(r.sku for r in self.results)),
            'avg_confidence': sum(r.confidence for r in self.results) / len(self.results)
        }

        for result in self.results:
            source = result.source
            if source not in stats['sources']:
                stats['sources'][source] = 0
            stats['sources'][source] += 1

        return stats

    def clear_results(self):
        """Clear stored results"""
        self.results = []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Find product images using SKU numbers"
    )
    parser.add_argument("--sku", type=str, help="Single SKU to search for")
    parser.add_argument("--file", type=str, help="CSV file with SKUs to process")
    parser.add_argument(
        "--output-dir", type=str, default="./images", help="Output directory for images"
    )
    parser.add_argument(
        "--max-images", type=int, default=5, help="Maximum images per SKU"
    )
    parser.add_argument(
        "--batch", action="store_true", help="Process multiple SKUs from file"
    )

    args = parser.parse_args()

    finder = SKUPictureFinder(output_dir=args.output_dir, max_images=args.max_images)

    if args.sku:
        # Single SKU search
        results = finder.find_images(args.sku)
        print(f"Found {len(results)} images for SKU: {args.sku}")

    elif args.file and args.batch:
        # Batch processing from CSV file
        skus = []
        with open(args.file, "r") as f:
            reader = csv.reader(f)
            skus = [row[0] for row in reader if row]

        batch_results = finder.batch_process(skus)
        print(f"Processed {len(skus)} SKUs")

    else:
        print(
            "Please provide either --sku for single search or --file with --batch for batch processing"
        )
        parser.print_help()

    # Export results and show stats
    if finder.results:
        export_file = finder.export_results()
        stats = finder.get_stats()
        print(f"\nResults exported to: {export_file}")
        print(f"Statistics: {json.dumps(stats, indent=2)}")
