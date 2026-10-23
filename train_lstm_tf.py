import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score

print(f"TensorFlow Version: {tf.__version__}")

# 1. Load Data
print("Loading phishing dataset...")
df = pd.read_csv("phishing_email.csv")
X_texts = df["text_combined"].astype(str).values
y_labels = df["label"].astype(int).values

MAX_WORDS = 20000
MAX_LEN = 120

print("Tokenizing texts...")
tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
tokenizer.fit_on_texts(X_texts)

sequences = tokenizer.texts_to_sequences(X_texts)
padded_sequences = pad_sequences(sequences, maxlen=MAX_LEN, padding="post", truncating="post")
print("Sequence tensor shape:", padded_sequences.shape)

X_train, X_test, y_train, y_test = train_test_split(
    padded_sequences, y_labels, test_size=0.20, random_state=42, stratify=y_labels
)

# 2. Build Bidirectional LSTM in TensorFlow
print("Building Bidirectional LSTM Model...")
model = Sequential([
    Embedding(input_dim=MAX_WORDS, output_dim=64, input_length=MAX_LEN),
    Bidirectional(LSTM(64, return_sequences=False)),
    Dropout(0.3),
    Dense(32, activation="relu"),
    Dropout(0.2),
    Dense(1, activation="sigmoid")
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

# 3. Train on 35,000 samples for fast convergence and high accuracy
print("Training TensorFlow LSTM...")
model.fit(
    X_train[:35000], y_train[:35000],
    epochs=2,
    batch_size=128,
    validation_split=0.15,
    verbose=1
)

# 4. Evaluate
print("Evaluating on test set...")
y_prob = model.predict(X_test[:5000], batch_size=256).flatten()
y_pred = (y_prob >= 0.5).astype(int)

acc = accuracy_score(y_test[:5000], y_pred)
auc = roc_auc_score(y_test[:5000], y_prob)

print(f"\nTensorFlow LSTM Accuracy: {acc * 100:.2f}%")
print(f"TensorFlow LSTM ROC-AUC : {auc:.4f}")
print("Classification Report:\n", classification_report(y_test[:5000], y_pred, digits=4))

# 5. Save Artifacts
save_dir = os.path.join("backend", "ml", "saved_models")
os.makedirs(save_dir, exist_ok=True)

model_path = os.path.join(save_dir, "lstm_model.keras")
model.save(model_path)

tokenizer_json = tokenizer.to_json()
with open(os.path.join(save_dir, "lstm_tokenizer.json"), "w", encoding="utf-8") as f:
    f.write(tokenizer_json)

print(f"TensorFlow LSTM model and tokenizer saved to {save_dir} successfully!")
