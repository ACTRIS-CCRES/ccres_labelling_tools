"""Function to plot coverage of data availability for different products."""

from pathlib import Path
from types import ModuleType

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import DateFormatter, MonthLocator
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

from ccres_labelling_tools.coverage.utils import (
    add_logo,
    check_vars_in_df,
    extract_short_pid,
)


def plot_data_coverage(
    site: str,
    df: pd.DataFrame,
    months_start: int,
    output_dir: Path,
    params: ModuleType,
) -> None:
    """_summary_

    Parameters
    ----------
    site : _type_
        _description_
    df : _type_
        _description_
    months_start : _type_
        _description_
    output_dir : _type_
        _description_
    params : _type_
        _description_
    """
    # get monthly mean
    df = df.fillna(0).resample("1MS").mean()
    df = df.dropna(axis=1, how="all")

    # get date of analysis for plotting
    date_start_analysis = df.index[0]
    date_end_analysis = df.index[-1]

    # Annual reindexing on monthly basis
    df = df.reindex(months_start)

    df = check_vars_in_df(df, params.all_products)
    df = df.rename(columns={"radar_backup": "radar"})

    width = pd.Timedelta("20d")
    # PLOT
    fig, axes = plt.subplots(len(params.products_to_plot), 1, figsize=(9, 10))
    avail_below_75 = (df[params.products_to_plot] < 75).sum(axis=1) >= 1
    problematic_dates = avail_below_75.index[avail_below_75]

    for n, product in enumerate(params.products_to_plot):
        avail_series = df[product]
        color_vector = []
        for d in df.index:
            if d in problematic_dates:
                color_vector.append("yellow")
            else:
                color_vector.append("g")

        axes[n].bar(
            avail_series.index,
            avail_series,
            width=width,
            align="center",
            color=color_vector,
            edgecolor="k",
            alpha=0.7,
        )
        # short pid for title
        if product not in ["categorize", "classification"]:
            if product in ["mwr-l1c", "mwr-single", "mwr-multi"]:
                product_pid = "mwr"
            else:
                product_pid = product
            if isinstance(site["nominal_instrument"][product_pid], dict):
                short_pid = extract_short_pid(
                    site["nominal_instrument"][product_pid]["1"]
                )
            else:
                short_pid = extract_short_pid(site["nominal_instrument"][product_pid])
            axes[n].set_title(
                f"{params.products_to_plot[n].capitalize()} availability (pid:{short_pid} [{df[product].mean():.0f}%])",  # noqa:E501
                fontsize=params.asize,
            )
        else:
            axes[n].set_title(
                f"{params.products_to_plot[n].capitalize()} availability [{df[product].mean():.0f}%]",  # noqa:E501
                fontsize=params.asize,
            )

        # line for 75% of data - ACTRIS HO rule
        axes[n].hlines(
            75,
            df.index[0] - width,
            df.index[-1] + width,
            lw=1.5,
            color="k",
            ls="--",
        )

    # legend
    legend_patches = [
        Patch(facecolor="g", label="Compliant", alpha=0.7, edgecolor="k"),
        Patch(
            facecolor="yellow",
            label="Warning\nTo be investigated",
            alpha=0.7,
            edgecolor="k",
        ),
    ]

    # custom
    for i, ax in enumerate(axes.flatten()):
        if i == 0:
            ax.legend(
                handles=legend_patches,
                loc="center left",
                fontsize=params.lsize,
                bbox_to_anchor=(-0.08, 1.75),
            )
        if i not in [6]:  # noqa: FURB171
            ax.tick_params(labelbottom=False)
        else:
            ax.xaxis.set_major_formatter(DateFormatter("%b"))
            ax.xaxis.set_major_locator(MonthLocator(interval=1))
            ax.set_xlabel(f"{avail_series.index.year[0]}", fontsize=params.asize)

        ax.set_ylabel("[%]", fontsize=params.asize)
        ax.tick_params(labelsize=params.lsize)
        ax.set_ylim(0, 100)
        ax.set_xlim(df.index[0] - width, df.index[-1] + width)
        ax.yaxis.set_minor_locator(MultipleLocator(10))
        ax.yaxis.set_major_locator(MultipleLocator(50))
        ax.xaxis.set_minor_locator(MonthLocator())
    plt.tight_layout()
    fig.suptitle(
        f"{site['station'].capitalize()} ({site['lat']}°N, {site['lon']}°E, {site['alt']}m)\nCloudnet Data Availability\n{date_start_analysis.strftime('%b')}-{date_end_analysis.strftime('%b %Y')} analysis",  # noqa: E501
        fontsize=params.tsize,
    )
    add_logo(left=0.78, bottom=0.885, width=0.2, height=0.1)
    plt.subplots_adjust(top=0.86)

    filename = f"{site['station'].lower()}_{date_start_analysis.strftime('%Y%m%d')}_{date_end_analysis.strftime('%Y%m%d')}_cloudnet_data_availability.png"  # noqa: E501
    output_filename = output_dir / site["station"].lower() / filename
    output_filename.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_filename)

    plt.close()
