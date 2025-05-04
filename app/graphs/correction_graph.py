from typing import Dict, Any, TypedDict
from langgraph.graph import Graph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import os
import json
import logging

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

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0
    )

    def analyze_error(state: GraphState) -> GraphState:
        """Analyze the SQL error and determine correction strategy"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a SQL debugging expert for Trino. Analyze the error and suggest corrections.

Consider:
1. Syntax errors (especially semicolons - Trino doesn't use them)
2. Table/column name mismatches
3. Join conditions
4. Data type mismatches
5. Aggregation issues
6. Trino-specific syntax requirements

Common Trino issues:
- No semicolons at the end of queries
- Proper use of fully qualified table names (catalog.schema.table)
- LIMIT clause syntax

Provide a specific correction strategy."""),
            HumanMessage(content=f"""
Original query: {state['query']}
SQL: {state['sql']}
Error: {state['error']}
Schema: {json.dumps(state['schema'], indent=2)}

What's wrong and how should we fix it?""")
        ])

        formatted_prompt = prompt.format_messages()
        response = llm.invoke(formatted_prompt)
        state['correction_strategy'] = response.content
        return state

    def correct_sql(state: GraphState) -> GraphState:
        """Correct the SQL based on the error analysis"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a SQL expert. Correct the SQL query based on the error analysis.

Rules:
1. Fix the specific error identified
2. Maintain the original query intent
3. Use proper Trino SQL syntax
4. Ensure all table references are fully qualified
5. Return only the corrected SQL query
6. Do not include markdown formatting, just the raw SQL
7. DO NOT use semicolons at the end of queries - Trino doesn't allow them
8. Make sure LIMIT is included to prevent overwhelming results"""),
            HumanMessage(content=f"""
Original query: {state['query']}
Failed SQL: {state['sql']}
Error: {state['error']}
Correction strategy: {state['correction_strategy']}
Schema: {json.dumps(state['schema'], indent=2)}

Provide the corrected SQL query:""")
        ])

        formatted_prompt = prompt.format_messages()
        response = llm.invoke(formatted_prompt)

        corrected_sql = response.content.strip()

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

        # Check for semicolons (Trino doesn't like them)
        if ';' in sql and not sql.endswith('LIMIT 100'):
            state['validation_error'] = "Query contains semicolons which Trino doesn't support"
            return state

        # Check for required table references
        if 'nps_db.public.nps_feedback' not in sql and 'products_db.public.products' not in sql:
            state['validation_error'] = "Missing proper table references"
            return state

        state['validation_passed'] = True
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