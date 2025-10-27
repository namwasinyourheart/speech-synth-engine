#!/usr/bin/env python3
# ============================================================
# Generate Address Audio with MiniMax Selenium
# Example script for generating Vietnamese address audio using MiniMax voice cloning
# ============================================================

import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

# Add speech-synth-engine to path
sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

def setup_logging(log_file: str = "logs/minimax_address_generation.log"):
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_addresses(file_path: Path) -> List[str]:
    """Load addresses from text file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def generate_addresses(
    addresses: List[str],
    reference_audio: Path,
    output_dir: Path,
    provider_config: Dict[str, Any],
    batch_size: int = 5,
    delay: float = 5.0
) -> Dict[str, Any]:
    """
    Generate audio for addresses using MiniMax voice cloning
    
    Args:
        addresses: List of address strings
        reference_audio: Path to reference audio for voice cloning
        output_dir: Directory to save generated audio files
        provider_config: Configuration for MiniMax provider
        batch_size: Number of addresses to process in each batch
        delay: Delay between API calls in seconds
    """
    logger = logging.getLogger("MiniMaxAddressGenerator")
    
    # Initialize provider
    provider = MiniMaxSeleniumProvider("minimax", provider_config)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'total': len(addresses),
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        for i, address in enumerate(addresses, 1):
            # Skip if already processed
            output_file = output_dir / f"address_{i:04d}.wav"
            if output_file.exists():
                logger.info(f"Skipping existing file: {output_file}")
                results['success'] += 1
                continue
                
            logger.info(f"Processing {i}/{len(addresses)}: {address}")
            
            try:
                # Generate audio with metadata
                result = provider.clone_with_metadata(
                    text=address,
                    reference_audio=reference_audio,
                    output_file=output_file
                )
                
                if result.get('success'):
                    results['success'] += 1
                    logger.info(f"✅ Success: {output_file}")
                else:
                    results['failed'] += 1
                    error_msg = result.get('error', 'Unknown error')
                    results['errors'].append({
                        'address': address,
                        'error': error_msg
                    })
                    logger.error(f"❌ Failed: {error_msg}")
                
                # Add delay between requests
                if i < len(addresses):
                    time.sleep(delay)
                    
            except Exception as e:
                results['failed'] += 1
                error_msg = str(e)
                results['errors'].append({
                    'address': address,
                    'error': error_msg
                })
                logger.error(f"❌ Error processing {address}: {error_msg}")
                
    except KeyboardInterrupt:
        logger.warning("\nGeneration interrupted by user")
    
    return results

def main():
    # Configuration
    config = {
        'google_email': 'your_email@gmail.com',  # Replace with your email
        'google_password': 'your_password',      # Replace with your password
        'headless': False,                      # Set to True for headless mode
        'max_wait_time': 300,                   # 5 minutes max wait time
        'language': 'Vietnamese'
    }
    
    # File paths
    script_dir = Path(__file__).parent
    addresses_file = script_dir / "data/addresses.txt"
    reference_audio = script_dir / "data/reference_voice.wav"
    output_dir = script_dir / "output/minimax_addresses"
    log_file = script_dir / "logs/minimax_address_generation.log"

    addresses_file = 

    
    # Setup logging
    log_file.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(str(log_file))
    
    logger = logging.getLogger("MiniMaxAddressGenerator")
    
    try:
        # Load addresses
        logger.info(f"Loading addresses from: {addresses_file}")
        addresses = load_addresses(addresses_file)
        
        if not addresses:
            logger.error("No addresses found in the input file")
            return
            
        logger.info(f"Found {len(addresses)} addresses to process")
        
        # Generate audio
        start_time = time.time()
        results = generate_addresses(
            addresses=addresses,
            reference_audio=reference_audio,
            output_dir=output_dir,
            provider_config=config,
            batch_size=5,
            delay=5.0
        )
        
        # Print summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 50)
        logger.info("🎉 Generation Complete!")
        logger.info(f"✅ Success: {results['success']}/{results['total']}")
        logger.info(f"❌ Failed: {results['failed']}/{results['total']}")
        logger.info(f"⏱️  Elapsed time: {elapsed/60:.1f} minutes")
        
        if results['errors']:
            logger.warning("\nErrors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                logger.warning(f"- {error['address']}: {error['error']}")
            if len(results['errors']) > 5:
                logger.warning(f"... and {len(results['errors']) - 5} more errors")
        
    except Exception as e:
        logger.exception("An error occurred during generation")
        raise

if __name__ == "__main__":
    main()
