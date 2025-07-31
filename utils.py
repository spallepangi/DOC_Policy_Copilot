import fitz  # PyMuPDF
import os
import base64
import io
from typing import List, Dict, Any
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PIL import Image

# Try to import config, use defaults if not available
try:
    import config
except ImportError:
    # Fallback configuration if config module is not available
    class config:
        CHUNK_SIZE = 500
        CHUNK_OVERLAP = 20


def load_pdf_files(folder_path: str) -> List[Dict[str, Any]]:
    """
    Load all PDF files from the specified folder and extract text.
    
    Args:
        folder_path (str): Path to the folder containing PDF files
        
    Returns:
        List[Dict]: List of documents with text content and metadata
    """
    documents = []
    
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return documents
    
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # Only add pages with content
                    documents.append({
                        'text': text,
                        'filename': pdf_file,
                        'page_number': page_num + 1,
                        'source': f"{pdf_file} (Page {page_num + 1})"
                    })
            
            doc.close()
            print(f"Loaded {len(doc)} pages from {pdf_file}")
            
        except Exception as e:
            print(f"Error loading {pdf_file}: {str(e)}")
    
    return documents


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into chunks using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        text (str): Text to be chunked
        chunk_size (int): Approximate number of characters per chunk (defaults to config)
        overlap (int): Number of characters to overlap between chunks (defaults to config)
        
    Returns:
        List[str]: List of text chunks
    """
    # Use config defaults if not provided
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE * 4  # Approximate chars per token
    if overlap is None:
        overlap = config.CHUNK_OVERLAP * 4  # Approximate chars per token
    
    # Initialize the text splitter with semantic separators
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=[
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            "! ",    # Exclamatory sentences
            "? ",    # Questions
            "; ",    # Semicolons
            ", ",    # Commas
            " ",     # Words
            "",      # Characters
        ]
    )
    
    chunks = text_splitter.split_text(text)
    return chunks


def chunk_documents(documents: List[Dict[str, Any]], chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
    """
    Chunk all documents into smaller pieces while preserving metadata using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        documents (List[Dict]): List of documents with text and metadata
        chunk_size (int): Approximate number of tokens per chunk (defaults to config)
        overlap (int): Number of tokens to overlap between chunks (defaults to config)
        
    Returns:
        List[Dict]: List of chunked documents with metadata
    """
    # Use config defaults if not provided
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE
    if overlap is None:
        overlap = config.CHUNK_OVERLAP
    
    chunked_docs = []
    
    for doc in documents:
        # Convert token-based sizes to character-based for the text splitter
        char_chunk_size = chunk_size * 4  # Approximate chars per token
        char_overlap = overlap * 4  # Approximate chars per token
        
        text_chunks = chunk_text(doc['text'], char_chunk_size, char_overlap)
        
        for i, chunk in enumerate(text_chunks):
            chunked_doc = {
                'text': chunk,
                'filename': doc['filename'],
                'page_number': doc['page_number'],
                'source': doc['source'],
                'chunk_id': f"{doc['filename']}_page{doc['page_number']}_chunk{i+1}"
            }
            chunked_docs.append(chunked_doc)
    
    return chunked_docs


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_images_from_pdf(folder_path: str) -> List[Dict[str, Any]]:
    """
    Extract images from all PDF files in the specified folder.
    
    Args:
        folder_path (str): Path to the folder containing PDF files
        
    Returns:
        List[Dict]: List of image documents with base64 data and metadata
    """
    image_documents = []
    
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return image_documents
    
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Skip images that are too small (likely artifacts)
                        if pix.width < 50 or pix.height < 50:
                            pix = None
                            continue
                        
                        # Convert to RGB if CMYK
                        if pix.n - pix.alpha < 4:  # CMYK: n == 5, Alpha: 0 or 1
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Resize if too large (optional optimization)
                        max_size = (1024, 1024)
                        if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Convert to base64
                        img_buffer = io.BytesIO()
                        pil_image.save(img_buffer, format='PNG')
                        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                        
                        # Generate caption based on context
                        page_text = page.get_text()
                        caption = generate_image_caption(page_text, img_index)
                        
                        image_documents.append({
                            'type': 'image',
                            'base64_data': img_base64,
                            'filename': pdf_file,
                            'page_number': page_num + 1,
                            'image_index': img_index + 1,
                            'source': f"{pdf_file} (Page {page_num + 1}, Image {img_index + 1})",
                            'caption': caption,
                            'dimensions': pil_image.size,
                            'chunk_id': f"{pdf_file}_page{page_num + 1}_img{img_index + 1}"
                        })
                        
                        pix = None  # Clean up
                        
                    except Exception as e:
                        print(f"Error extracting image {img_index} from {pdf_file} page {page_num + 1}: {str(e)}")
                        continue
            
            doc.close()
            print(f"Extracted images from {pdf_file}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
    
    return image_documents


def generate_image_caption(page_text: str, img_index: int) -> str:
    """
    Generate a caption for an image based on surrounding text context.
    
    Args:
        page_text (str): Text content from the page containing the image
        img_index (int): Index of the image on the page
        
    Returns:
        str: Generated caption
    """
    # Check for specific map indicators first
    if "Map of Missouri Correctional Facilities" in page_text:
        return "Map of Missouri Correctional Facilities showing locations of DOC institutions including ACC, JCCC, BCC, CCC, CTCC, FRDC, CRCC, ERDCC, FCC, KCRC, MTC, MECC, MCC, NECC, OCC, PCC, SCCC, SECC, TCC, WMCC, WRDCC, WERDCC"
    
    # Check for organizational chart indicators
    if "Organizational chart" in page_text or "organizational chart" in page_text:
        return "Missouri Department of Corrections organizational chart showing departmental structure and hierarchy"
    
    # Look for facility codes that suggest a map
    facility_codes = ['ACC', 'JCCC', 'BCC', 'CCC', 'CTCC', 'FRDC', 'CRCC', 'ERDCC', 'FCC', 'KCRC', 'MTC', 'MECC', 'MCC', 'NECC', 'OCC', 'PCC', 'SCCC', 'SECC', 'TCC', 'WMCC', 'WRDCC', 'WERDCC']
    found_codes = [code for code in facility_codes if code in page_text]
    if len(found_codes) >= 10:  # If many facility codes are present, likely a map
        return f"Map or diagram showing Missouri correctional facilities including {', '.join(found_codes[:10])}{'...' if len(found_codes) > 10 else ''}"
    
    # Simple heuristic: look for common caption patterns
    caption_patterns = [
        r'Figure\s+\d+[:\.]?\s*([^\n]+)',
        r'Image\s+\d+[:\.]?\s*([^\n]+)',
        r'Chart\s+\d+[:\.]?\s*([^\n]+)',
        r'Diagram\s+\d+[:\.]?\s*([^\n]+)',
        r'Table\s+\d+[:\.]?\s*([^\n]+)',
        r'Map\s+of\s+([^\n]+)',
        r'([^\n]*Map[^\n]*)',
    ]
    
    for pattern in caption_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches and len(matches) > img_index:
            return matches[img_index].strip()
    
    # Fallback: use first sentence or meaningful text snippet
    sentences = re.split(r'[.!?]', page_text)
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if meaningful_sentences:
        return meaningful_sentences[0][:100] + ("..." if len(meaningful_sentences[0]) > 100 else "")
    
    return f"Image from policy document"


def image_to_base64(image_path: str) -> str:
    """
    Convert an image file to base64 string.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded image string
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
        return ""
