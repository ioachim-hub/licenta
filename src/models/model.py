import torch

import torch.nn as nn

import transformers
import models.config


class FakeRoBERTModel(nn.Module):
    def __init__(self):
        super(FakeRoBERTModel, self).__init__()
        # embedding
        self.bert = transformers.AutoModel.from_pretrained(models.config.BERT_PATH)

        # first convolutional layers
        self.conv1_2 = nn.Conv1d(768, 512, kernel_size=1, stride=1, padding=0)
        self.drop1_3 = nn.Dropout(p=0.2)
        self.pool1_4 = nn.MaxPool1d(kernel_size=1, stride=2, padding=0)

        # second convolutional layers
        self.conv1_5 = nn.Conv1d(512, 256, kernel_size=1, stride=1, padding=0)
        self.drop1_5 = nn.Dropout(p=0.2)
        self.pool1_5 = nn.MaxPool1d(kernel_size=1, stride=2, padding=0)
        self.conv1_6 = nn.Conv1d(256, 64, kernel_size=1, stride=1, padding=0)
        self.drop1_6 = nn.Dropout(p=0.2)
        self.pool1_6 = nn.MaxPool1d(kernel_size=1, stride=2, padding=0)

        # flatten
        self.flatt_7 = nn.Flatten(1, -1)

        # dense layers
        self.dense1_8 = nn.Linear(64, 32)
        self.dense1_9 = nn.Linear(32, 1)

        self.dense_1 = nn.Linear(768, 256)
        self.dense_3 = nn.Linear(256, 32)
        self.dense_4 = nn.Linear(32, 1)

    def forward(self, input_ids, attention_mask, token_type_ids):
        _, pooled_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            return_dict=False,
        )

        # x, y = pooled_output.size()
        # pooled_output = torch.reshape(pooled_output, (x, y, 1))

        # conv1_2 = self.pool1_4(self.drop1_3(
        #     torch.relu(self.conv1_2(pooled_output))))
        # x = conv1_2
        # x = self.pool1_5(self.drop1_5(torch.relu(self.conv1_5(x))))
        # x = self.pool1_6(self.drop1_6(torch.relu(self.conv1_6(x))))
        # x = self.flatt_7(x)
        # x = self.dense1_8(x)
        # x = self.dense1_9(x)

        x = pooled_output
        x = self.drop1_5(torch.relu(self.dense_1(x)))
        x = self.drop1_3(torch.relu(self.dense_3(x)))
        x = torch.sigmoid(self.dense_4(x))

        return x
