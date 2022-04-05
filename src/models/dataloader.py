import pandas as pd

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
            pad_to_max_length=True,
            return_token_type_ids=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoded_text["input_ids"].squeeze(0),
            "attention_mask": encoded_text["attention_mask"].squeeze(0),
            "token_type_ids": encoded_text["token_type_ids"].squeeze(0),
            "label": label,
        }
