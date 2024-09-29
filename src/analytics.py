import asyncio  # noqa: I001
import logging
import tempfile
from typing import TypedDict

import matplotlib
matplotlib.use("Agg")  # Prevents matplotlib from displayin
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pydantic import BaseModel

from utils import ANSICodes


class AnalyticsService(TypedDict):
    load_time: float
    timeout_count: int
    error_count: int


class Analytics(BaseModel):
    services: dict[str, AnalyticsService]
    speed_box_plot: str  # base64 encoded png


sns.set_theme(
    style="darkgrid",
    palette="vlag",
    rc={
        "axes.spines.right": True,
        "axes.spines.top": False
    }
)

logger = logging.getLogger(f"{ANSICodes.MAGENTA}analytics{ANSICodes.RESET}")

_lock = asyncio.Lock()


def _render_speed_box_plot(data: dict[str, list[int | float]]) -> bytes:
    logger.info("Rendering box plot")
    logger.debug(f"Data: {data}")

    # Fill in missing values with NaN
    series_data = {}
    for key, value in data.items():
        series_data[key] = pd.Series(value)

    # Create dataframe
    df = pd.DataFrame(series_data)

    # Create figure
    fig, ax = plt.subplots()
    ax.set(
        title="Speed of Services Box Plot",
        xlabel="Time in seconds",
        ylabel="Services"
    )

    # Box plot
    sns.boxplot(
        df,
        orient="h",
        width=0.5
    )

    # Strip plot
    sns.stripplot(
        df,
        orient="h",
        size=4,
        color="0.3"
    )

    # Set size
    fig.set_size_inches(10, 5)

    # Adjust margins to fit text
    plt.tight_layout()

    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        logger.debug("Saving to temporary file")
        plt.savefig(f.name)
        logger.debug("Saved")
        plt.close(fig)
        logger.info("Finished box plot")
        return f.read()


async def render_speed_box_plot(data: dict[str, list[int | float]]) -> bytes:
    """Render a box plot of the speed of the services."""
    async with _lock:
        logger.debug("Starting box plot thread")
        response = await asyncio.to_thread(_render_speed_box_plot, data)
        logger.debug("Finished box plot thread")
        return response
