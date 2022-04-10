import pandas as pd

import torch
from torch.utils.data.dataset import Dataset  # For custom datasets


class FakeRoBERTDataset(Dataset):
    def __init__(self, df: pd.DataFrame, tokenizer: str, column: str, max_len: int = 512):
        self.tokenizer = tokenizer
        self.max_len = max_len

        self.df = df
        self.df = self.df.dropna()
        self.df = self.df[[column, "label"]]
        

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        text = self.df.iloc[idx, 0]
        label = self.df.iloc[idx, 1]

        encoded_text = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="longest",
            return_token_type_ids=True,
            return_attention_mask=True,
            truncation=True,
        )

        ids = encoded_text["input_ids"]
        mask = encoded_text["attention_mask"]
        token_type_ids = encoded_text["token_type_ids"]

        padding_length = self.max_len - len(ids)
        ids = ids + ([0] * padding_length)
        mask = mask + ([0] * padding_length)
        token_type_ids = token_type_ids + ([0] * padding_length)

        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(mask, dtype=torch.long),
            "token_type_ids": torch.tensor(token_type_ids, dtype=torch.long),
            "label": torch.tensor(label, dtype=torch.float),
        }
