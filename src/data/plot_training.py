import re
import click
import logging
import numpy as np
import plotly.io as pio
import plotly.subplots as psub
import plotly.graph_objects as go

pio.renderers.default = "notebook_connected"


@click.command()
@click.argument("log_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(log_filepath: str, output_filepath: str):
    logger = logging.getLogger(__name__)
    logger.info("plotting trainig of model")
    loss_re = re.compile(r".*loss:(\d+\.\d+)")
    acc_re = re.compile(r".*accuracy: (\d+\.\d+)")
    epoch_acc_re = re.compile(r".*Accuracy: (\d+\.\d+)")

    loss = []
    acc = []
    epoch_acc = []

    with open(log_filepath, "r") as o:
        for line in o:
            if loss_re.match(line):
                number = loss_re.match(line)
                if number is not None:
                    loss.append(float(number.group(1)))
            if acc_re.match(line):
                number = acc_re.match(line)
                if number is not None:
                    acc.append(float(number.group(1)))
            if epoch_acc_re.match(line):
                number = epoch_acc_re.match(line)
                if number is not None:
                    epoch_acc.append(float(number.group(1)))

    fig = psub.make_subplots(rows=3, cols=1)
    fig.add_trace(go.Scatter(x=np.arange(len(loss)), y=loss, name="loss"), row=1, col=1)
    fig.add_trace(go.Scatter(x=np.arange(len(acc)), y=acc, name="acc"), row=2, col=1)
    fig.add_trace(
        go.Scatter(x=np.arange(len(epoch_acc)), y=epoch_acc, name="epoch_acc"),
        row=3,
        col=1,
    )
    fig.update_layout(height=800, width=800)

    fig.write_html(output_filepath)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
