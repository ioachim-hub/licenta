import transformers


MAX_LEN = 512
TRAIN_BATCH_SIZE = 32
VALID_BATCH_SIZE = 32
LEARNING_RATE = 0.00001
EPOCHS = 20
COLUMN = "content"
BERT_PATH = "dumitrescustefan/bert-base-romanian-cased-v1"
MODEL_PATH = f"models/pytorch_fakerobertmodel_{COLUMN}_twenty_epochs.bin"
TRAINING_FILE = "data/processed/scrappedv2.gzip"
# "../../data/processed/scrapped_cleaned_valid_and_fake_balanced.gzip"
TOKENIZER = transformers.BertTokenizer.from_pretrained(
    BERT_PATH, do_lower_case=True)
