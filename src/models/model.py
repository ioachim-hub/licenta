import torch

import torch.nn as nn
import torch.nn.functional as F

import transformers
import licenta.src.models.config


class FakeRoBERTModel(nn.Module):
    def __init__(self):
        super(FakeRoBERTModel, self).__init__()
        # embedding
        self.bert = transformers.AutoModel.from_pretrained(licenta.src.models.config.BERT_PATH)

        # first convolutional layers
        self.conv1_2 = nn.Conv1d(1000, 100, kernel_size=3, stride=1, padding=0)
        self.conv2_2 = nn.Conv1d(1000, 100, kernel_size=4, stride=1, padding=0)
        self.conv3_2 = nn.Conv1d(1000, 100, kernel_size=5, stride=1, padding=0)
        self.drop1_3 = nn.Dropout(p=0.2)
        self.drop2_3 = nn.Dropout(p=0.2)
        self.drop3_3 = nn.Dropout(p=0.2)
        self.pool1_4 = nn.MaxPool1d(kernel_size=5, stride=3, padding=0)
        self.pool2_4 = nn.MaxPool1d(kernel_size=5, stride=3, padding=0)
        self.pool3_4 = nn.MaxPool1d(kernel_size=5, stride=3, padding=0)

        # second convolutional layers
        self.conv1_5 = nn.Conv1d(199, 128, kernel_size=5, stride=1, padding=0)
        self.drop1_5 = nn.Dropout(p=0.2)
        self.pool1_5 = nn.MaxPool1d(kernel_size=5, stride=3, padding=0)
        self.conv1_6 = nn.Conv1d(39, 128, kernel_size=5, stride=1, padding=0)
        self.drop1_6 = nn.Dropout(p=0.2)
        self.pool1_6 = nn.MaxPool1d(kernel_size=5, stride=3, padding=0)

        # flatten
        self.flatt_7 = nn.Flatten(1, -1)

        # dense layers
        self.dense1_8 = nn.Linear(128, 128)
        self.dense1_9 = nn.Linear(128, 2)

    def forward(self, input_ids, attention_mask, token_type_ids):
        _, pooled_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        conv1_2 = self.pool1_4(self.drop1_3(F.relu(self.conv1_2(pooled_output))))
        conv2_2 = self.pool2_4(self.drop2_3(F.relu(self.conv2_2(pooled_output))))
        conv3_2 = self.pool3_4(self.drop3_3(F.relu(self.conv3_2(pooled_output))))
        x = torch.cat((conv1_2, conv2_2, conv3_2), dim=1)
        x = self.pool1_5(self.drop1_5(F.relu(self.conv1_5(x))))
        x = self.pool1_6(self.drop1_6(F.relu(self.conv1_6(x))))
        x = self.flatt_7(x)
        x = self.dense1_8(x)
        x = self.dense1_9(x)

        return x
