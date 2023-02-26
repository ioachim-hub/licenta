import torch
import transformers

from sklearn import preprocessing
from models.model import FakeRoBERTModel  # import: ignore


def predict(
    text: str,
    model: FakeRoBERTModel,
    tokenizer: transformers.BertTokenizer,
    scaler: preprocessing.MinMaxScaler,
    device: torch.device,
    max_len: int = 512,
):
    model.eval()
    with torch.no_grad():
        encoded_text = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=max_len,
            padding="longest",
            return_token_type_ids=True,
            return_attention_mask=True,
            truncation=True,
        )

        ids = encoded_text["input_ids"]
        mask = encoded_text["attention_mask"]
        token_type_ids = encoded_text["token_type_ids"]

        padding_length = max_len - len(ids)
        ids = ids + ([0] * padding_length)
        mask = mask + ([0] * padding_length)
        token_type_ids = token_type_ids + ([0] * padding_length)

        ids = torch.tensor([ids], dtype=torch.long)
        mask = torch.tensor([mask], dtype=torch.long)
        token_type_ids = torch.tensor([token_type_ids], dtype=torch.long)

        ids = ids.to(device, dtype=torch.long)
        token_type_ids = token_type_ids.to(device, dtype=torch.long)
        mask = mask.to(device, dtype=torch.long)

        output = model(
            input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids
        )

    output = output.cpu().detach().numpy()
    return scaler.inverse_transform(output)
