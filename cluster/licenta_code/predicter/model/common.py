import os
import pickle
import torch
import torch.nn as nn
import transformers

from model.model import FakeRoBERTModel

os.environ["CUDA_VISIBLE_DEVICES"] = ""

with open("train_models/scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

device = torch.device("cpu")

model_title = FakeRoBERTModel()
model_title = model_title.to(device)
model_title = nn.DataParallel(model_title)
model_title.load_state_dict(
    torch.load("train_models/pytorch_fakerobertmodel_title_cpu.bin")
)

model_content = FakeRoBERTModel()
model_content = model_content.to(device)
model_content = nn.DataParallel(model_content)
model_content.load_state_dict(
    torch.load("train_models/pytorch_fakerobertmodel_content_cpu.bin")
)

BERT_PATH = "model/bert-base-romanian-cased-v1"
TOKENIZER = transformers.BertTokenizer.from_pretrained(BERT_PATH, do_lower_case=True)
