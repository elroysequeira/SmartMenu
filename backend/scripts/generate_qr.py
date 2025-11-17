"""Generate QR codes for restaurant tables."""
import argparse
import qrcode
from pathlib import Path

# Base URL for QR codes
BASE_URL = "https://localhost:3000"


def generate_qr_codes(restaurant_slug: str, num_tables: int, output_dir: Path = None):
    """
    Generate QR codes for restaurant tables.
    
    Args:
        restaurant_slug: Restaurant slug identifier
        num_tables: Number of tables to generate QR codes for
        output_dir: Output directory (defaults to scripts directory)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent
    
    # Create QR code for each table
    for table_num in range(1, num_tables + 1):
        # Generate URL
        url = f"{BASE_URL}/r/{restaurant_slug}/t/{table_num}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save image
        filename = output_dir / f"qr_{restaurant_slug}_table_{table_num}.png"
        img.save(filename)
        print(f"Generated: {filename} -> {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QR codes for restaurant tables")
    parser.add_argument(
        "--restaurant-slug",
        required=True,
        help="Restaurant slug (e.g., 'sunset-bistro')"
    )
    parser.add_argument(
        "--tables",
        type=int,
        required=True,
        help="Number of tables to generate QR codes for"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for QR code images (defaults to scripts directory)"
    )
    
    args = parser.parse_args()
    
    generate_qr_codes(args.restaurant_slug, args.tables, args.output_dir)
    print(f"\nGenerated {args.tables} QR code(s) for {args.restaurant_slug}")

