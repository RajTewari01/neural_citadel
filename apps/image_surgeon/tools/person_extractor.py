"""
Person Extraction using Grounded-SAM2 (Transformers Edition)
============================================================
Combines HuggingFace GroundingDINO (for detection) and SAM2 (for segmentation).
Robust Windows implementation avoiding C++ extension issues.
"""

import sys
import torch
import numpy as np
from PIL import Image
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.paths import SAM2_MODELS, SAM2_CONFIGS

def extract_person_grounded(image_path, output_path=None):
    print(f"Extracting person from: {image_path}")
    image_path = Path(image_path)
    
    # Load Image
    image_pil = Image.open(image_path).convert("RGB")
    
    # 1. GroundingDINO Detection (HF Transformers) - OFFLINE MODE
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"  # Force offline mode
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    
    print("Loading GroundingDINO (Transformers, offline)...")
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

    model_id = "IDEA-Research/grounding-dino-tiny"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, torch_dtype=torch.float32, local_files_only=True).to(device)
    
    print("Detecting 'person'...")
    text = "person."  # Text prompt must end with dot usually
    
    inputs = processor(images=image_pil, text=text, return_tensors="pt").to(device)
    # Ensure inputs match model dtype
    inputs["pixel_values"] = inputs["pixel_values"].to(dtype=model.dtype)
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Post-process results
    width, height = image_pil.size
    target_sizes = torch.tensor([[height, width]], device=device)
    results = processor.post_process_grounded_object_detection(
        outputs,
        inputs.input_ids,
        target_sizes=target_sizes
    )[0]
    
    boxes = results["boxes"]  # [N, 4] (x1, y1, x2, y2)
    scores = results["scores"]
    labels = results["labels"]
    
    if len(boxes) == 0:
        print("No person detected!")
        return None
        
    print(f"Found {len(boxes)} person(s) with max score {scores.max().item():.2f}")
    
    # 2. SAM2 Segmentation
    print("Loading SAM2 (Large)...")
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    
    model_path = SAM2_MODELS["large"]
    config_name = SAM2_CONFIGS["large"]
    
    sam_model = build_sam2(config_file=config_name, ckpt_path=str(model_path), device=device)
    predictor = SAM2ImagePredictor(sam_model)
    
    # Set image for predictor
    predictor.set_image(np.array(image_pil))
    
    # Pick best box (highest score)
    best_idx = torch.argmax(scores)
    input_box = boxes[best_idx].cpu().numpy()
    
    print(f"Segmenting main subject box: {input_box}")
    
    masks, scores_sam, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_box[None, :],
        multimask_output=False
    )
    
    # 3. Save Result
    mask = masks[0]
    
    # Ensure mask is boolean (SAM2 outputs float logits/probs sometimes)
    if mask.dtype != bool:
        mask = (mask > 0.0)
    
    # Apply mask
    image_rgba = image_pil.convert("RGBA")
    data = np.array(image_rgba)
    data[~mask, 3] = 0 
    
    result = Image.fromarray(data)
    
    if output_path is None:
        output_path = image_path.parent / (image_path.stem + "_extracted_grounded.png")
        
    result.save(output_path)
    print(f"Saved extracted person: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_person.py <image_path>")
    else:
        extract_person_grounded(sys.argv[1])
