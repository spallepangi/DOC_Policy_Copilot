#!/usr/bin/env python3
"""
Manually extract images from Family_Friends_Handbook.pdf page 11.
"""

import os
import sys
import fitz  # PyMuPDF
import base64
import io
from PIL import Image

def extract_page11_images():
    """Extract all images from page 11 of Family_Friends_Handbook.pdf."""
    
    pdf_path = "data/policies/Family_Friends_Handbook.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
        
    try:
        doc = fitz.open(pdf_path)
        page_num = 10  # 0-indexed, so page 11 is index 10
        
        if page_num >= len(doc):
            print(f"❌ Page {page_num + 1} doesn't exist in document")
            doc.close()
            return
            
        page = doc[page_num]
        print(f"📄 Examining page {page_num + 1} of {pdf_path}")
        
        # Get page text
        page_text = page.get_text()
        print(f"📝 Page text ({len(page_text)} chars):")
        print(page_text[:500] + "..." if len(page_text) > 500 else page_text)
        print("-" * 80)
        
        # Get image list
        image_list = page.get_images()
        print(f"🖼️  Found {len(image_list)} images on page {page_num + 1}")
        
        if not image_list:
            print("   No images found on this page")
            
            # Check if there are drawings/vector graphics
            drawings = page.get_drawings()
            print(f"✏️  Found {len(drawings)} drawings/vector graphics")
            
            if drawings:
                print("   This page contains vector graphics that might represent the map")
                for i, drawing in enumerate(drawings):
                    print(f"   Drawing {i+1}: {drawing}")
            
        else:
            for img_index, img in enumerate(image_list):
                print(f"\n📷 Image {img_index + 1}:")
                print(f"   Image info: {img}")
                
                try:
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # CMYK
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                    print(f"   Dimensions: {pix.width} x {pix.height}")
                    print(f"   Color space: {pix.colorspace}")
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    pil_image = Image.open(io.BytesIO(img_data))
                    
                    # Save for inspection
                    output_path = f"page11_image_{img_index + 1}.png"
                    pil_image.save(output_path)
                    print(f"   ✅ Saved as: {output_path}")
                    
                    pix = None
                    
                except Exception as e:
                    print(f"   ❌ Error extracting image {img_index + 1}: {str(e)}")
        
        # Check text for map references
        map_keywords = ["map", "Map", "MAP", "facility", "location", "chart"]
        found_keywords = [kw for kw in map_keywords if kw in page_text]
        if found_keywords:
            print(f"\n🗺️  Found map-related keywords: {found_keywords}")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_page11_images()
