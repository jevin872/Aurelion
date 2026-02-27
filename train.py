#!/usr/bin/env python3
"""
Simple training script - trains on small_data automatically
Usage: python train.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.feature_extraction_fast import process_dataset_parallel
from backend.train_model import build_simple_classifier
import time


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          The Polyglot Ghost - Quick Training                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    start_time = time.time()
    
    # Check data
    if not Path('small_data').exists():
        print(" small_data directory not found!")
        return 1
    
    # Extract features
    print("\n Extracting features (fast parallel processing)...")
    dataset = process_dataset_parallel('small_data', 'features.json')
    
    if not dataset:
        print(" Feature extraction failed!")
        return 1
    
    # Train classifier
    print("\n🤖 Building classifier...")
    build_simple_classifier('features.json')
    
    elapsed = time.time() - start_time
    
    print(f"\n Training complete in {elapsed:.2f} seconds!")
    print(f"\n Start dashboard: streamlit run frontend/dashboard.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
