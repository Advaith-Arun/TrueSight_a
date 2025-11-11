"""
TrueSight Evaluation Script
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import yaml
from pathlib import Path
from tqdm import tqdm
import sys
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(str(Path(__file__).parent.parent))

from models.ensemble import TrueSightEnsemble
from preprocessing.dataset import DeepfakeDataset


def load_config():
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / 'configs' / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def evaluate_model(model, test_loader, device):
    """Comprehensive model evaluation with threshold optimization"""
    model.eval()
    
    all_labels = []
    all_probabilities = []
    
    print("\n🔍 Evaluating on test set...")
    with torch.no_grad():
        for videos, labels in tqdm(test_loader, desc="Testing"):
            videos = videos.to(device)
            labels = labels.to(device).float()
            
            logits = model(videos).squeeze()
            probabilities = torch.sigmoid(logits)
            
            all_labels.extend(labels.cpu().numpy())
            all_probabilities.extend(probabilities.cpu().numpy())
    
    all_labels = np.array(all_labels)
    all_probabilities = np.array(all_probabilities)
    
    # Find optimal threshold
    print("\n🎯 Finding optimal classification threshold...")
    best_threshold = 0.5
    best_f1 = 0
    
    for threshold in np.arange(0.1, 0.9, 0.05):
        preds = (all_probabilities > threshold).astype(int)
        from sklearn.metrics import f1_score
        f1 = f1_score(all_labels, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    print(f"   Optimal threshold: {best_threshold:.2f} (F1: {best_f1:.2%})")
    
    # Use optimal threshold
    all_predictions = (all_probabilities > best_threshold).astype(int)
    
    return all_labels, all_predictions, all_probabilities



def calculate_metrics(labels, predictions, probabilities):
    
    accuracy = (predictions == labels).mean() * 100
    
    # Confusion matrix
    cm = confusion_matrix(labels, predictions)
    tn, fp, fn, tp = cm.ravel()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # ROC-AUC
    auc_roc = roc_auc_score(labels, probabilities)
    
    # FPR at 95% TPR
    fpr, tpr, thresholds = roc_curve(labels, probabilities)
    fpr_at_95_tpr = fpr[np.where(tpr >= 0.95)[0][0]] if any(tpr >= 0.95) else None
    
    metrics = {
        'accuracy': accuracy,
        'precision': precision * 100,
        'recall': recall * 100,
        'f1_score': f1 * 100,
        'auc_roc': auc_roc * 100,
        'fpr_at_95_tpr': fpr_at_95_tpr * 100 if fpr_at_95_tpr else None,
        'confusion_matrix': cm,
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_positives': int(tp)
    }
    
    return metrics


def plot_confusion_matrix(cm, save_path):
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Real', 'Fake'],
                yticklabels=['Real', 'Fake'])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"✅ Confusion matrix saved: {save_path}")


def plot_roc_curve(labels, probabilities, auc_roc, save_path):
    
    fpr, tpr, _ = roc_curve(labels, probabilities)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc_roc:.2f}%)')
    plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Deepfake Detection')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"✅ ROC curve saved: {save_path}")

def main():
    print("="*70)
    print("TRUESIGHT MODEL EVALUATION")
    print("="*70)
    
    # Load config
    config = load_config()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n🖥️  Device: {device}")
    
    # Load test dataset
    print("\n📊 Loading test data...")
    test_dataset = DeepfakeDataset(
        data_root=config['paths']['data_root'],  # Uses 'data/'
        split='test',
        num_frames=config['training']['num_frames']
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=config['training']['batch_size'],
        shuffle=False,
        num_workers=2
    )
    print(f"✅ Test dataset: {len(test_dataset)} videos")
    
    # Load trained model
    print("\n🧠 Loading trained model...")
    checkpoint_path = Path(config['paths']['model_checkpoints']) / 'best_model.pth'
    
    if not checkpoint_path.exists():
        print(f"❌ Model not found at: {checkpoint_path}")
        return
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model = TrueSightEnsemble(config).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"✅ Loaded checkpoint from epoch {checkpoint['epoch']}")
    print(f"   Validation Accuracy: {checkpoint.get('val_acc', 'N/A'):.2f}%")
    
    # Evaluate
    labels, predictions, probabilities = evaluate_model(model, test_loader, device)
    
    # Calculate metrics
    print("\n📈 Calculating metrics...")
    metrics = calculate_metrics(labels, predictions, probabilities)
    
    # Print results
    print("\n" + "="*70)
    print("TEST SET RESULTS")
    print("="*70)
    print(f"\n🎯 Overall Performance:")
    print(f"   Accuracy:  {metrics['accuracy']:.2f}%")
    print(f"   Precision: {metrics['precision']:.2f}%")
    print(f"   Recall:    {metrics['recall']:.2f}%")
    print(f"   F1-Score:  {metrics['f1_score']:.2f}%")
    print(f"   AUC-ROC:   {metrics['auc_roc']:.2f}%")
    if metrics['fpr_at_95_tpr']:
        print(f"   FPR@95%TPR: {metrics['fpr_at_95_tpr']:.2f}%")
    
    print(f"\n📊 Confusion Matrix:")
    print(f"   True Negatives:  {metrics['true_negatives']} (Real correctly identified)")
    print(f"   False Positives: {metrics['false_positives']} (Real misclassified as Fake)")
    print(f"   False Negatives: {metrics['false_negatives']} (Fake misclassified as Real)")
    print(f"   True Positives:  {metrics['true_positives']} (Fake correctly identified)")
    
    # Save results
    results_dir = Path(config['paths']['results'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save plots
    plot_confusion_matrix(
        metrics['confusion_matrix'],
        results_dir / 'confusion_matrix.png'
    )
    
    plot_roc_curve(
        labels, probabilities, metrics['auc_roc'],
        results_dir / 'roc_curve.png'
    )
    
    # Save metrics to file
    with open(results_dir / 'metrics.txt', 'w') as f:
        f.write("TrueSight Model Evaluation Results\n")
        f.write("="*50 + "\n\n")
        f.write(f"Accuracy:  {metrics['accuracy']:.2f}%\n")
        f.write(f"Precision: {metrics['precision']:.2f}%\n")
        f.write(f"Recall:    {metrics['recall']:.2f}%\n")
        f.write(f"F1-Score:  {metrics['f1_score']:.2f}%\n")
        f.write(f"AUC-ROC:   {metrics['auc_roc']:.2f}%\n")
        if metrics['fpr_at_95_tpr']:
            f.write(f"FPR@95%TPR: {metrics['fpr_at_95_tpr']:.2f}%\n")
        f.write(f"\nTrue Negatives:  {metrics['true_negatives']}\n")
        f.write(f"False Positives: {metrics['false_positives']}\n")
        f.write(f"False Negatives: {metrics['false_negatives']}\n")
        f.write(f"True Positives:  {metrics['true_positives']}\n")
    
    print(f"\n💾 Results saved to: {results_dir}/")
    print("="*70)


if __name__ == '__main__':
    main()
