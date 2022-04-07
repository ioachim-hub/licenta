import logging
import torch
import torch.nn as nn
from tqdm import tqdm

logging.basicConfig(
    filename="app.log", filemode="w", format="%(name)s - %(levelname)s - %(message)s"
)


def loss_fn(outputs, targets):
    loss = nn.KLDivLoss()(outputs, targets.view(-1, 1))
    print(loss)
    return loss


def accuracy_score(targets, outputs):
    num_matches: int = 0
    for output, target in zip(outputs, targets):
        if abs(output[0] - target) < 0.05:
            num_matches += 1

    return num_matches / len(outputs)


def train_fn(data_loader, model, optimizer, device, scheduler):
    logging.info("Starting training on epoch...")
    model.train()

    for _, d in tqdm(enumerate(data_loader), total=len(data_loader)):
        ids = d["input_ids"]
        token_type_ids = d["token_type_ids"]
        mask = d["attention_mask"]
        targets = d["label"]

        ids = ids.to(device, dtype=torch.long)
        token_type_ids = token_type_ids.to(device, dtype=torch.long)
        mask = mask.to(device, dtype=torch.long)
        targets = targets.to(device, dtype=torch.float)

        optimizer.zero_grad()
        outputs = model(input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids)

        loss = loss_fn(outputs, targets)
        loss.backward()
        optimizer.step()
        scheduler.step()


def eval_fn(data_loader, model, device):
    logging.info("Starting evaluation on epoch...")
    model.eval()
    fin_targets = []
    fin_outputs = []
    with torch.no_grad():
        for _, d in tqdm(enumerate(data_loader), total=len(data_loader)):
            ids = d["input_ids"]
            token_type_ids = d["token_type_ids"]
            mask = d["attention_mask"]
            targets = d["label"]

            ids = ids.to(device, dtype=torch.long)
            token_type_ids = token_type_ids.to(device, dtype=torch.long)
            mask = mask.to(device, dtype=torch.long)
            targets = targets.to(device, dtype=torch.float)

            outputs = model(input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids)
            fin_targets.extend(targets.cpu().detach().numpy().tolist())
            fin_outputs.extend(torch.relu(outputs).cpu().detach().numpy().tolist())
    return fin_outputs, fin_targets
