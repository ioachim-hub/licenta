import pydantic


class Column(pydantic.BaseModel):
    name: str
    percent_max_numeric: float
    percent_max_non_ascii: float
    min_line_length: int


class Config(pydantic.BaseModel):
    input_filepath: str
    output_stats_filepath: str
    output_df_filepath: str
    num_threads: int
    colums: list[Column]


def load_cfg(config_filepath: str) -> Config:
    with open(config_filepath, "r") as o:
        return Config.parse_raw(o.read())
