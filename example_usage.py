#!/usr/bin/env python3
"""
Simple example usage of the SKU Picture Finder
"""

from sku_finder import SKUPictureFinder
import json


def main():
    # Initialize the finder
    finder = SKUPictureFinder(output_dir="./example_images", max_images=3)

    # Example SKUs to test (these are common UPC codes that might have results)
    test_skus = [
        "049000028911",  # Coca-Cola (example UPC)
        "012000161155",  # Pepsi (example UPC)
        "037000127130",  # Procter & Gamble product (example)
        "885909950805",  # Example electronics UPC
        "123456789012",  # Fake SKU for testing
    ]

    print("🔍 SKU Picture Finder - Example Usage")
    print("=" * 50)

    # Test single SKU search
    print("\n1. Testing single SKU search...")
    for sku in test_skus[:2]:  # Test first 2 SKUs
        print(f"\nSearching for SKU: {sku}")
        results = finder.find_images(sku)

        if results:
            print(f"✅ Found {len(results)} images:")
            for i, result in enumerate(results, 1):
                print(
                    f"  {i}. {result.title} ({result.source}) - Confidence: {result.confidence:.1%}"
                )
        else:
            print("❌ No images found")

    # Test batch processing
    print(f"\n2. Testing batch processing with {len(test_skus)} SKUs...")
    batch_results = finder.batch_process(test_skus)

    total_found = sum(len(results) for results in batch_results.values())
    print(f"✅ Batch processing complete! Found {total_found} total images")

    # Show statistics
    print("\n3. Statistics:")
    stats = finder.get_stats()
    if stats:
        print(json.dumps(stats, indent=2))
    else:
        print("No statistics available")

    # Export results
    print("\n4. Exporting results...")
    export_file = finder.export_results()
    print(f"✅ Results exported to: {export_file}")

    print(
        f"\n🎉 Example complete! Check the '{finder.output_dir}' directory for downloaded images."
    )


if __name__ == "__main__":
    main()
