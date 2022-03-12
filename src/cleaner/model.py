import re
import multiprocessing as mp


import tqdm
import numpy as np
import pandas as pd

from src.cleaner.common import Column


# https://github.com/ioachim-hub/Romanian-Transformers/tree/master/corpus
class Cleaner:
    def __init__(self, columns: list[Column], num_threads=1) -> None:
        self.columns: list[Column] = columns
        self.verbose: bool = False

        self.num_threads = min(num_threads, int(mp.cpu_count() / 2))

        """
        'sa- l', 'nu- l', 'intr- un'
        """
        self.r1 = re.compile(r"([\w]+-)[\s]([\w]+)", re.IGNORECASE)

        """
        {LL/ AAAA}
        Humalog Mix50 100 U/ ml
        """
        self.r2 = re.compile(r"([\w]+/)\s([\w]+)", re.IGNORECASE)

        """
        All unicode dashes to normal '-', see https://www.fileformat.info/info/unicode/category/Pd/list.htm
        includes bull : • \u2022
        """
        self.r3 = re.compile(
            r"([■\u2022\u007E\u00AD\u058A\u05BE\u1400\u1806\u2010\u2011\u2012\u2013\u2014\u2015\u2053\u207B\u208B\u2212"
            + r"\u2E17\u2E3A\u2E3B\u301C\u3030\u30A0\uFE31\uFE32\uFE63\uFF0D]+)",
            re.UNICODE,
        )

        """
        spaces after comma in numbers: 1, 4% -> 1,4%
        """
        self.r4 = re.compile(r"([\d]+,)\s([\d]+)", re.IGNORECASE)

        """
        soft hyphens #\u00AD
        """
        self.r5 = re.compile(r"[\u00AD]")

        """
        remove URLS
        """
        self.r6 = re.compile(r"(?:www|http)\S+|<\S+|\w+\/*>")

        """
        remove emails
        """
        self.r7 = re.compile(r"([^@]+@[^@]+\.[^@]+)")

        """
        multiple spaces
        """
        self.space = re.compile(" +")

        """
        forbiden chars that cause a lot of bad sentences
        """
        self.forbidden_chars = "ºþÈ™ÓÑÄÈÃ®ƒ"

    def map_dataframe(
        self,
        line,
        min_line_length: int,
        percent_max_numeric: float,
        percent_max_non_ascii: float,
    ):
        skipped_because_min_length = np.array([0, 0], dtype=np.uint64)
        skipped_alpha_count = np.array([0, 0], dtype=np.uint64)
        skipped_because_max_numeric = np.array([0, 0], dtype=np.uint64)
        skipped_because_max_non_ascii = np.array([0, 0], dtype=np.uint64)
        skipped_because_forbidden_chars = np.array([0, 0], dtype=np.uint64)

        line = line.strip()

        # get stats about line
        length = len(line)

        if length < min_line_length:
            skipped_because_min_length += np.array([1, length], dtype=np.uint64)
            return (
                line,
                skipped_because_min_length,
                skipped_alpha_count,
                skipped_because_max_numeric,
                skipped_because_max_non_ascii,
                skipped_because_forbidden_chars,
            )

        line = bytes(line, "utf-8").decode("utf-8", "ignore")  # strip not utf-8 chars

        digit_count = 0
        alpha_count = 0
        ascii_count = 0
        forbidden_char = False
        for char in line:
            if char in self.forbidden_chars:
                forbidden_char = True
                break
            if char.isnumeric():
                digit_count += 1
            if char.isalpha():
                alpha_count += 1
            if char.isascii():
                ascii_count += 1

        # reject if forbidden char
        if forbidden_char:
            skipped_because_forbidden_chars += np.array([1, length], dtype=np.uint64)

        # reject if number of letters is too small
        if alpha_count == 0 or alpha_count / length < 0.5:
            skipped_alpha_count += np.array([1, length], dtype=np.uint64)
            if self.verbose:
                print(f"Skipping alpha={alpha_count / length:.3f}: [{line}]")

        # reject if too many numbers
        if digit_count / alpha_count >= percent_max_numeric and digit_count > 6:
            skipped_because_max_numeric += np.array([1, length], dtype=np.uint64)
            if self.verbose:
                print(f"Skipping digit={digit_count / alpha_count:.3f}: [{line}]")
        # reject if too many non-ascii
        if ascii_count / alpha_count < percent_max_non_ascii and length > 15:
            skipped_because_max_non_ascii += np.array([1, length], dtype=np.uint64)
            if self.verbose:
                print(f"Skipping ascii={digit_count / alpha_count:.3f}: [{line}]")
        # clean line
        # print(f"\nbef: {line}")
        line = self.r1.sub(r"\1\2", line)
        line = self.r2.sub(r"\1\2", line)
        line = self.r3.sub("-", line)
        line = self.r4.sub(r"\1\2", line)
        line = self.r5.sub("", line)
        line = self.r6.sub("", line)
        line = self.r7.sub("", line)

        line = line.replace("( ă)", "(ă)")
        line = line.replace("ţ", "ț")
        line = line.replace("ş", "ș")
        line = line.replace("Ţ", "Ț")
        line = line.replace("Ş", "Ș")
        line = line.replace("Ã¢", "â")

        # print(f"aft: {line}")

        line = self.space.sub(" ", line).strip()

        # check that after processing the line is not too short
        if len(line) < min_line_length:
            skipped_because_min_length += np.array([1, length], dtype=np.uint64)

        return (
            line,
            skipped_because_min_length,
            skipped_alpha_count,
            skipped_because_max_numeric,
            skipped_because_max_non_ascii,
            skipped_because_forbidden_chars,
        )

    def multiprocessing_thread(
        self,
        df,
    ) -> None:

        for column in self.columns:
            (
                df[column.name],
                df[f"{column.name}_skipped_because_min_length"],
                df[f"{column.name}_skipped_alpha_count"],
                df[f"{column.name}_skipped_because_max_numeric"],
                df[f"{column.name}_skipped_because_max_non_ascii"],
                df[f"{column.name}_skipped_because_forbidden_chars"],
            ) = zip(
                *df[column.name].apply(
                    self.map_dataframe,
                    args=(
                        column.min_line_length,
                        column.percent_max_numeric,
                        column.percent_max_non_ascii,
                    ),
                )
            )
        return df

    def process(self, df):
        # https://pypi.org/project/tqdm/#ipython-jupyter-integration
        # https://stackoverflow.com/questions/26784164/pandas-multiprocessing-apply
        # https://stackoverflow.com/questions/41920124/multiprocessing-use-tqdm-to-display-a-progress-bar
        df_split = np.array_split(df, self.num_threads)
        df_output: pd.DataFrame

        with mp.Pool(self.num_threads) as p:
            df_output = pd.concat(
                tqdm.tqdm(p.map(self.multiprocessing_thread, df_split))
            )

        # pack stats
        stats = {}
        for column in self.columns:

            stats[f"{column.name}_skipped_because_min_length"] = df_output[
                f"{column.name}_skipped_because_min_length"
            ].sum()
            stats[f"{column.name}_skipped_alpha_count"] = df_output[
                f"{column.name}_skipped_alpha_count"
            ].sum()
            stats[f"{column.name}_skipped_because_max_numeric"] = df_output[
                f"{column.name}_skipped_because_max_numeric"
            ].sum()
            stats[f"{column.name}_skipped_because_max_non_ascii"] = df_output[
                f"{column.name}_skipped_because_max_non_ascii"
            ].sum()
            stats[f"{column.name}_skipped_because_forbidden_chars"] = df_output[
                f"{column.name}_skipped_because_forbidden_chars"
            ].sum()

        return df_output, stats

    def add_stats(self, a, b):
        """
        Add two stats dict that are returned by the process function.
        This is used for multiple files
        :param a: stats dict
        :param b: stats dict
        :return: stats dict
        """
        stats = {}
        for key in a.keys:
            stats[key] = a[key] + b[key]

        return stats

    def print_stats(self, stats):
        print("\nCleaning statistics:")
        print(f"Total original length (chars) = {stats['total_original_length']}")
        print(f"Total length after cleaning (chars) = {stats['total_clean_length']}")
        print(
            f"Percent data kept = {100.0 * stats['total_clean_length'] / stats['total_original_length']:.3f} %"
        )

        print(
            f"Skipped because line length was below minimum (lines/chars): {stats['skipped_because_min_length']}"
        )
        print(
            f"Skipped because line had forbidden characters (lines/chars): {stats['skipped_because_forbidden_chars']}"
        )
        print(
            f"Skipped because alpha count was below minimum (lines/chars): {stats['skipped_alpha_count']}"
        )
        print(
            f"Skipped because digit count was above maximum (lines/chars): {stats['skipped_because_max_numeric']}"
        )
        print(
            f"Skipped because too many non-ascii characters (lines/chars): {stats['skipped_because_max_non_ascii']}"
        )
