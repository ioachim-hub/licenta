import logging
import torch
import pandas as pd
import torch.nn as nn

from sklearn import model_selection
from sklearn.preprocessing import LabelEncoder
from transformers import get_linear_schedule_with_warmup
from torch.optim import AdamW

import src.models.engine
import src.models.config
from src.models.model import FakeRoBERTModel
from src.models.dataloader import FakeRoBERTDataset

logging.basicConfig(
    filename="logs.txt",
    filemode='a',
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)


def run():
    logging.info("Starting training...")
    logging.info("Loading data...")
    dfx = pd.read_parquet(src.models.config.TRAINING_FILE).fillna("none")

    logging.info("Splitting data...")
    df_train, df_valid = model_selection.train_test_split(
        dfx, test_size=0.1, random_state=42)

    df_train = df_train.reset_index(drop=True)
    df_valid = df_valid.reset_index(drop=True)

    logging.info("Creating datasets...")
    train_dataset = FakeRoBERTDataset(
        df_train, src.models.config.TOKENIZER, src.models.config.COLUMN, src.models.config.MAX_LEN
    )

    train_data_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=src.models.config.TRAIN_BATCH_SIZE, num_workers=4
    )

    valid_dataset = FakeRoBERTDataset(
        df_valid, src.models.config.TOKENIZER, src.models.config.COLUMN, src.models.config.MAX_LEN
    )

    valid_data_loader = torch.utils.data.DataLoader(
        valid_dataset, batch_size=src.models.config.VALID_BATCH_SIZE, num_workers=1
    )

    logging.info("Creating model...")
    device = torch.device("cuda")
    model = FakeRoBERTModel()
    model.to(device)

    logging.info("Creating optimizer...")
    param_optimizer = list(model.named_parameters())
    no_decay = ["bias", "LayerNorm.bias", "LayerNorm.weight"]
    optimizer_parameters = [
        {
            "params": [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
            "weight_decay": 0.001,
        },
        {
            "params": [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
            "weight_decay": 0.0,
        },
    ]

    num_train_steps = int(
        len(df_train) / src.models.config.TRAIN_BATCH_SIZE *
        src.models.config.EPOCHS
    )
    optimizer = AdamW(optimizer_parameters, lr=src.models.config.LEARNING_RATE)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=0, num_training_steps=num_train_steps
    )

    model = nn.DataParallel(model)
    # model.load_state_dict(torch.load(src.models.config.MODEL_PATH))

    best_accuracy = 0

    logging.info("Training model...")
    for epoch in range(0, src.models.config.EPOCHS):
        logging.info(f"Starting epoch {epoch}...")
        logging.info(f"Epoch: {epoch}")
        src.models.engine.train_fn(
            train_data_loader, model, optimizer, device, scheduler)
        outputs, targets = src.models.engine.eval_fn(
            valid_data_loader, model, device)
        accuracy = src.models.engine.accuracy_score(targets, outputs)
        logging.info(f"Accuracy: {accuracy}")
        logging.info(f"Accuracy Score = {accuracy}")
        if accuracy > best_accuracy:
            logging.info(f"New best accuracy! {accuracy}")
            torch.save(model.state_dict(), src.models.config.MODEL_PATH)
            best_accuracy = accuracy


if __name__ == "__main__":
    run()
