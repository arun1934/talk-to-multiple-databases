from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ChartConfig(BaseModel):
    title: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[Any] = None  # Can be str or List[str] for stacked/grouped
    series: Optional[Any] = None  # Can be str or List[str]
    labels_col: Optional[str] = None # For pie/donut
    values_col: Optional[str] = None # For pie/donut/kpi
    value_col: Optional[str] = None # For heatmap intensity
    subtitle: Optional[str] = None
    legend: Optional[bool] = True
    colors: Optional[List[str]] = None
    # Add any other relevant config fields your charts might use
    # e.g., is_stacked: Optional[bool] = False, fill: Optional[bool] = False (for area)

class DataTransformation(BaseModel):
    required: bool = False
    type: Optional[str] = None # e.g., "aggregate", "time_series", "pivot"
    instructions: List[str] = Field(default_factory=list)

class VisualizationRecommendation(BaseModel):
    visualization_type: str
    config: ChartConfig
    reasoning: Optional[str] = None
    data_transformation: Optional[DataTransformation] = None

# Example usage (optional, for testing):
if __name__ == "__main__":
    # Example for a bar chart
    bar_config = ChartConfig(
        title="Sales per Region",
        x_axis="region",
        y_axis="total_sales"
    )
    bar_recommendation = VisualizationRecommendation(
        visualization_type="bar_chart",
        config=bar_config,
        reasoning="Bar chart is suitable for comparing sales across different regions."
    )
    print(bar_recommendation.model_dump_json(indent=2))

    # Example for a pie chart
    pie_config = ChartConfig(
        title="NPS Distribution",
        labels_col="nps_category",
        values_col="count"
    )
    pie_recommendation = VisualizationRecommendation(
        visualization_type="pie_chart",
        config=pie_config,
        reasoning="Pie chart shows proportions of NPS categories.",
        data_transformation=DataTransformation(
            required=False,
            instructions=["Ensure data is aggregated by nps_category with counts."]
        )
    )
    print(pie_recommendation.model_dump_json(indent=2)) 