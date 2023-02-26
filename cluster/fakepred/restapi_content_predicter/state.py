import os

import torch
import torch.nn as nn
import transformers

from fakepred.restapi_content_predicter.ml_model import FakeRoBERTModel


os.environ["CUDA_VISIBLE_DEVICES"] = ""
BERT_PATH = "dumitrescustefan/bert-base-romanian-cased-v1"


class RESTState:
    def __init__(self) -> None:
        self.device = torch.device("cpu")

        model = FakeRoBERTModel()
        model = model.to(self.device)
        model = nn.DataParallel(model)
        model.load_state_dict(
            torch.load("trained_models/pytorch_fakerobertmodel_content_cpu.bin")
        )

        self.model = model
        self.tokenizer = transformers.BertTokenizer.from_pretrained(
            BERT_PATH, do_lower_case=True
        )

    def predict(
        self,
        text: str,
        max_len: int = 512,
    ) -> float:
        self.model.eval()
        with torch.no_grad():
            encoded_text = self.tokenizer.encode_plus(
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

            ids = ids.to(self.device, dtype=torch.long)
            token_type_ids = token_type_ids.to(self.device, dtype=torch.long)
            mask = mask.to(self.device, dtype=torch.long)

            output = self.model(
                input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids
            )

        output = output.cpu().detach().numpy()
        return output
