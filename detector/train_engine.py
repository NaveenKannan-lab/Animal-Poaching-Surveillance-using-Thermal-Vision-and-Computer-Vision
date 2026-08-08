"""
Thermal YOLO Training Engine
Train YOLOv8 on thermal/infrared datasets for better detection in thermal footage.

Datasets supported:
1. FLIR ADAS Dataset (thermal pedestrians, vehicles)
2. Custom thermal wildlife dataset
3. Any YOLO-format thermal dataset

Usage:
    python train_engine.py --dataset flir --epochs 50
    python train_engine.py --dataset custom --data path/to/data.yaml --epochs 100
"""

import os
import sys
import argparse
import shutil
import zipfile
import urllib.request
from pathlib import Path

# Check if ultralytics is installed
try:
    from ultralytics import YOLO
except ImportError:
    print("Installing ultralytics...")
    os.system("pip install ultralytics")
    from ultralytics import YOLO


class ThermalTrainer:
    def __init__(self, base_dir="thermal_dataset"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def download_flir_dataset(self):
        """
        Download FLIR ADAS thermal dataset.
        Note: FLIR requires registration. This provides instructions.
        """
        print("\n" + "="*60)
        print("FLIR ADAS THERMAL DATASET SETUP")
        print("="*60)
        print("""
To download the FLIR ADAS Dataset:

1. Go to: https://www.flir.com/oem/adas/adas-dataset-form/
2. Fill in the registration form
3. Download the dataset (FLIR_ADAS_v2.zip)
4. Extract to: {}/flir_adas/

Dataset structure should be:
{}/flir_adas/
├── images_thermal_train/
├── images_thermal_val/
├── video_thermal_test/
└── ...

After downloading, run:
    python train_engine.py --dataset flir --convert
        """.format(self.base_dir, self.base_dir))
        
        return False
    
    def download_sample_thermal_dataset(self):
        """
        Download a smaller open thermal dataset for testing.
        Using LLVIP dataset subset (thermal pedestrians).
        """
        print("\n[*] Setting up sample thermal dataset...")
        
        dataset_dir = self.base_dir / "thermal_sample"
        dataset_dir.mkdir(exist_ok=True)
        
        # Create directory structure for YOLO
        for split in ['train', 'val']:
            (dataset_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (dataset_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
        print("""
[!] To use the sample thermal dataset:

1. Download thermal images from one of these sources:
   - LLVIP: https://github.com/bupt-ai-cz/LLVIP
   - KAIST: https://soonminhwang.github.io/rgbt-ped-detection/
   - SCUT: https://github.com/SCUT-CV/SCUT_FIR_Pedestrian_Dataset
   
2. Place thermal images in:
   - {}/images/train/  (80% of images)
   - {}/images/val/    (20% of images)
   
3. Create YOLO format labels (.txt files) in:
   - {}/labels/train/
   - {}/labels/val/

YOLO Label Format (one line per object):
<class_id> <x_center> <y_center> <width> <height>
- All values normalized (0-1)
- class_id: 0=person, 1=animal (or your custom classes)

Example label file content:
0 0.5 0.5 0.3 0.6
1 0.2 0.4 0.15 0.2
        """.format(
            dataset_dir / 'images' / 'train',
            dataset_dir / 'images' / 'val',
            dataset_dir / 'labels' / 'train',
            dataset_dir / 'labels' / 'val'
        ))
        
        # Create data.yaml for training
        data_yaml = dataset_dir / "data.yaml"
        yaml_content = f"""# Thermal Dataset Configuration
path: {dataset_dir.absolute()}
train: images/train
val: images/val

# Classes
names:
  0: person
  1: animal
  2: dog
  3: cat
  4: deer
  5: elephant
  6: horse
  7: cow

# Number of classes
nc: 8
"""
        data_yaml.write_text(yaml_content)
        print(f"\n[+] Created config: {data_yaml}")
        
        return str(data_yaml)
    
    def convert_flir_to_yolo(self, flir_path):
        """
        Convert FLIR ADAS annotations to YOLO format.
        FLIR uses JSON annotations, we convert to YOLO txt format.
        """
        import json
        
        flir_path = Path(flir_path)
        output_dir = self.base_dir / "flir_yolo"
        output_dir.mkdir(exist_ok=True)
        
        # FLIR class mapping (adjust based on your needs)
        flir_classes = {
            1: 0,   # person -> 0
            2: 1,   # bicycle -> 1 (or skip)
            3: 2,   # car -> 2 (or skip)
            17: 3,  # dog -> 3
            18: 4,  # cat -> 4
        }
        
        for split in ['train', 'val']:
            images_dir = flir_path / f"images_thermal_{split}"
            annot_file = flir_path / f"thermal_{split}.json"
            
            if not annot_file.exists():
                print(f"[!] Annotation file not found: {annot_file}")
                continue
                
            out_images = output_dir / 'images' / split
            out_labels = output_dir / 'labels' / split
            out_images.mkdir(parents=True, exist_ok=True)
            out_labels.mkdir(parents=True, exist_ok=True)
            
            # Load COCO-format annotations
            with open(annot_file, 'r') as f:
                data = json.load(f)
            
            # Build image id to filename mapping
            img_map = {img['id']: img for img in data['images']}
            
            # Group annotations by image
            img_annotations = {}
            for ann in data['annotations']:
                img_id = ann['image_id']
                if img_id not in img_annotations:
                    img_annotations[img_id] = []
                img_annotations[img_id].append(ann)
            
            # Convert each image
            converted = 0
            for img_id, img_info in img_map.items():
                img_name = img_info['file_name']
                img_w = img_info['width']
                img_h = img_info['height']
                
                # Copy image
                src_img = images_dir / img_name
                if src_img.exists():
                    shutil.copy(src_img, out_images / img_name)
                
                # Convert annotations to YOLO format
                label_file = out_labels / (Path(img_name).stem + '.txt')
                labels = []
                
                for ann in img_annotations.get(img_id, []):
                    cat_id = ann['category_id']
                    if cat_id not in flir_classes:
                        continue
                    
                    yolo_class = flir_classes[cat_id]
                    
                    # COCO bbox: [x, y, width, height] (top-left corner)
                    x, y, w, h = ann['bbox']
                    
                    # Convert to YOLO: center x, center y, width, height (normalized)
                    x_center = (x + w/2) / img_w
                    y_center = (y + h/2) / img_h
                    w_norm = w / img_w
                    h_norm = h / img_h
                    
                    labels.append(f"{yolo_class} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
                
                if labels:
                    label_file.write_text('\n'.join(labels))
                    converted += 1
            
            print(f"[+] Converted {converted} images for {split} split")
        
        # Create data.yaml
        data_yaml = output_dir / "data.yaml"
        yaml_content = f"""# FLIR Thermal Dataset (YOLO format)
path: {output_dir.absolute()}
train: images/train
val: images/val

# Classes (modify based on your needs)
names:
  0: person
  1: bicycle
  2: car
  3: dog
  4: cat

nc: 5
"""
        data_yaml.write_text(yaml_content)
        print(f"\n[+] Created config: {data_yaml}")
        
        return str(data_yaml)
    
    def create_custom_dataset_template(self):
        """
        Create a template structure for custom thermal wildlife dataset.
        """
        print("\n" + "="*60)
        print("CUSTOM THERMAL WILDLIFE DATASET TEMPLATE")
        print("="*60)
        
        dataset_dir = self.base_dir / "wildlife_thermal"
        
        # Create directory structure
        for split in ['train', 'val', 'test']:
            (dataset_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (dataset_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
        # Create data.yaml
        data_yaml = dataset_dir / "data.yaml"
        yaml_content = f"""# Custom Thermal Wildlife Dataset
# Optimized for anti-poaching detection

path: {dataset_dir.absolute()}
train: images/train
val: images/val
test: images/test

# Wildlife + Human classes for poaching detection
names:
  0: human
  1: elephant
  2: rhino
  3: lion
  4: leopard
  5: buffalo
  6: deer
  7: zebra
  8: giraffe
  9: dog
  10: unknown_animal

nc: 11
"""
        data_yaml.write_text(yaml_content)
        
        # Create README
        readme = dataset_dir / "README.txt"
        readme_content = """
THERMAL WILDLIFE DATASET SETUP
==============================

1. COLLECT THERMAL IMAGES:
   - Use FLIR camera or thermal drone footage
   - Capture at night for authentic conditions
   - Include various animals and human activities
   
2. ANNOTATE IMAGES:
   Use one of these tools:
   - LabelImg: pip install labelImg
   - CVAT: https://cvat.ai
   - Label Studio: https://labelstud.io
   
   Export in YOLO format (txt files)

3. ORGANIZE FILES:
   images/train/  -> 70% of images (jpg/png)
   images/val/    -> 20% of images
   images/test/   -> 10% of images
   
   labels/train/  -> Matching .txt label files
   labels/val/    -> Matching .txt label files
   labels/test/   -> Matching .txt label files

4. LABEL FORMAT (YOLO):
   Each .txt file has one line per object:
   <class_id> <x_center> <y_center> <width> <height>
   
   Example (0=human, 1=elephant):
   0 0.5 0.5 0.3 0.6
   1 0.2 0.4 0.15 0.2

5. TRAIN:
   python train_engine.py --dataset custom --data wildlife_thermal/data.yaml --epochs 100

TIPS FOR THERMAL DATA:
- Keep images in original thermal colormap
- Don't convert to grayscale
- Maintain consistent resolution
- Include various weather conditions
"""
        readme.write_text(readme_content)
        
        print(f"""
[+] Created dataset template at: {dataset_dir}

Directory structure:
{dataset_dir}/
├── images/
│   ├── train/   <- Place 70% of thermal images here
│   ├── val/     <- Place 20% of thermal images here
│   └── test/    <- Place 10% of thermal images here
├── labels/
│   ├── train/   <- YOLO format .txt labels
│   ├── val/
│   └── test/
├── data.yaml    <- Dataset configuration
└── README.txt   <- Setup instructions

Next steps:
1. Add your thermal images to images/train and images/val
2. Create YOLO labels using LabelImg or CVAT
3. Run: python train_engine.py --dataset custom --data {data_yaml} --epochs 100
        """)
        
        return str(data_yaml)
    
    def train(self, data_yaml, epochs=100, imgsz=640, batch=16, model_base='yolov8m.pt', 
              device='', project='runs/thermal', name='train'):
        """
        Train YOLOv8 on thermal dataset.
        
        Args:
            data_yaml: Path to data.yaml configuration
            epochs: Number of training epochs
            imgsz: Image size for training
            batch: Batch size (-1 for auto)
            model_base: Base model to fine-tune from
            device: Device to train on ('' for auto, '0' for GPU 0, 'cpu' for CPU)
            project: Project directory for results
            name: Name of the training run
        """
        print("\n" + "="*60)
        print("THERMAL YOLO TRAINING")
        print("="*60)
        
        # Verify data.yaml exists
        if not Path(data_yaml).exists():
            print(f"[!] Error: {data_yaml} not found!")
            return None
        
        print(f"""
Configuration:
- Dataset config: {data_yaml}
- Base model: {model_base}
- Epochs: {epochs}
- Image size: {imgsz}
- Batch size: {batch}
- Device: {device or 'auto'}
- Output: {project}/{name}
        """)
        
        # Load base model
        print(f"\n[*] Loading base model: {model_base}")
        model = YOLO(model_base)
        
        # Train
        print(f"\n[*] Starting training for {epochs} epochs...")
        print("-" * 60)
        
        try:
            results = model.train(
                data=data_yaml,
                epochs=epochs,
                imgsz=imgsz,
                batch=batch,
                device=device,
                project=project,
                name=name,
                patience=20,          # Early stopping patience
                save=True,            # Save checkpoints
                save_period=10,       # Save every 10 epochs
                cache=True,           # Cache images for faster training
                amp=True,             # Automatic mixed precision
                verbose=True,
                plots=True,           # Generate training plots
                
                # Data augmentation for thermal
                hsv_h=0.015,          # Hue augmentation
                hsv_s=0.7,            # Saturation augmentation  
                hsv_v=0.4,            # Value augmentation
                degrees=10,           # Rotation
                translate=0.1,        # Translation
                scale=0.5,            # Scale
                flipud=0.5,           # Vertical flip (thermal can be upside down)
                fliplr=0.5,           # Horizontal flip
                mosaic=1.0,           # Mosaic augmentation
                mixup=0.1,            # Mixup augmentation
            )
            
            print("\n" + "="*60)
            print("TRAINING COMPLETE!")
            print("="*60)
            
            # Get best model path
            best_model = Path(project) / name / 'weights' / 'best.pt'
            last_model = Path(project) / name / 'weights' / 'last.pt'
            
            print(f"""
Results saved to: {project}/{name}

Model weights:
- Best: {best_model}
- Last: {last_model}

To use the trained model:
1. Copy best.pt to models/ folder:
   copy "{best_model}" "models/thermal_yolo.pt"

2. Update app.py to use the new model:
   Change 'yolov8m.pt' to 'thermal_yolo.pt'
   
Or use the Settings page in the web UI to switch models.
            """)
            
            return str(best_model)
            
        except Exception as e:
            print(f"\n[!] Training error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate(self, model_path, data_yaml):
        """Validate a trained model on the test set."""
        print(f"\n[*] Validating model: {model_path}")
        
        model = YOLO(model_path)
        results = model.val(data=data_yaml, split='test')
        
        print(f"""
Validation Results:
- mAP50: {results.box.map50:.4f}
- mAP50-95: {results.box.map:.4f}
- Precision: {results.box.mp:.4f}
- Recall: {results.box.mr:.4f}
        """)
        
        return results
    
    def export_model(self, model_path, format='onnx'):
        """Export trained model to different formats."""
        print(f"\n[*] Exporting model to {format}...")
        
        model = YOLO(model_path)
        model.export(format=format)
        
        print(f"[+] Model exported successfully!")


def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 on thermal datasets')
    
    parser.add_argument('--dataset', type=str, default='setup',
                        choices=['flir', 'custom', 'setup'],
                        help='Dataset to use (default: setup)')
    
    parser.add_argument('--data', type=str, default=None,
                        help='Path to data.yaml for custom dataset')
    
    parser.add_argument('--convert', action='store_true',
                        help='Convert FLIR dataset to YOLO format')
    
    parser.add_argument('--flir-path', type=str, default='thermal_dataset/flir_adas',
                        help='Path to FLIR ADAS dataset')
    
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs (default: 100)')
    
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size (default: 16, use -1 for auto)')
    
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Image size (default: 640)')
    
    parser.add_argument('--model', type=str, default='yolov8m.pt',
                        help='Base model to fine-tune (default: yolov8m.pt)')
    
    parser.add_argument('--device', type=str, default='',
                        help='Device: "" for auto, "0" for GPU 0, "cpu" for CPU')
    
    parser.add_argument('--validate', type=str, default=None,
                        help='Path to model to validate')
    
    args = parser.parse_args()
    
    trainer = ThermalTrainer()
    
    # Handle different modes
    if args.validate:
        if not args.data:
            print("[!] Please provide --data for validation")
            return
        trainer.validate(args.validate, args.data)
        return
    
    if args.dataset == 'setup':
        print("\n" + "="*60)
        print("THERMAL YOLO TRAINING SETUP")
        print("="*60)
        print("""
Choose a dataset option:

1. FLIR ADAS Dataset (recommended for thermal pedestrians):
   python train_engine.py --dataset flir

2. Custom Wildlife Dataset (create your own):
   python train_engine.py --dataset custom

3. Train with existing data.yaml:
   python train_engine.py --dataset custom --data path/to/data.yaml --epochs 100

Example full training command:
   python train_engine.py --dataset custom --data thermal_dataset/wildlife_thermal/data.yaml --epochs 100 --batch 16 --imgsz 640
        """)
        return
    
    if args.dataset == 'flir':
        if args.convert:
            # Convert FLIR to YOLO format
            data_yaml = trainer.convert_flir_to_yolo(args.flir_path)
        else:
            # Show download instructions
            trainer.download_flir_dataset()
            return
    
    elif args.dataset == 'custom':
        if args.data:
            data_yaml = args.data
        else:
            # Create template
            data_yaml = trainer.create_custom_dataset_template()
            print("\n[!] Add your data and re-run with --data option to train")
            return
    
    # Start training if we have data
    if args.data or (args.dataset == 'flir' and args.convert):
        data_yaml = args.data if args.data else data_yaml
        trainer.train(
            data_yaml=data_yaml,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            model_base=args.model,
            device=args.device
        )


if __name__ == '__main__':
    main()
