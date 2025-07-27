import jinja2
import datetime as dt
import pandas as pd
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import io
import pathlib 
import argparse
import plotly.express as px

TEMPLATE_FOLDER_PATH = pathlib.Path(__file__).parent / "templates"
OUTPUT_FOLDER_PATH = pathlib.Path(__file__).parent / "reports"
DATE_FORMAT = "%d-%b-%Y" 

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate HTML report from CSV data"
    )
    
    parser.add_argument(
        "-f", "--csv_file_input", 
        type=str,
        required=True, 
        help="Path to input CSV file"
    )

    parser.add_argument(
        "-o", "--output_filename",
        type=str,
        required=True,
        help="Name of the output HTML file"
    )

    parser.add_argument(
        "-t", "--top_items",
        type=int,
        default=5,
        help="Number of top items to highlight"
    )

    return parser.parse_args()


def create_bar_chart_vpc(df: pd.DataFrame) -> str:
    grouped_df = df[["Value", "code"]].groupby("code").max().reset_index()
    fig = px.bar(grouped_df, x="code", y="Value", title="Maximum Values by Code")
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def convert_to_month(df:pd.DataFrame)->None:
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m')
    df['month'] = pd.to_datetime(df['month'], format='%m').dt.month_name().str[:3]

def value_per_date(df:pd.DataFrame)->sns.lineplot:
    convert_to_month(df)
    gruped_df = df[["Value", "month"]].groupby("month").sum().reset_index()
    gruped_df.sort_values(by=['month'], inplace = True)
    fig = px.line(gruped_df, x="month", y="Value", title="Value per date")
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def get_top_items(df: pd.DataFrame, top_n: int) -> list:
    mock_data_tbl_rows = df.to_dict(orient="records")
    top_items_list = [x["id"] for x in sorted(
        mock_data_tbl_rows, key=lambda x: x["Value"], reverse=True)][:top_n]
    return top_items_list

def main():

    args = parse_args()
    csv_file_path = args.csv_file_input
    output_filename = args.output_filename
    top_n = args.top_items

    if not OUTPUT_FOLDER_PATH.exists():
        OUTPUT_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

    template = jinja2.Environment(
        loader = jinja2.FileSystemLoader(TEMPLATE_FOLDER_PATH), 
        autoescape=jinja2.select_autoescape
    ).get_template("report.html")

    today_str = dt.datetime.now().strftime(DATE_FORMAT)
    df = pd.read_csv(csv_file_path)

    top_items_list = get_top_items(df, top_n)
    bar_chart_html = create_bar_chart_vpc(df)
    line_plot_html = value_per_date(df)

    with open(TEMPLATE_FOLDER_PATH / "logo.png", "rb") as f:
        logo_img = base64.b64encode(f.read()).decode()
    
    context = {
        "report_dt_str": today_str,
        "mock_data_tbl_rows": df.to_dict(orient="records"),
        "top_items_rows": top_items_list,
        "v_p_c_bar_chart_html": bar_chart_html,
        "v_p_d_line_plot_html": line_plot_html,
        "logo_img": logo_img,
    }

    reportText = template.render(context)

    output_path = OUTPUT_FOLDER_PATH / output_filename
    with open(output_path, mode="w", encoding="utf-8") as f:
        f.write(reportText)

    print(f"Report save to: {output_path}")

if __name__ == "__main__":
    main()