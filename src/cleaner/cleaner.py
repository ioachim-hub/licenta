import click
import pickle

import pandas as pd

from src.cleaner.common import load_cfg
from src.cleaner.model import Cleaner


@click.command()
@click.argument("config_filepath", type=click.Path(exists=True))
def main(config_filepath):
    cfg = load_cfg(config_filepath=config_filepath)
    cleaner = Cleaner(num_threads=cfg.num_threads, columns=cfg.colums)
    df_input = pd.read_parquet(cfg.input_filepath)
    df_output, s = cleaner.process(df_input)
    df_output.to_parquet(cfg.output_df_filepath)

    with open(cfg.output_stats_filepath, "wb") as output_file:
        pickle.dump(s, output_file)


if __name__ == "__main__":
    main()
