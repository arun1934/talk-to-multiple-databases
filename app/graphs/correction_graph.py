from typing import Dict, Any, TypedDict
from langgraph.graph import Graph, END
from langchain_core.messages import SystemMessage, HumanMessage
import litellm
import json
import logging

# Import config
from app.config import LLM

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    query: str
    sql: str
    error: str
    schema: Dict[str, Any]
    corrected_sql: str
    attempts: int
    max_attempts: int
    final_result: Dict[str, Any]


def create_correction_graph():
    """Create a graph for SQL query correction"""

    # Initialize LiteLLM directly
    litellm.api_key = LLM["api_key"]
    litellm.api_base = LLM["api_base"]

    # Set custom headers if provided
    if LLM["auth_header"]:
        litellm.headers = {"Authorization": LLM["auth_header"]}

    # Store model name and temperature for later use
    model = LLM["model"]
    temperature = LLM["generation_temperature"]

    def correct_sql(state: GraphState) -> GraphState:
        """Correct the SQL based on the error analysis"""
        prompt = f"""You are an SQL expert specializing in NPS (Net Promoter Score) analytics. Correct the SQL query based on the error analysis.

    # NPS Domain Knowledge
    Net Promoter Score (NPS) is a customer loyalty metric with specific calculation requirements:
    - Promoters: CAST(p_rating AS INTEGER) BETWEEN 9 AND 10
    - Passives: CAST(p_rating AS INTEGER) BETWEEN 7 AND 8
    - Detractors: CAST(p_rating AS INTEGER) BETWEEN 0 AND 6
    - NPS calculation: (COUNT(CASE WHEN CAST(p_rating AS INTEGER) BETWEEN 9 AND 10 THEN 1 END)::NUMERIC / NULLIF(COUNT(*),0) - 
                       COUNT(CASE WHEN CAST(p_rating AS INTEGER) BETWEEN 0 AND 6 THEN 1 END)::NUMERIC / NULLIF(COUNT(*),0)) * 100

    # PostgreSQL Function Requirements
    1. ROUND function - MUST use with NUMERIC type:
       - Correct: ROUND(CAST(expression AS NUMERIC), 2)
       - Alternative: CAST(expression AS NUMERIC(10,2))
    2. Division safety with NULLIF to prevent division by zero errors
    3. Proper casting for mathematical operations using NUMERIC instead of FLOAT
    
    **VERY IMPORTANT: Correct Column Names for public.hyb_nps_dtl:**
    - The primary date column is 'nps_date'.
    - The rating column is 'p_rating'.
    - If the failed SQL used 'survey_date', change it to 'nps_date'.
    - If the failed SQL used 'rating' for the score, change it to 'p_rating'.

    Rules:
    1. Fix the specific error identified. If it's a missing column error for a date or rating in hyb_nps_dtl, use 'nps_date' or 'p_rating' respectively.
    2. Maintain the original query intent.
    3. Use proper PostgreSQL syntax.
    4. Ensure all table references include the schema (public.table_name).
    5. Return only the corrected SQL query.
    6. Do not include markdown formatting, just the raw SQL.
    7. Include LIMIT to prevent overwhelming results.
    8. Common PostgreSQL fixes to consider:
       - For table names, use: public.hyb_nps_dtl, public.dm_empmast, public.hyb_order_detail
       - For numeric operations, use CAST(field AS INTEGER) or CAST(field AS NUMERIC)
       - For date operations, use CAST(date_field AS DATE) or date_field::DATE
    9. IMPORTANT: Check column existence in tables
       - p_areaname exists in hyb_order_detail but NOT in hyb_nps_dtl
       - If column not found error, either remove the column reference or use a join to get it from another table (unless it is 'survey_date' or 'rating' for hyb_nps_dtl, in which case correct it).
    10. For NPS-specific fixes:
       - Use explicit CAST when comparing ratings (CAST(p_rating AS INTEGER))
       - Ensure proper division by using NULLIF to avoid division by zero
       - For trend analysis, use date_trunc() with the appropriate time bucket
       - For sentiment analysis, check text operations on the p_comment field

    Original query: {state['query']}
    Failed SQL: {state['sql']}
    Error: {state['error']}
    Correction strategy: {state['correction_strategy']}
    Schema: {json.dumps(state['schema'], indent=2)}

    Provide the corrected SQL query:"""

        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )

        corrected_sql = response.choices[0].message.content.strip()

        # Clean the SQL query
        if corrected_sql.startswith("```sql"):
            corrected_sql = corrected_sql.replace("```sql", "").replace("```", "").strip()
        elif corrected_sql.startswith("```"):
            corrected_sql = corrected_sql.replace("```", "").strip()

        # Remove semicolon at the end if present
        if corrected_sql.endswith(';'):
            corrected_sql = corrected_sql[:-1].strip()

        state['corrected_sql'] = corrected_sql
        state['attempts'] = state.get('attempts', 0) + 1
        return state

    def validate_correction(state: GraphState) -> GraphState:
        """Validate the corrected SQL"""
        sql = state['corrected_sql']

        # Basic validation checks
        if not sql:
            state['validation_error'] = "Empty SQL query"
            return state

        # Check for semicolons (should be removed)
        if ';' in sql:
            state['validation_error'] = "Query contains semicolons which should be removed"
            return state

        # Check for required table references - case insensitive because we want to ensure the tables exist
        sql_lower = sql.lower()
        table_references = [
            'public.hyb_nps_dtl',
            'public.dm_empmast',
            'public.hyb_order_detail',
            'public.hyb_product_data'
        ]

        found_table = False
        for table in table_references:
            if table in sql_lower:
                found_table = True
                break

        if not found_table:
            state['validation_error'] = "Missing proper table references"
            return state

        state['validation_passed'] = True
        return state

    def analyze_error(state: GraphState) -> GraphState:
        """Analyze the SQL error and determine correction strategy"""
        prompt = f"""You are an SQL debugging expert specialized in NPS (Net Promoter Score) analytics for PostgreSQL. Analyze the error and suggest corrections.

    # NPS Domain Knowledge
    Net Promoter Score (NPS) is a customer loyalty metric ranging from -100 to +100:
    - Promoters: Customers who rated 9-10 (loyal enthusiasts who will refer others)
    - Passives: Customers who rated 7-8 (satisfied but unenthusiastic customers)
    - Detractors: Customers who rated 0-6 (unhappy customers who can damage brand)
    - NPS calculation requires proper casting of rating strings to integers

    # PostgreSQL-Specific Function Issues
    1. ROUND function in PostgreSQL requires numeric input (not double precision)
       - Use: ROUND(CAST(value AS NUMERIC), 2)
       - or: CAST(expression AS NUMERIC)::NUMERIC
    2. Ensure proper type handling for mathematical operations
       - CAST as NUMERIC instead of FLOAT for financial/percentage calculations
    
    Common issues when working with NPS data:
    1. Improper calculation of NPS percentages (requires proper CAST and NULLIF for division safety)
    2. Improper categorization of Promoters/Passives/Detractors
    3. Text field processing issues when analyzing comment sentiment
    4. Date formatting and truncation errors in trend analysis
    5. Joining issues between NPS feedback and order/product data
    6. Column existence issues - fields like p_areaname might exist in one table but not another.
       **CRITICAL: For public.hyb_nps_dtl, the main date column is 'nps_date' and the rating column is 'p_rating'.** 
       If the error is 'column does not exist' for a date or rating field, check if 'survey_date' or 'rating' was used instead of 'nps_date' or 'p_rating'.

    General PostgreSQL issues to consider:
    1. Syntax errors 
    2. Table/column name case sensitivity
    3. Join conditions
    4. Data type mismatches - most fields are stored as VARCHAR and need explicit casting:
       - For numeric operations (SUM, AVG, etc.), use CAST(field AS INTEGER) or CAST(field AS NUMERIC)
       - For date operations, use CAST(date_field AS DATE) or date_field::DATE
    5. Aggregation issues - can't apply numeric functions to string fields without casting
    6. GROUP BY requirements - columns in SELECT must be in GROUP BY or used in aggregate functions
    7. Schema qualification - use public.table_name format
    8. Proper quoting of date literals (use DATE '2025-01-01' format or '2025-01-01'::DATE)

    Original query: {state['query']}
    SQL: {state['sql']}
    Error: {state['error']}
    Schema: {json.dumps(state['schema'], indent=2)}

    What's wrong and how should we fix it? If the error is 'column does not exist', pay close attention to the schema and common mistakes like using 'survey_date' or 'rating' for the hyb_nps_dtl table. Be specific about the NPS-related issue if applicable."""
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        state['correction_strategy'] = response.choices[0].message.content
        return state

    def should_retry(state: GraphState) -> str:
        """Determine if we should retry the correction"""
        if state.get('validation_passed', False):
            return "success"

        if state.get('attempts', 0) >= state.get('max_attempts', 3):
            return "failure"

        return "retry"

    def prepare_final_result(state: GraphState) -> GraphState:
        """Prepare the final result"""
        if state.get('validation_passed', False):
            state['final_result'] = {
                'success': True,
                'sql_query': state['corrected_sql'],
                'attempts': state.get('attempts', 0)
            }
        else:
            state['final_result'] = {
                'success': False,
                'error': state.get('validation_error', 'Failed to correct SQL after multiple attempts'),
                'attempts': state.get('attempts', 0)
            }
        return state

    # Build the graph
    workflow = Graph()

    # Add nodes
    workflow.add_node("analyze_error", analyze_error)
    workflow.add_node("correct_sql", correct_sql)
    workflow.add_node("validate_correction", validate_correction)
    workflow.add_node("prepare_final_result", prepare_final_result)

    # Add edges
    workflow.add_edge("analyze_error", "correct_sql")
    workflow.add_edge("correct_sql", "validate_correction")

    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_correction",
        should_retry,
        {
            "retry": "analyze_error",
            "success": "prepare_final_result",
            "failure": "prepare_final_result"
        }
    )

    workflow.add_edge("prepare_final_result", END)

    # Set entry point
    workflow.set_entry_point("analyze_error")

    return workflow.compile()