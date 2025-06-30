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
            self.min_width = getattr(config, 'MINIMUM_IMAGE_WIDTH', 300)  # Lowered default
            self.min_height = getattr(config, 'MINIMUM_IMAGE_HEIGHT', 300)  # Lowered default
        self.session = requests.Session()
        self.results = []
        
        # Enable flexible resolution mode if very few results
        self.flexible_resolution = True

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.output_dir / "sku_finder.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # API configurations
        self.ebay_app_id = os.getenv("EBAY_APP_ID")
        self.upc_key = os.getenv("UPC_DATABASE_KEY")

        # Setup session headers
        self.session.headers.update(
            {
                "User-Agent": os.getenv(
                    "USER_AGENT",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                )
            }
        )

    def find_images(self, sku: str) -> List[ImageResult]:
        """Main method to find images for a given SKU"""
        self.logger.info(f"Searching for images for SKU: {sku}")
        results = []

        # Try different search strategies - prioritize liquor-specific sources
        strategies = [
            self._search_liquor_specific,  # Try liquor databases first
            self._search_open_food_facts,
            self._search_upc_database,
            self._search_duckduckgo_images,  # Often better quality images
            self._search_google_images,
            self._search_ebay,
            self._search_shopping_sites
        ]

        for strategy in strategies:
            try:
                strategy_results = strategy(sku)
                if strategy_results:
                    results.extend(strategy_results)
                    self.logger.info(
                        f"Found {len(strategy_results)} results from {strategy.__name__}"
                    )

                # Continue to try more sources (don't break early)
                # This gives us more variety and better chances of high-res images

            except Exception as e:
                self.logger.warning(f"Error in {strategy.__name__}: {str(e)}")
                continue

        # If we have too many results, prioritize by confidence and source quality
        if len(results) > self.max_images:
            # Sort by confidence (higher is better) and prefer certain sources
            source_priority = {
                'Total Wine': 10, 'BevMo': 9, 'Walmart': 8, 'Target': 7,
                'Open Food Facts': 6, 'UPC Database': 5, 'eBay': 4,
                'Barcode Lookup': 3, 'Bing Images': 2, 'Google Images': 1, 'DuckDuckGo Images': 1
            }
            results.sort(key=lambda x: (
                source_priority.get(x.source, 0),
                x.confidence
            ), reverse=True)
            results = results[:self.max_images]

        # Download images
        downloaded_results = []
        for result in results:
            if self._download_image(result):
                downloaded_results.append(result)

        # If no images met resolution requirements, try with relaxed standards
        if not downloaded_results and results:
            self.logger.info("No images met minimum resolution. Trying with relaxed standards...")
            
            # Add a special fallback download method that ignores resolution
            for result in results[:3]:  # Try top 3 results with relaxed standards
                if self._download_image_relaxed(result):
                    downloaded_results.append(result)

        self.results.extend(downloaded_results)
        return downloaded_results

    def _search_open_food_facts(self, sku: str) -> List[ImageResult]:
        """Search Open Food Facts database (free food product database)"""
        results = []

        # Open Food Facts API - completely free
        url = f"https://world.openfoodfacts.org/api/v0/product/{sku}.json"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                if data.get("status") == 1: # Product found
                    product = data.get("product", {})

                    # Get product images
                    images = []
                    if "image_url" in product:
                        images.append(product["image_url"])
                    if "image_front_url" in product:
                        images.append(product["image_front_url"])
                    if "image_nutrition_url" in product:
                        images.append(product["image_nutrition_url"])

                    for img_url in images:
                        if img_url:
                            results.append(
                                ImageResult(
                                    sku=sku,
                                    source="Open Food Facts",
                                    image_url=img_url,
                                    title=product.get("product_name", f"Product {sku}"),
                                    description=product.get("brands", ""),
                                    confidence=0.9,
                                )
                            )

        except Exception as e:
            self.logger.warning(f"Open Food Facts search failed: {str(e)}")

        return results

    def _search_upc_database(self, sku: str) -> List[ImageResult]:
        """Search UPC Database API"""
        results = []

        if not self.upc_key:
            return results

        # UPC Database API
        url = f"https://api.upcitemdb.com/prod/trial/lookup"
        params = {"upc": sku}
        headers = {"Authorization": f"Bearer {self.upc_key}"}

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()

                items = data.get("items", [])
                for item in items:
                    images = item.get("images", [])
                    for img_url in images:
                        results.append(
                            ImageResult(
                                sku=sku,
                                source="UPC Database",
                                image_url=img_url,
                                title=item.get("title", f"Product {sku}"),
                                description=item.get("brand", ""),
                                confidence=0.8,
                            )
                        )

        except Exception as e:
            self.logger.warning(f"UPC Database search failed: {str(e)}")

        return results

    def _search_ebay(self, sku: str) -> List[ImageResult]:
        """Search eBay using Browse API (requires app ID)"""
        results = []

        if not self.ebay_app_id:
            return results

        # eBay Browse API
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {self.ebay_app_id}",
            "X-EBAY-C-ENDUSERCTX": "contextualLocation=country%3DUS,zip%3D95125",
        }
        params = {"q": sku, "limit": 5}

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                items = data.get("itemSummaries", [])
                for item in items:
                    image_url = item.get("image", {}).get("imageUrl")
                    if image_url:
                        results.append(
                            ImageResult(
                                sku=sku,
                                source="eBay",
                                image_url=image_url,
                                title=item.get("title", f"Product {sku}"),
                                price=item.get("price", {}).get("value"),
                                confidence=0.7,
                            )
                        )

        except Exception as e:
            self.logger.warning(f"eBay search failed: {str(e)}")

        return results

    def _search_google_images(self, sku: str) -> List[ImageResult]:
        """Search Google Images via web scraping (use responsibly)"""
        results = []

        search_url = f"https://www.google.com/search?q={quote(sku)}&tbm=isch"

        try:
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")

                # Find image elements with proper attribute checking
                img_elements = soup.find_all("img")[: self.max_images]

                for img in img_elements:
                    try:
                        img_url = img.get("src") or img.get("data-src")
                        if (
                            img_url
                            and isinstance(img_url, str)
                            and img_url.startswith("http")
                        ):
                            alt_text = img.get("alt", f"Product {sku}")
                            results.append(
                                ImageResult(
                                    sku=sku,
                                    source="Google Images",
                                    image_url=img_url,
                                    title=(
                                        alt_text
                                        if isinstance(alt_text, str)
                                        else f"Product {sku}"
                                    ),
                                    confidence=0.6,
                                )
                            )
                    except AttributeError:
                        continue

            time.sleep(1)  # Be respectful with scraping

        except Exception as e:
            self.logger.warning(f"Google Images search failed: {str(e)}")

        return results

    def _search_duckduckgo_images(self, sku: str) -> List[ImageResult]:
        """Search for images using DuckDuckGo (often better quality than Google thumbnails)"""
        try:
            # Get product name first for better search
            product_name = self._get_product_name(sku)
            if product_name and product_name != f"Product {sku}":
                search_query = f"{product_name} {sku} product"
            else:
                search_query = f"{sku} upc barcode product"
            
            url = "https://duckduckgo.com/"
            headers = {"User-Agent": self.session.headers.get("User-Agent")}
            
            # Get initial token
            response = self.session.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Search for images via DuckDuckGo's image search
            search_url = f"https://duckduckgo.com/?q={quote(search_query)}&t=h_&iax=images&ia=images"
            response = self.session.get(search_url, headers=headers)
            
            results = []
            if response.status_code == 200:
                # Parse for image URLs in the page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for image data in script tags or data attributes
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'images' in script.string:
                        # Try to extract image URLs from JavaScript
                        import re
                        image_urls = re.findall(r'https?://[^\s"\']+\.(?:jpg|jpeg|png|gif|webp)', script.string)
                        for img_url in image_urls[:self.max_images]:
                            if 'duckduckgo' not in img_url and len(img_url) > 20:
                                title = product_name if product_name else f"Product {sku}"
                                results.append(ImageResult(
                                    sku=sku,
                                    source="DuckDuckGo Images",
                                    image_url=img_url,
                                    title=title,
                                    confidence=0.7
                                ))
                                if len(results) >= self.max_images:
                                    break
            
            self.logger.info(f"Found {len(results)} results from DuckDuckGo Images")
            return results
            
        except Exception as e:
            self.logger.warning(f"Error searching DuckDuckGo Images: {str(e)}")
            return []

    def _get_product_name(self, sku: str) -> str:
        """Try to get the actual product name from UPC database for better searches"""
        try:
            url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={sku}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items') and len(data['items']) > 0:
                    item = data['items'][0]
                    title = item.get('title', '')
                    brand = item.get('brand', '')
                    if title and brand:
                        return f"{brand} {title}".strip()
                    elif title:
                        return title.strip()
                    elif brand:
                        return brand.strip()
            
        except Exception as e:
            self.logger.debug(f"Could not get product name for {sku}: {str(e)}")
        
        return f"Product {sku}"

    def _search_wine_api(self, sku: str) -> List[ImageResult]:
        """Search Wine API for alcoholic beverages"""
        results = []

        # Try Wine-Searcher API (free tier available)
        try:
            # Search for wine/spirits by UPC or name
            search_terms = [sku, f"upc:{sku}"]

            for term in search_terms:
                url = f"https://api.wine-searcher.com/lwin"
                params = {"query": term, "format": "json"}

                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    wines = data.get("results", [])
                    for wine in wines:
                        image_url = wine.get("image")
                        if image_url:
                            results.append(
                                ImageResult(
                                    sku=sku,
                                    source="Wine API",
                                    image_url=image_url,
                                    title=wine.get("wine", f"Wine {sku}"),
                                    price=wine.get("price_min"),
                                    description=f"{wine.get('producer', '')} {wine.get('region', '')}".strip(),
                                    confidence=0.8,
                                )
                            )

                    if results:
                        break

        except Exception as e:
            self.logger.warning(f"Wine API search failed: {str(e)}")

        return results

    def _search_spirits_database(self, sku: str) -> List[ImageResult]:
        """Search spirits and liquor databases"""
        results = []

        # Search Distiller.com API (if available)
        try:
            url = f"https://distiller.com/api/spirits/search"
            params = {"q": sku, "type": "spirit"}

            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                spirits = data.get("spirits", [])
                for spirit in spirits:
                    image_url = spirit.get("image_url") or spirit.get("bottle_image")
                    if image_url:
                        results.append(
                            ImageResult(
                                sku=sku,
                                source="Spirits Database",
                                image_url=image_url,
                                title=spirit.get("name", f"Spirit {sku}"),
                                description=f"{spirit.get('distillery', '')} {spirit.get('category', '')}".strip(),
                                confidence=0.8,
                            )
                        )

        except Exception as e:
            self.logger.warning(f"Spirits database search failed: {str(e)}")

        return results

    def _search_liquor_specific(self, sku: str) -> List[ImageResult]:
        """Combined liquor-specific search using multiple alcohol databases"""
        results = []

        # Try different liquor search strategies
        strategies = [
            self._search_wine_api,
            self._search_spirits_database,
        ]

        for strategy in strategies:
            try:
                strategy_results = strategy(sku)
                if strategy_results:
                    results.extend(strategy_results)
                    self.logger.info(
                        f"Found {len(strategy_results)} results from {strategy.__name__}"
                    )

                # Don't break - collect from all liquor sources

            except Exception as e:
                self.logger.warning(f"Error in {strategy.__name__}: {str(e)}")
                continue

        return results

    def _download_image(self, result: ImageResult) -> bool:
        """Download an image from URL to local storage"""
        try:
            # Create main images directory
            self.output_dir.mkdir(exist_ok=True)

            # Generate filename with SKU-productname-source-timestamp format
            safe_sku = self._sanitize_filename(result.sku)
            safe_title = self._sanitize_filename(result.title)[
                :30
            ]  # Limit length for filename
            safe_source = self._sanitize_filename(
                result.source.lower().replace(" ", "_")
            )
            extension = self._get_image_extension(result.image_url)

            if safe_title and safe_title != f"Product_{result.sku}":
                filename = f"{safe_sku}-{safe_title}-{safe_source}-{int(time.time())}{extension}"
            else:
                filename = f"{safe_sku}-{safe_source}-{int(time.time())}{extension}"

            filepath = self.output_dir / filename

            # Download image
            response = self.session.get(result.image_url, timeout=30)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)

                # Verify it's a valid image and check minimum resolution
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size
                        # Check minimum resolution using instance variables
                        if width < self.min_width or height < self.min_height:
                            # If flexible resolution is enabled and we have very few results, be more lenient
                            if self.flexible_resolution and min(width, height) >= 150:
                                self.logger.info(f"Accepting smaller image due to flexible mode ({width}x{height}): {filename}")
                            else:
                                os.remove(filepath)
                                self.logger.info(f"Image too small ({width}x{height}), minimum {self.min_width}x{self.min_height}: {result.image_url}")
                                return False
                        img.verify()
                    result.local_path = str(filepath)
                    self.logger.info(f"Downloaded image ({width}x{height}): {filename}")
                    return True
                except Exception as e:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    self.logger.warning(f"Invalid image file or resolution check failed: {result.image_url} - {str(e)}")
                    return False

        except Exception as e:
            self.logger.warning(f"Failed to download image: {str(e)}")
            return False

        return False

    def _download_image_relaxed(self, result: ImageResult) -> bool:
        """Download image with relaxed resolution requirements (fallback method)"""
        try:
            # Create main images directory
            self.output_dir.mkdir(exist_ok=True)

            # Generate filename with SKU-productname-source-timestamp format
            safe_sku = self._sanitize_filename(result.sku)
            safe_title = self._sanitize_filename(result.title)[
                :30
            ]  # Limit length for filename
            safe_source = self._sanitize_filename(
                result.source.lower().replace(" ", "_")
            )
            extension = self._get_image_extension(result.image_url)

            if safe_title and safe_title != f"Product_{result.sku}":
                filename = f"{safe_sku}-{safe_title}-{safe_source}-{int(time.time())}{extension}"
            else:
                filename = f"{safe_sku}-{safe_source}-{int(time.time())}{extension}"

            filepath = self.output_dir / filename

            # Download image
            response = self.session.get(result.image_url, timeout=30)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)

                # Verify it's a valid image (NO resolution check)
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size
                        img.verify()
                    result.local_path = str(filepath)
                    self.logger.info(f"Downloaded image with relaxed standards ({width}x{height}): {filename}")
                    return True
                except Exception as e:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    self.logger.warning(f"Invalid image file: {result.image_url} - {str(e)}")
                    return False

        except Exception as e:
            self.logger.warning(f"Failed to download image: {str(e)}")
            return False

        return False

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        return re.sub(r'[<>:"/\\|?*]', "_", filename)

    def _get_image_extension(self, url: str) -> str:
        """Extract image extension from URL"""
        extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        for ext in extensions:
            if ext in url.lower():
                return ext
        return ".jpg"  # Default

    def batch_process(self, sku_list: List[str]) -> Dict[str, List[ImageResult]]:
        """Process multiple SKUs in batch"""
        results = {}
        total = len(sku_list)

        for i, sku in enumerate(sku_list, 1):
            self.logger.info(f"Processing SKU {i}/{total}: {sku}")
            results[sku] = self.find_images(sku)

            # Add delay between requests to be respectful
            time.sleep(2)

        return results

    def export_results(self, filename: Optional[str] = None) -> str:
        """Export results to CSV file"""
        if not filename:
            filename = str(self.output_dir / f"sku_results_{int(time.time())}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "sku",
                "source",
                "image_url",
                "title",
                "price",
                "description",
                "local_path",
                "confidence",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in self.results:
                writer.writerow(
                    {
                        "sku": result.sku,
                        "source": result.source,
                        "image_url": result.image_url,
                        "title": result.title,
                        "price": result.price,
                        "description": result.description,
                        "local_path": result.local_path,
                        "confidence": result.confidence,
                    }
                )

        self.logger.info(f"Results exported to: {filename}")
        return str(filename)

    def get_stats(self) -> Dict:
        """Get statistics about the search results"""
        if not self.results:
            return {}

        sources = {}
        for result in self.results:
            sources[result.source] = sources.get(result.source, 0) + 1

        return {
            "total_images": len(self.results),
            "sources": sources,
            "skus_processed": len(set(r.sku for r in self.results)),
            "avg_confidence": sum(r.confidence for r in self.results)
            / len(self.results),
        }

    def _search_walmart(self, sku: str) -> List[ImageResult]:
        """Search Walmart for product images using UPC"""
        results = []
        try:
            # Use Walmart's search page
            search_url = f"https://www.walmart.com/search?q={sku}"
            headers = {"User-Agent": config.DEFAULT_USER_AGENT}
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product images
            img_selectors = [
                'img[data-automation-id="product-image"]',
                'img[alt*="product"]',
                'img[src*="i5.walmartimages.com"]',
                '.hover-zoom-in img'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images[:3]:  # Limit to 3 per selector
                    if hasattr(img, 'get'):
                        img_url = img.get('src') or img.get('data-src')
                        if img_url and 'walmartimages.com' in img_url:
                            # Get high-res version
                            if '?odnHeight=' in img_url:
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
            self.logger.warning(f"Walmart search error: {str(e)}")
            
        return results

    def _search_target(self, sku: str) -> List[ImageResult]:
        """Search Target for product images using UPC"""
        results = []
        try:
            # Use Target's search API/page
            search_url = f"https://www.target.com/s?searchTerm={sku}"
            headers = {"User-Agent": config.DEFAULT_USER_AGENT}
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product images
            img_selectors = [
                'img[data-test="product-image"]',
                'picture img',
                'img[src*="target.scene7.com"]'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images[:3]:
                    if hasattr(img, 'get'):
                        img_url = img.get('src') or img.get('data-src')
                        if img_url and ('target.scene7.com' in img_url or 'target.com' in img_url):
                            title = img.get('alt', f'Target Product {sku}')
                            results.append(ImageResult(
                                sku=sku,
                                source="Target",
                                image_url=img_url,
                                title=title,
                                confidence=0.8
                            ))
                            
        except Exception as e:
            self.logger.warning(f"Target search error: {str(e)}")
            
        return results

    def _search_amazon_like(self, sku: str) -> List[ImageResult]:
        """Search Amazon-style marketplaces for product images"""
        results = []
        try:
            # Use a general marketplace search
            search_url = f"https://www.barcodelookup.com/{sku}"
            headers = {"User-Agent": config.DEFAULT_USER_AGENT}
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product images
            images = soup.find_all('img', limit=5)
            for img in images:
                if hasattr(img, 'get'):
                    img_url = img.get('src') or img.get('data-src')
                    if img_url and any(domain in img_url for domain in ['amazon', 'product', 'image']):
                        title = img.get('alt', f'Marketplace Product {sku}')
                        results.append(ImageResult(
                            sku=sku,
                            source="Barcode Lookup",
                            image_url=img_url,
                            title=title,
                            confidence=0.7
                        ))
                        
        except Exception as e:
            self.logger.warning(f"Amazon-like search error: {str(e)}")
            
        return results

    def _search_total_wine(self, sku: str) -> List[ImageResult]:
        """Search Total Wine & More for liquor product images"""
        results = []
        try:
            search_url = f"https://www.totalwine.com/search/all?text={sku}"
            headers = {"User-Agent": config.DEFAULT_USER_AGENT}
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product images
            img_selectors = [
                '.plp-product-image img',
                '.product-image img',
                'img[data-testid="product-image"]'
            ]
            
            for selector in img_selectors:
                images = soup.select(selector)
                for img in images[:3]:
                    if hasattr(img, 'get'):
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            title = img.get('alt', f'Total Wine Product {sku}')
                            results.append(ImageResult(
                                sku=sku,
                                source="Total Wine",
                                image_url=img_url,
                                title=title,
                                confidence=0.9  # High confidence for liquor-specific retailer
                            ))
                            
        except Exception as e:
            self.logger.warning(f"Total Wine search error: {str(e)}")
            
        return results

    def _search_bevmo(self, sku: str) -> List[ImageResult]:
        """Search BevMo for liquor product images"""
        results = []
        try:
            search_url = f"https://www.bevmo.com/search?q={sku}"
            headers = {"User-Agent": config.DEFAULT_USER_AGENT}
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product images
            images = soup.find_all('img', limit=5)
            for img in images:
                if hasattr(img, 'get'):
                    img_url = img.get('src') or img.get('data-src')
                    if img_url and ('bevmo' in img_url or 'product' in img_url):
                        title = img.get('alt', f'BevMo Product {sku}')
                        results.append(ImageResult(
                            sku=sku,
                            source="BevMo",
                            image_url=img_url,
                            title=title,
                            confidence=0.9
                        ))
                        
        except Exception as e:
            self.logger.warning(f"BevMo search error: {str(e)}")
            
        return results

    def _search_bing_images(self, sku: str) -> List[ImageResult]:
        """Search Bing Images for product photos"""
        results = []
        try:
            search_url = f"https://www.bing.com/images/search?q={quote(sku)}"
            headers = {"User-Agent": config.DEFAULT_USER_AGENT}
            
            response = self.session.get(search_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for image results
            img_containers = soup.find_all('a', {'class': re.compile(r'iusc')})
            for container in img_containers[:5]:
                try:
                    # Extract image URL from Bing's data structure
                    m_attr = container.get('m')
                    if m_attr:
                        import json
                        data = json.loads(m_attr)
                        img_url = data.get('murl') or data.get('turl')
                        if img_url:
                            title = data.get('t', f'Bing Product {sku}')
                            results.append(ImageResult(
                                sku=sku,
                                source="Bing Images",
                                image_url=img_url,
                                title=title,
                                confidence=0.6
                            ))
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Bing Images search error: {str(e)}")
            
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Find product images using SKU numbers")
    parser.add_argument("--sku", type=str, help="Single SKU to search for")
    parser.add_argument("--file", type=str, help="CSV file with SKUs for batch processing")
    parser.add_argument("--output-dir", type=str, default="./images", help="Output directory for images")
    parser.add_argument("--max-images", type=int, default=5, help="Maximum images per SKU")
    parser.add_argument("--batch", action="store_true", help="Process multiple SKUs from file")
    
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
































































































            return []            self.logger.warning(f"Error in Google search with query '{query}': {str(e)}")        except Exception as e:                        return results[:self.max_images]                                                    break                                    if len(results) >= self.max_images:                                    ))                                        confidence=0.6                                        title=f"Product {sku}",                                        image_url=url,                                        source="Google Images",                                        sku=sku,                                    results.append(ImageResult(                                if len(url) > 50 and 'gstatic' not in url and 'encrypted-tbn' not in url:                            for url in image_urls:                            image_urls = re.findall(r'https?://[^\s"\']+\.(?:jpg|jpeg|png|gif|webp)', script.string)                            # Look for image URLs in JavaScript                            import re                        if hasattr(script, 'string') and script.string:                    for script in scripts:                    scripts = soup.find_all('script')                    # Fallback: try to extract larger images from page scripts                if len(results) < 2:                                                        ))                                confidence=0.8                                title=img.get('alt', f"Product {sku}"),                                image_url=img_url,                                source="Google Shopping",                                sku=sku,                            results.append(ImageResult(                        if 'encrypted-tbn' not in img_url:                        # Try to get original size images                    if img_url and img_url.startswith('http') and not 'gstatic' in img_url:                    img_url = img.get('src')                for img in img_tags:                img_tags = soup.find_all('img', {'src': True})                # Look for image data in the page                                soup = BeautifulSoup(response.text, 'html.parser')            if response.status_code == 200:                        results = []            response = self.session.get(search_url, headers=headers)                        }                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'            headers = {            search_url = f"https://www.google.com/search?q={quote(query)}&tbm=isch&tbs=isz:l"  # Large images only            # Use a more direct Google Images search        try:        """Search Google Images with a specific query"""    def _search_google_with_query(self, query: str, sku: str) -> List[ImageResult]:        return results[:self.max_images]                        continue                self.logger.debug(f"Error in shopping search with pattern '{pattern}': {str(e)}")            except Exception as e:                                        break                if len(results) >= self.max_images:                                results.extend(google_results)                google_results = self._search_google_with_query(shopping_search, sku)                shopping_search = f"{pattern} site:walmart.com OR site:target.com OR site:amazon.com OR site:kroger.com"                # Search with site restrictions for better quality            try:        for pattern in search_patterns:        # Try each search pattern                    search_patterns.insert(0, f"{product_name}")        if product_name != f"Product {sku}":                ]            f"upc {sku} product",            f"{product_name} {sku}",            f"{sku} product image",        search_patterns = [        # Search patterns for better quality images                product_name = self._get_product_name(sku)        # Get product name for better searches                results = []        """Search major shopping sites for better quality product images"""    def _search_shopping_sites(self, sku: str) -> List[ImageResult]:        return results                        self.logger.warning(f"Bing Images search error: {str(e)}")        except Exception as e:    import argparse

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
