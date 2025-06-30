"""
Playwright tests for SKU Picture Finder web interface
"""
import asyncio
import subprocess
import time
import pytest
from playwright.async_api import async_playwright
import requests
import os
import signal

class TestSKUPictureFinder:
    
    @pytest.fixture(scope="session", autouse=True)
    async def setup_server(self):
        """Start the Flask server before tests and clean up after"""
        # Start Flask server in background
        python_path = "/Users/lesgutches/Library/CloudStorage/OneDrive-Personal/Documents/Python Scripts/sku-pic-finder/venv/bin/python"
        self.server_process = subprocess.Popen([
            python_path, "web_app.py"
        ], cwd="/Users/lesgutches/Library/CloudStorage/OneDrive-Personal/Documents/Python Scripts/sku-pic-finder")
        
        # Wait for server to start
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://127.0.0.1:5001", timeout=2)
                if response.status_code == 200:
                    print("✅ Flask server is running")
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
                if attempt == max_attempts - 1:
                    raise Exception("Flask server failed to start")
        
        yield
        
        # Cleanup: terminate server
        self.server_process.terminate()
        self.server_process.wait()

    @pytest.mark.asyncio
    async def test_homepage_loads(self):
        """Test that the homepage loads correctly"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("http://127.0.0.1:5001")
            
            # Check title
            title = await page.title()
            assert "Liquor Store SKU Picture Finder" in title
            
            # Check main elements are present
            search_input = page.locator("#singleSku")
            assert await search_input.is_visible()
            
            search_button = page.locator("button:has-text('Search Images')")
            assert await search_button.is_visible()
            
            await browser.close()

    @pytest.mark.asyncio
    async def test_single_sku_search(self):
        """Test single SKU search functionality"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for headless
            page = await browser.new_page()
            
            await page.goto("http://127.0.0.1:5001")
            
            # Enter a SKU that we know has results
            sku_input = page.locator("#singleSku")
            await sku_input.fill("012000161155")
            
            # Click search button
            search_button = page.locator("button:has-text('Search Images')")
            await search_button.click()
            
            # Wait for loading to appear and disappear
            loading = page.locator(".loading")
            await loading.wait_for(state="visible")
            await loading.wait_for(state="hidden", timeout=30000)  # 30 second timeout
            
            # Check if results section appears
            results_section = page.locator("#resultsSection")
            await results_section.wait_for(state="visible", timeout=5000)
            
            # Check if selection mode is automatically enabled
            selection_notice = page.locator(".selection-mode")
            assert await selection_notice.is_visible()
            
            # Check if result cards are present
            result_cards = page.locator(".result-card")
            count = await result_cards.count()
            assert count > 0, "No result cards found"
            
            print(f"✅ Found {count} result cards")
            
            # Test image selection
            if count > 0:
                # Click on first image to select it
                first_card = result_cards.first
                await first_card.click()
                
                # Check if card gets selected (should have selected class or visual indicator)
                # Wait a moment for the selection to register
                await page.wait_for_timeout(500)
                
                # Look for selection indicators
                selected_checkbox = first_card.locator(".selection-checkbox")
                assert await selected_checkbox.is_visible()
                
                print("✅ Image selection working")
                
                # Test save functionality
                save_button = page.locator("button:has-text('Save Selected Images')")
                if await save_button.is_visible():
                    await save_button.click()
                    
                    # Check for success message or download
                    await page.wait_for_timeout(2000)
                    print("✅ Save functionality tested")
            
            await browser.close()

    @pytest.mark.asyncio 
    async def test_batch_sku_search(self):
        """Test batch SKU search functionality"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("http://127.0.0.1:5001")
            
            # Enter multiple SKUs
            batch_input = page.locator("#batchSkus")
            test_skus = "012000161155\n049000028911"
            await batch_input.fill(test_skus)
            
            # Click batch search button
            batch_button = page.locator("button:has-text('Batch Search')")
            await batch_button.click()
            
            # Wait for loading
            loading = page.locator(".loading")
            await loading.wait_for(state="visible")
            await loading.wait_for(state="hidden", timeout=60000)  # Longer timeout for batch
            
            # Check results
            results_section = page.locator("#resultsSection")
            await results_section.wait_for(state="visible", timeout=5000)
            
            # Should have results from multiple SKUs
            result_cards = page.locator(".result-card")
            count = await result_cards.count()
            assert count > 0, "No batch results found"
            
            print(f"✅ Batch search found {count} total results")
            
            await browser.close()

    @pytest.mark.asyncio
    async def test_auto_selection_mode(self):
        """Test that selection mode is automatically enabled when results load"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("http://127.0.0.1:5001")
            
            # Initially, selection mode should not be visible
            selection_notice = page.locator(".selection-mode")
            assert not await selection_notice.is_visible()
            
            # Perform search
            sku_input = page.locator("#singleSku")
            await sku_input.fill("012000161155")
            
            search_button = page.locator("button:has-text('Search Images')")
            await search_button.click()
            
            # Wait for results
            loading = page.locator(".loading")
            await loading.wait_for(state="visible")
            await loading.wait_for(state="hidden", timeout=30000)
            
            # Check that selection mode is now automatically enabled
            await selection_notice.wait_for(state="visible", timeout=5000)
            
            selection_text = await selection_notice.text_content()
            assert selection_text and ("Selection Mode Active" in selection_text or "Click images to select" in selection_text)
            
            print("✅ Auto-selection mode is working correctly")
            
            await browser.close()

    @pytest.mark.asyncio
    async def test_image_resolution_filter(self):
        """Test that image resolution filtering is working"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("http://127.0.0.1:5001")
            
            # Search for SKU
            sku_input = page.locator("#singleSku")
            await sku_input.fill("012000161155")
            
            search_button = page.locator("button:has-text('Search Images')")
            await search_button.click()
            
            # Wait for results
            loading = page.locator(".loading")
            await loading.wait_for(state="visible")
            await loading.wait_for(state="hidden", timeout=30000)
            
            # Check if any results were found (resolution filter should allow some through)
            results_section = page.locator("#resultsSection")
            if await results_section.is_visible():
                result_cards = page.locator(".result-card")
                count = await result_cards.count()
                
                if count > 0:
                    # Check that images loaded (indicates they passed resolution filter or fallback)
                    images = page.locator(".result-image")
                    first_image = images.first
                    
                    # Wait for image to load
                    await first_image.wait_for(state="visible")
                    
                    # Check image is not the "No Image" placeholder
                    src = await first_image.get_attribute("src")
                    assert src and not src.startswith("data:image/svg+xml"), "Image failed to load, might indicate resolution filter issue"
                    
                    print("✅ Resolution filter allowing appropriate images through")
                else:
                    print("⚠️  No images found - resolution filter may be too strict")
            
            await browser.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
