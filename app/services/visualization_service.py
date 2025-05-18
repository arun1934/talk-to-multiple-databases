from typing import Dict, Any, List, Optional, Tuple
import os
import litellm
import json
import logging
from dateutil import parser as date_parser
from datetime import datetime, date
from decimal import Decimal

from app.config import LLM
from app.models.visualization_models import VisualizationRecommendation, ChartConfig

logger = logging.getLogger(__name__)


class VisualizationService:
    def __init__(self):
        # Configure LiteLLM directly
        litellm.api_key = LLM["api_key"]
        litellm.api_base = LLM["api_base"]

        # Set custom headers if provided
        if LLM["auth_header"]:
            litellm.headers = {"Authorization": LLM["auth_header"]}

        # Store model name and temperature for later use
        self.model = LLM["model"]
        self.temperature = LLM["summary_temperature"]
        self.llm_model = LLM["model"]

    async def recommend_visualization(
        self, question: str, sql_query: str, results: Dict[str, Any]
    ) -> VisualizationRecommendation:
        """Recommend appropriate visualization based on query results"""
        try:
            # Log endpoint hit and essential parts of the request
            logger.info(f"[VISUALIZATION SVC] recommend_visualization endpoint hit.")
            logger.info(f"[VISUALIZATION SVC] Question: {question[:200]}...") # Log first 200 chars
            logger.info(f"[VISUALIZATION SVC] SQL Query: {sql_query[:200]}...") # Log first 200 chars
            # Avoid logging full results if they are very large, log summary instead
            results_preview = {
                "columns": results.get("columns"),
                "num_rows": len(results.get("rows", [])),
                "first_row_preview": results.get("rows", [None])[0]
            }
            logger.info(f"[VISUALIZATION SVC] Results Preview: {json.dumps(results_preview)}")

            if not results or not results.get("rows"):
                logger.warning("[VISUALIZATION SVC] No results data provided (expected 'rows' key in input), returning default table recommendation.")
                # Try to get columns from results if rows are missing, for the x-axis fallback
                cols_for_fallback = results.get("columns", [None])
                x_axis_fallback = cols_for_fallback[0] if cols_for_fallback else None
                return VisualizationRecommendation(
                    visualization_type="table",
                    config=ChartConfig(title=question or "Query Results", x_axis=x_axis_fallback),
                    reasoning="No data rows provided for visualization.",
                    data_transformation=None
                )

            # Prepare data summary for LLM
            data_summary = self._create_data_summary(results)
            logger.info(f"[VISUALIZATION SVC] Data summary for LLM: {json.dumps(data_summary, indent=2)}")

            prompt = f"""You are a data visualization expert. Based on the SQL query, the user's question, and a summary of the results, recommend the most appropriate visualization type and its configuration.

User Question: {question}
SQL Query:
{sql_query}

Data Summary:
{json.dumps(data_summary, indent=2)}

Available visualization types:
1. table - Default for raw data, or when other charts are not suitable. Good for mixed data types or many columns.
   - Config: {{ "title": "...", "columns_to_display": ["col1", "col2"] }} (optional, defaults to all)
2. bar_chart - Comparing values across categories.
   - Config: {{ "title": "...", "x_axis": "categorical_col", "y_axis": "numerical_col", "series": "optional_grouping_col" }}
3. line_chart - Showing trends over time or continuous data.
   - Config: {{ "title": "...", "x_axis": "time_or_continuous_col", "y_axis": "numerical_col", "series": "optional_grouping_col" }}
4. pie_chart - Showing proportions of a whole (few categories, <=7).
   - Config: {{ "title": "...", "labels_col": "categorical_col", "values_col": "numerical_col" }}
5. scatter_plot - Showing relationships between two numerical variables.
   - Config: {{ "title": "...", "x_axis": "numerical_col_1", "y_axis": "numerical_col_2", "series": "optional_grouping_col" }}
6. area_chart - Like line chart, but emphasizes volume/magnitude.
   - Config: {{ "title": "...", "x_axis": "time_or_continuous_col", "y_axis": "numerical_col", "series": "optional_grouping_col" }}
7. horizontal_bar - Like bar chart, but for long category labels or many categories.
   - Config: {{ "title": "...", "x_axis": "numerical_col", "y_axis": "categorical_col", "series": "optional_grouping_col" }}
8. stacked_bar - Comparing parts to a whole across categories.
    - Config: {{ "title": "...", "x_axis": "categorical_col", "y_axis": ["num_col1", "num_col2"], "series": "optional_grouping_col_for_x_axis_categories" }} or {{ "x_axis": "categorical_col", "y_axis": "numerical_col_values", "series": "categorical_col_for_stacking_segments"}}
9. donut_chart - Similar to pie, but with center cutout (few categories, <=7).
   - Config: {{ "title": "...", "labels_col": "categorical_col", "values_col": "numerical_col" }}
10. heatmap - Good for showing intensity across two dimensions (e.g., categories or time). Expects config with x_axis, y_axis, and value_col for intensity.
    - Config: {{ "title": "...", "x_axis": "col_for_x", "y_axis": "col_for_y", "value_col": "col_for_intensity_value" }}
11. kpi - Displaying a single key metric value.
    - Config: {{ "title": "...", "value_col": "numerical_col_with_single_value", "subtitle": "optional_description_or_comparison_metric" }}


Consider:
-- Number and types of columns (e.g., categorical, numerical, time-series based on _infer_data_type).
-- Data patterns (trends, distributions, proportions, correlations, rankings).
-- Cardinality of categorical data: If a categorical column has many unique values (e.g., >15-20), a standard bar chart might be cluttered. Consider a horizontal bar chart for better label readability or a table view.
-- Number of data points: Pie/Donut charts are best for few categories (<=10). Line charts are good for many data points if x-axis is ordered (e.g., time).
-- Query Intent: What is the user trying to achieve? (e.g., comparison, trend, distribution). If the query is "Show me raw numbers for X", a table might be best.
-- Axes: Ensure x_axis, y_axis, labels_col, values_col, value_col are appropriate for the chart type and exist in the data_summary.columns.
-- For 'series' or grouping, it should generally be a categorical column.
-- If data has only one row and multiple columns, a table or KPI (if one primary metric) is often best. A bar chart of one bar per column might also work if all are numeric.
-- If data has many columns with diverse types, a table is usually safest.

Specific Guidance:
- Use line_chart or area_chart for time-series data showing trends (column type 'datetime' or 'year' on x-axis).
  - **For time-series data (e.g., trends over time identified by a 'datetime', 'date', or 'year' type x-axis column), STRONGLY PREFER 'line_chart'.**
  - The 'x_axis' should be the time-based column.
  - For 'y_axis':
    - If there is one primary numeric column (e.g., 'nps_score', 'sales_amount', 'count'), use that single column name.
    - If there are multiple numeric columns and the user's question doesn't specify which one to plot, pick the most relevant or the first numeric column after the date column as the primary 'y_axis'.
    - If appropriate, you can specify multiple numeric columns as a list for 'y_axis' (e.g., `"y_axis": ["metric1", "metric2"]`) for a multi-line chart. The frontend will attempt to plot these.
- Use bar_chart for comparing distinct categories. If category names are long or there are many categories, prefer horizontal_bar.
- Use pie_chart or donut_chart for showing parts of a whole (proportions) with a small number of categories (typically 3-7). If the user query explicitly asks for "distribution of [categories]", "proportion of [categories]", or "share of [categories]" and the result has one categorical column and one numerical column with few rows, STRONGLY prefer pie_chart or donut_chart.
- Use scatter_plot for correlations between two numerical axes. If one axis is time, prefer line_chart.
- Use heatmap when you have three dimensions: two categorical (or binnable numerical) for axes, and one numerical for intensity/color.
- Use KPI for single, important numbers. If the result is a single row with one primary numeric value, consider KPI.
- Default to 'table' if no other chart type is clearly superior or if the data structure is complex (e.g. many columns, mixed types, no clear patterns).

**CRITICAL FOR AXES AND SERIES:**
- When using `series` for grouping or stacking (e.g., in bar, horizontal_bar, line, area, stacked_bar charts):
  - For `bar_chart`, `stacked_bar`, `line_chart`, `area_chart`: `x_axis` is the primary categorical grouping, `y_axis` **MUST BE A SINGLE STRING** naming the numerical value column, and `series` is the secondary categorical column for grouping/stacking within each `x_axis` category.
  - For `horizontal_bar`: `y_axis` is the primary categorical grouping, `x_axis` **MUST BE A SINGLE STRING** naming the numerical value column, and `series` is the secondary categorical column for grouping/stacking within each `y_axis` category.
- If you recommend a `data_transformation` to pivot data from wide to long (e.g., creating columns like 'CategoryType' and 'Value'), ensure the `x_axis`, `y_axis`, and `series` in the `config` refer to these NEWLY CREATED column names from the long format, not the original wide format columns.
  - Example Transformation: Original wide data `(region, promoters, passives, detractors)` transformed to long data `(region, NPS_Category, count)`.
    For a horizontal_bar showing this: `y_axis` would be "region", `x_axis` would be "count", and `series` would be "NPS_Category".
    **DO NOT put multiple original column names (e.g., `["promoters", "passives"]`) into `x_axis` or `y_axis` in the config if you are also recommending a transformation to a long format with a series column.**

Output JSON with 'visualization_type', 'config' (JS object with keys like title, x_axis, y_axis, series, labels_col, values_col, value_col), and 'reasoning' (brief explanation).
Optionally, include 'data_transformation' object with 'required': boolean and 'instructions': [strings] if data needs minor reshaping (e.g., pivoting, aggregation hint for LLM that generates SQL next time, not for client to do). Example: {{ "required": false, "instructions": ["Consider aggregating by month for a clearer trend."] }}

Example for pie chart:
User Question: "What is the distribution of product categories?"
Data Summary: {{ "num_rows": 3, "num_cols": 2, "columns": [{{"name": "category", "type": "categorical"}}, {{"name": "count", "type": "numeric"}}] }}
Output:
{{
    "visualization_type": "pie_chart",
    "config": {{
        "title": "Distribution of Product Categories",
        "labels_col": "category",
        "values_col": "count"
    }},
    "reasoning": "Pie chart is suitable for showing proportions of a few categories.",
    "data_transformation": null
}}

Example for bar chart:
User Question: "Sales per region"
Data Summary: {{ "num_rows": 5, "num_cols": 2, "columns": [{{"name": "region", "type": "categorical"}}, {{"name": "total_sales", "type": "numeric"}}] }}
Output:
{{
    "visualization_type": "bar_chart",
    "config": {{
        "title": "Sales per Region",
        "x_axis": "region",
        "y_axis": "total_sales"
    }},
    "reasoning": "Bar chart for comparing sales across different regions.",
    "data_transformation": null
}}

Ensure that all column names used in the 'config' (e.g., for x_axis, y_axis, series, labels_col, values_col, value_col) EXACTLY MATCH the column names provided in the Data Summary. Be very careful with this.
If data_summary shows num_rows: 0, always recommend 'table' with a message.
If the user asks for "raw data" or "show table", always recommend 'table'.
Provide your response as a single, valid JSON object.
"""
            # logger.debug(f"Prompt for LLM: {prompt}")
            response = await litellm.acompletion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, # Low temperature for more deterministic recommendations
                response_format={"type": "json_object"}
            )
            response_content = response.choices[0].message.content
            logger.info(f"[VISUALIZATION SVC] Raw LLM response for visualization: {response_content[:1000]}...") # Log more chars

            try:
                visualization_config_dict = json.loads(response_content)
                logger.info(f"[VISUALIZATION SVC] Parsed LLM response: {json.dumps(visualization_config_dict, indent=2)}")

                is_valid, error_msg = self._validate_recommendation(visualization_config_dict, data_summary)
                if not is_valid:
                    logger.error(f"[VISUALIZATION SVC] LLM recommendation failed validation: {error_msg}. LLM Output: {response_content}")
                    # Fallback to table with the error message as reasoning or part of title
                    fallback_reason = f"Invalid recommendation from LLM: {error_msg}. Defaulting to table."
                    chart_config = ChartConfig(title=f"Data (Recommendation Error)", x_axis=data_summary["columns"][0]["name"] if data_summary["columns"] else None)
                    vis_rec = VisualizationRecommendation(visualization_type="table", config=chart_config, reasoning=fallback_reason, data_transformation=None)
                else:
                    logger.info("[VISUALIZATION SVC] LLM recommendation PASSED validation.")
                    chart_config = ChartConfig(**visualization_config_dict.get("config", {}))
                    vis_rec = VisualizationRecommendation(
                        visualization_type=visualization_config_dict["visualization_type"],
                        config=chart_config,
                        reasoning=visualization_config_dict.get("reasoning", ""),
                        data_transformation=visualization_config_dict.get("data_transformation")
                    )

            except json.JSONDecodeError as e:
                logger.error(f"[VISUALIZATION SVC] Failed to parse LLM JSON response for visualization: {e}. Response: {response_content}", exc_info=True)
                chart_config = ChartConfig(title="Data (JSON Error)", x_axis=data_summary["columns"][0]["name"] if data_summary["columns"] else None)
                vis_rec = VisualizationRecommendation(visualization_type="table", config=chart_config, reasoning=f"Error parsing LLM response: {e}", data_transformation=None)
            
            return vis_rec

        except Exception as e:
            logger.error(f"[VISUALIZATION SVC] Error in recommend_visualization: {e}", exc_info=True)
            # Fallback to a table if any error occurs
            # Try to get columns from results if rows are missing, for the x-axis fallback
            cols_for_fallback = results.get("columns", [None])
            x_axis_fallback = cols_for_fallback[0] if cols_for_fallback else None
            return VisualizationRecommendation(
                visualization_type="table",
                config=ChartConfig(title="Data (Error)", x_axis=x_axis_fallback),
                reasoning=f"An unexpected error occurred: {str(e)}",
                data_transformation=None
            )

    def _create_data_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the result data for LLM analysis"""
        # The 'results' object here is expected to be the tableData structure: {"columns": [], "rows": []}
        # It might also contain a "success" key from the original SQL execution, but we prioritize "columns" and "rows".

        columns = results.get("columns", [])
        data = results.get("rows", []) # MODIFIED: "results" to "rows"

        if not columns and not data:
             # If it was a failed SQL query object that still made it here.
            if "success" in results and not results["success"]:
                 return {"error": results.get("error", "SQL query execution failed and no data available.")}
            return {"error": "No columns or rows found in the provided results."}


        summary = {
            "column_count": len(columns),
            "row_count": len(data),
            "columns": []
        }

        for i, col_name in enumerate(columns): # MODIFIED: Iterate by col_name from columns list
            # Ensure row has enough elements before trying to access by index i
            col_data = [row[i] for row in data if isinstance(row, (list, tuple)) and i < len(row)]
            
            col_summary = {
                "name": col_name, # MODIFIED: Use col_name directly
                "data_type": self._infer_data_type(col_data),
                "unique_values": len(set(str(x) for x in col_data if x is not None)),
                "null_count": sum(1 for x in col_data if x is None),
                "sample_values": list(set(str(x) for x in col_data[:5] if x is not None))
            }

            # Add numeric statistics if applicable
            if col_summary["data_type"] in ["integer", "float"]:
                numeric_values = [x for x in col_data if isinstance(x, (int, float))]
                if numeric_values:
                    col_summary["min"] = min(numeric_values)
                    col_summary["max"] = max(numeric_values)
                    col_summary["avg"] = sum(numeric_values) / len(numeric_values)

            summary["columns"].append(col_summary)

        return summary

    def _infer_data_type(self, values: List[Any]) -> str:
        """Infer the data type of a column from its values"""
        non_null_values = [v for v in values if v is not None]
        if not non_null_values:
            return "unknown"

        # Attempt to parse as datetime first
        datetime_count = 0
        for v in non_null_values[:10]: # Sample first 10 non-null values
            if isinstance(v, (datetime, date)):
                datetime_count += 1
                continue
            if isinstance(v, str):
                try:
                    date_parser.parse(v)
                    # Heuristic: if parsing succeeded and original string contains typical date separators or time patterns
                    if any(sep in v for sep in ['-', '/', ':']) or ('AM' in v.upper() or 'PM' in v.upper()):
                        datetime_count += 1
                except (ValueError, TypeError, OverflowError):
                    pass
        if datetime_count > 5: # If more than half of the sample parsed as datetime
            return "datetime"

        # Check for numeric types (integer or float)
        numeric_count = 0
        potential_year_count = 0
        for v in non_null_values:
            if isinstance(v, (int, float, Decimal)):
                numeric_count += 1
                # Heuristic for Year (e.g., 2023, 2024) - avoid treating as general numeric if it looks like a year
                if isinstance(v, int) and 1900 <= v <= 2100:
                    potential_year_count +=1
            elif isinstance(v, str) and v.replace('.', '', 1).isdigit(): # handles "123", "123.45"
                 numeric_count += 1
                 if v.isdigit() and 1900 <= int(v) <= 2100: # String year check
                     potential_year_count +=1


        if numeric_count == len(non_null_values):
            # If all numeric values look like years, and the column name hints at it, prefer 'year' or 'categorical'
            # For now, let's lean towards numeric if all are numeric, refinement can be done in _create_data_summary
            if potential_year_count == len(non_null_values):
                 return "year" # or "categorical" if context suggests, but "year" is more specific
            return "numeric"

        # Default to categorical
        return "categorical"

    def _validate_recommendation(self, recommendation: Dict[str, Any], data_summary: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        viz_type = recommendation.get("visualization_type")
        config = recommendation.get("config", {})
        
        logger.debug(f"[VISUALIZATION VALIDATION] Validating: {recommendation} against summary: {data_summary}")

        if not viz_type:
            return False, "Missing 'visualization_type'."

        available_types = [
            "bar_chart", "line_chart", "pie_chart", "scatter_plot", "table", 
            "area_chart", "horizontal_bar", "stacked_bar", "donut_chart", "heatmap", "kpi"
        ]
        if viz_type not in available_types:
            return False, f"Invalid 'visualization_type': {viz_type}. Must be one of {available_types}."

        if not isinstance(config, dict):
            return False, "'config' must be a dictionary."
            
        if not config.get("title"):
            logger.warning("[VISUALIZATION VALIDATION] Missing 'title' in config, will use a default.")
            # Not a critical error, can be defaulted on frontend.

        column_names = [col["name"] for col in data_summary.get("columns", [])]

        required_axes = {
            "bar_chart": ["x_axis", "y_axis"],
            "line_chart": ["x_axis", "y_axis"],
            "horizontal_bar": ["x_axis", "y_axis"], # x usually categories, y values
            "stacked_bar": ["x_axis", "y_axis"], # y_axis could be multiple series
            "area_chart": ["x_axis", "y_axis"],
            "scatter_plot": ["x_axis", "y_axis"],
            "heatmap": ["x_axis", "y_axis", "value_col"],
            "pie_chart": ["labels_col", "values_col"], # More descriptive for pie/donut
            "donut_chart": ["labels_col", "values_col"]
        }
        
        if viz_type in required_axes:
            for axis in required_axes[viz_type]:
                axis_val = config.get(axis)
                if not axis_val:
                    # For stacked_bar, y_axis might be a list of columns.
                    if viz_type == "stacked_bar" and axis == "y_axis" and isinstance(config.get("series"), list) and config.get("series"):
                        continue # y_axis itself isn't specified but series are, which is fine.

                    return False, f"Missing '{axis}' in config for {viz_type}."
                
                # If a data transformation is required, skip strict column validation for axes/series involved in transformation,
                # as they might refer to columns created by the transformation.
                data_transformation_field = recommendation.get("data_transformation")
                data_transformation_required = isinstance(data_transformation_field, dict) and data_transformation_field.get("required", False)

                # If axis_val is a single column string
                if isinstance(axis_val, str) and not data_transformation_required and axis_val not in column_names:
                    return False, f"Column '{axis_val}' specified for '{axis}' not found in data columns: {column_names}."
                # If axis_val is a list (e.g. for y_axis in stacked_bar if LLM returns list for y_axis directly)
                elif isinstance(axis_val, list) and not data_transformation_required:
                    for col in axis_val:
                        if col not in column_names:
                             return False, f"Column '{col}' in '{axis}' list not found in data columns: {column_names}."
        
        # Validate series column if present
        series_col = config.get("series")
        data_transformation_field = recommendation.get("data_transformation") # Check again for series context
        data_transformation_required = isinstance(data_transformation_field, dict) and data_transformation_field.get("required", False)

        if series_col and not data_transformation_required: # Only validate if no transformation is pending that might create this column
            if isinstance(series_col, str) and series_col not in column_names:
                return False, f"Column '{series_col}' specified for 'series' not found in data columns: {column_names}."
            elif isinstance(series_col, list): # For multi-series charts like stacked_bar
                for col in series_col:
                    if col not in column_names:
                        return False, f"Column '{col}' in 'series' list not found in data columns: {column_names}."

        # Specific check for KPI
        if viz_type == "kpi":
            if not config.get("value_col"):
                return False, "Missing 'value_col' in config for kpi."
            if config.get("value_col") not in column_names:
                 return False, f"Column '{config.get('value_col')}' specified for 'value_col' in KPI not found in data columns: {column_names}."

        return True, None

    def _suggest_data_transformation(self, config: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest data transformations needed for visualization"""
        viz_type = config.get("visualization_type")
        transformation = {
            "required": False,
            "type": None,
            "instructions": []
        }

        if viz_type in ["pie_chart", "donut_chart"]:
            transformation["required"] = True
            transformation["type"] = "aggregate"
            transformation["instructions"] = [
                "Group by category column",
                "Sum or count values",
                "Calculate percentages"
            ]

        elif viz_type == "line_chart":
            # Check if x-axis is time-based
            x_axis = config.get("config", {}).get("x_axis")
            if x_axis and any(time_word in x_axis.lower() for time_word in ["date", "time", "year", "month"]):
                transformation["required"] = True
                transformation["type"] = "time_series"
                transformation["instructions"] = [
                    "Parse dates",
                    "Sort by date",
                    "Handle missing time periods"
                ]

        return transformation

    def _fallback_visualization(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Provide a fallback visualization when recommendation fails"""
        return {
            "visualization_type": "table",
            "config": {
                "title": "Query Results",
                "subtitle": "Displaying data in tabular format",
                "pagination": True,
                "page_size": 10
            },
            "reasoning": "Defaulting to table view for data display"
        }