import transformers


MAX_LEN = 512
TRAIN_BATCH_SIZE = 1
VALID_BATCH_SIZE = 1
LEARNING_RATE = 0.00001
EPOCHS = 20
COLUMN = "title"
BERT_PATH = "dumitrescustefan/bert-base-romanian-cased-v1"
MODEL_PATH = f"models/pytorch_fakerobertmodel_{COLUMN}_conv.bin"
TRAINING_FILE = "data/processed/toy_dataset.gzip"
# "../../data/processed/scrapped_cleaned_valid_and_fake_balanced.gzip"
TOKENIZER = transformers.BertTokenizer.from_pretrained(BERT_PATH, do_lower_case=True)
