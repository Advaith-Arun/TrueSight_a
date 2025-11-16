"""
Fixed standalone test script for Grad-CAM with real video.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import torch
import logging
from src.app.inference import InferenceEngine
from src.app.video_processor import VideoProcessor
from src.app.config_loader import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_gradcam_with_video(video_path: str):
    """Test Grad-CAM with a real video file."""
    print("=" * 70)
    print("🎥 GRAD-CAM VIDEO TEST")
    print("=" * 70)
    
    video_path = Path(video_path)
    
    # Validate video exists
    if not video_path.exists():
        print(f"❌ Error: Video file not found: {video_path}")
        return False
    
    print(f"\n📹 Video: {video_path.name}")
    print(f"📊 Size: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        # Step 1: Initialize components
        print("\n" + "=" * 70)
        print("STEP 1: Initializing Components")
        print("=" * 70)
        
        config = get_config()
        print(f"✅ Config loaded - Grad-CAM enabled: {config.is_gradcam_enabled()}")
        
        # Initialize video processor
        video_processor = VideoProcessor()
        print("✅ Video processor initialized")
        
        # Initialize inference engine with Grad-CAM
        inference_engine = InferenceEngine(
            model_path='models/checkpoints/best_model.pth',
            device='auto',
            enable_gradcam=True
        )
        print(f"✅ Inference engine initialized (device: {inference_engine.device})")
        
        # Step 2: Preprocess video
        print("\n" + "=" * 70)
        print("STEP 2: Preprocessing Video")
        print("=" * 70)
        
        # process_video returns the tensor directly
        video_tensor = video_processor.process_video(str(video_path))
        
        print(f"✅ Video preprocessed")
        print(f"   - Tensor shape: {video_tensor.shape}")
        print(f"   - Frames extracted: {video_tensor.shape[1]}")
        
        # Step 3: Run inference with Grad-CAM
        print("\n" + "=" * 70)
        print("STEP 3: Running Inference with Grad-CAM")
        print("=" * 70)
        
        inference_result = inference_engine.predict_with_gradcam(
            video_tensor=video_tensor,
            raw_frames=None
        )
        
        print(f"✅ Inference completed")
        print(f"   - Verdict: {inference_result['verdict']}")
        print(f"   - Confidence: {inference_result['confidence']:.2f}%")
        print(f"   - Probability: {inference_result['probability']:.4f}")
        print(f"   - Grad-CAM enabled: {inference_result.get('gradcam_enabled', False)}")
        
        # Step 4: Save Grad-CAM visualizations
        if inference_result.get('gradcam_enabled') and inference_result.get('gradcam'):
            print("\n" + "=" * 70)
            print("STEP 4: Saving Grad-CAM Visualizations")
            print("=" * 70)
            
            gradcam_data = inference_result['gradcam']
            
            # Create output directory
            output_dir = Path('results/gradcam_test') / video_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save overlays
            from PIL import Image
            overlays_dir = output_dir / 'overlays'
            overlays_dir.mkdir(exist_ok=True)
            
            for idx, overlay in enumerate(gradcam_data['overlays']):
                overlay_img = Image.fromarray(overlay)
                overlay_path = overlays_dir / f'frame_{idx:03d}_overlay.jpg'
                overlay_img.save(overlay_path, quality=95)
            
            print(f"✅ Saved {len(gradcam_data['overlays'])} overlay images to:")
            print(f"   {overlays_dir}")
            
            # Save average heatmap
            avg_heatmap = Image.fromarray(gradcam_data['avg_heatmap'])
            avg_path = output_dir / 'average_heatmap.jpg'
            avg_heatmap.save(avg_path, quality=95)
            
            print(f"✅ Saved average heatmap to:")
            print(f"   {avg_path}")
            
            # Summary
            print("\n" + "=" * 70)
            print("📊 GRAD-CAM SUMMARY")
            print("=" * 70)
            print(f"Frames processed: {gradcam_data['num_frames']}")
            print(f"Target class: {gradcam_data['target_class']}")
            print(f"Output directory: {output_dir}")
            print(f"\nGenerated files:")
            print(f"  - {len(gradcam_data['overlays'])} overlay images (overlays/)")
            print(f"  - 1 average heatmap (average_heatmap.jpg)")
            
        else:
            print("\n⚠️  Grad-CAM was not generated")
            if 'gradcam_error' in inference_result:
                print(f"   Error: {inference_result['gradcam_error']}")
        
        # Final success message
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📁 Check the output in: results/gradcam_test/{video_path.stem}/")
        print(f"🎨 View the Grad-CAM heatmaps to see what the model is focusing on!")
        
        # Cleanup
        video_processor.cleanup()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("\n🚀 Starting Grad-CAM Video Test\n")
    
    # Check if video path provided
    if len(sys.argv) < 2:
        print("Usage: python test_gradcam_with_video.py <path_to_video.mp4>")
        print("\nExample:")
        print("  python test_gradcam_with_video.py data/test/fake/fake4.mp4")
        print("\nPlease provide a video file path.")
        return 1
    
    video_path = sys.argv[1]
    
    # Run test
    success = test_gradcam_with_video(video_path)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
