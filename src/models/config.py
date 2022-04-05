import transformers


MAX_LEN = 512
TRAIN_BATCH_SIZE = 128
VALID_BATCH_SIZE = 128
LEARNING_RATE = 0.001
EPOCHS = 10
COLUMN = "title"
BERT_PATH = "dumitrescustefan/bert-base-romanian-cased-v1"
MODEL_PATH = "../../models/pytorch_fakerobertmodel.bin"
TRAINING_FILE = "../../data/processed/scrapped_cleaned_valid_and_fake_balanced.gzip"
TOKENIZER = transformers.BertTokenizer.from_pretrained(BERT_PATH, do_lower_case=True)
