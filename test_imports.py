#!/usr/bin/env python3
"""
Simple test to check if all imports work correctly.
"""

print("Testing imports...")
try:
    import torch
    print("✅ torch imported successfully")
    print(f"   PyTorch version: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"❌ torch import failed: {e}")

try:
    import transformers
    print("✅ transformers imported successfully")
    print(f"   Transformers version: {transformers.__version__}")
except Exception as e:
    print(f"❌ transformers import failed: {e}")

try:
    from transformers import CLIPProcessor, CLIPModel
    print("✅ CLIP components imported successfully")
except Exception as e:
    print(f"❌ CLIP import failed: {e}")

try:
    import faiss
    print("✅ faiss imported successfully")
    print(f"   FAISS version: {faiss.__version__}")
except Exception as e:
    print(f"❌ faiss import failed: {e}")

try:
    import numpy as np
    print("✅ numpy imported successfully")
    print(f"   NumPy version: {np.__version__}")
except Exception as e:
    print(f"❌ numpy import failed: {e}")

print("\n🧪 Testing CLIP model loading...")
try:
    model_name = "openai/clip-vit-base-patch32"
    print(f"Loading {model_name}...")
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    print("✅ CLIP model loaded successfully")
    
    # Test a simple embedding
    with torch.no_grad():
        inputs = processor(text=["test"], return_tensors="pt")
        features = model.get_text_features(**inputs)
        print(f"✅ Generated test embedding with shape: {features.shape}")
        
except Exception as e:
    print(f"❌ CLIP model loading failed: {e}")

print("\n✅ All import tests completed!")
