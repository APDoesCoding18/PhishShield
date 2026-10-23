import os
import re
import json
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score

print(f"PyTorch version: {torch.__version__}")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# 1. Load Data
print("Loading dataset for LSTM...")
df = pd.read_csv("phishing_email.csv")
X_texts = df["text_combined"].astype(str).tolist()
y_labels = df["label"].astype(int).tolist()

# 2. Build Vocabulary (Top 20,000 frequent words)
print("Building vocabulary...")
def tokenize(text):
    return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

from collections import Counter
word_counts = Counter()
for text in X_texts[:40000]: # Sample for fast, high-quality vocab
    word_counts.update(tokenize(text))

MAX_WORDS = 20000
vocab = {"<PAD>": 0, "<UNK>": 1}
for idx, (word, _) in enumerate(word_counts.most_common(MAX_WORDS - 2), start=2):
    vocab[word] = idx

MAX_LEN = 120

def encode_text(text):
    tokens = tokenize(text)[:MAX_LEN]
    encoded = [vocab.get(t, 1) for t in tokens]
    if len(encoded) < MAX_LEN:
        encoded += [0] * (MAX_LEN - len(encoded))
    return encoded

print("Encoding texts...")
# Split first
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X_texts, y_labels, test_size=0.20, random_state=42, stratify=y_labels
)

# For fast training on CPU while preserving high accuracy, train on 35,000 samples
X_train_enc = np.array([encode_text(t) for t in X_train_raw[:35000]], dtype=np.int64)
y_train_sub = np.array(y_train[:35000], dtype=np.float32)

X_test_enc = np.array([encode_text(t) for t in X_test_raw[:5000]], dtype=np.int64)
y_test_sub = np.array(y_test[:5000], dtype=np.float32)

class EmailDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_loader = DataLoader(EmailDataset(X_train_enc, y_train_sub), batch_size=128, shuffle=True)
test_loader = DataLoader(EmailDataset(X_test_enc, y_test_sub), batch_size=128, shuffle=False)

# 3. Model Architecture
class PhishingLSTM(nn.Module):
    def __init__(self, vocab_size=20000, embed_dim=64, hidden_dim=64):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        embedded = self.embedding(x)
        out, (hn, _) = self.lstm(embedded)
        # Concatenate forward and backward final hidden states
        hidden = torch.cat((hn[-2, :, :], hn[-1, :, :]), dim=1)
        logits = self.fc(hidden).squeeze(1)
        return logits

model = PhishingLSTM(vocab_size=len(vocab)).to(device)
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.003)

# 4. Training Loop (2 epochs is sufficient to converge on 35,000 sequence samples)
print("Training Bidirectional LSTM...")
model.train()
for epoch in range(2):
    total_loss = 0
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        optimizer.zero_grad()
        preds = model(batch_x)
        loss = criterion(preds, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch + 1}/2 - Avg Loss: {total_loss / len(train_loader):.4f}")

# 5. Evaluation
model.eval()
all_probs = []
all_preds = []
with torch.no_grad():
    for batch_x, _ in test_loader:
        batch_x = batch_x.to(device)
        logits = model(batch_x)
        probs = torch.sigmoid(logits).cpu().numpy()
        all_probs.extend(probs)
        all_preds.extend((probs >= 0.5).astype(int))

acc = accuracy_score(y_test_sub, all_preds)
auc = roc_auc_score(y_test_sub, all_probs)
print(f"\nLSTM Test Accuracy: {acc * 100:.2f}%")
print(f"LSTM Test ROC-AUC:  {auc:.4f}")
print("Classification Report:\n", classification_report(y_test_sub, all_preds, digits=4))

# 6. Save Model Artifacts
save_dir = "backend/ml/saved_models"
os.makedirs(save_dir, exist_ok=True)
torch.save(model.state_dict(), os.path.join(save_dir, "lstm_model.pt"))
with open(os.path.join(save_dir, "lstm_vocab.json"), "w", encoding="utf-8") as f:
    json.dump({"vocab": vocab, "max_len": MAX_LEN}, f)

print("LSTM model state and vocabulary saved successfully!")
