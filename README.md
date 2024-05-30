# Astronomer SnowPatrol Plugin

The Astronomer SnowPatrol Plugin is an Airflow plugin designed to enhance your Snowflake data operations within Airflow.
This plugin installs a policy in your Airflow environment adding query tags to all Airflow Snowflake sql queries.

The Plugin will add the following Sowflake query tags to any Snowflake-related Airflow Operators:

- `dag_id`
- `task_id`
- `run_id`
- `logical_date`
- `started`
- `operator`

Once the Plugin is installed, Tags are automatically sent to Snowflake allowing you to query the QUERY_HISTORY table and
identify all queries run by a given Airflow DAG or Task.
Snowflake Costs can be then attributed to specific DAGs and Tasks.

## Features

- **Query Tagging**: Automatically adds query tags to Snowflake operators within Airflow DAGs.
- **Enhanced Monitoring**: Enables better tracking and monitoring of Snowflake queries executed through Airflow.
- **Cluster Policy**: Easily integrate with your existing Airflow clusters and workflows. No changes needed to your
  existing DAGs.

**NOTE**: query tags are added to every Operator inheriting from the BaseSQLOperator.
If other third party tools are used and do not make use of this Operator, query tags will not be added automatically.

## Installation

You can install the Astronomer SnowPatrol Plugin via pip:

```bash
pip install astronomer-snowpatrol-plugin
```

## Usage

You can use the `SnowflakeOperator` or any other BaseSQLOperator-related operators in your Airflow DAGs as usual.
The plugin will automatically add the query tags earlier mentioned.

See the following Airflow documentation pages for supported SQL Operators:
https://airflow.apache.org/docs/apache-airflow-providers-snowflake/stable/operators/snowflake.html
[Airflow Documentation](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/_api/airflow/providers/common/sql/operators/sql/index.html)

### Example

Given the following DAG, query tags will be added at runtime every time the SnowflakeOperator is run.

```python
from airflow import DAG
from airflow.operators.snowflake_operator import SnowflakeOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2022, 1, 1),
}

dag = DAG(
    'my_snowflake_dag',
    default_args=default_args,
    description='A simple DAG to demonstrate SnowflakeOperator',
    schedule_interval='@once',
)

with dag:
    task = SnowflakeOperator(
        task_id='snowflake_query',
        sql="SELECT * FROM my_table",
        snowflake_conn_id="snowflake_default",
        warehouse="my_warehouse",
        database="my_database",
        schema="my_schema",
    )

task
```

## Tracking Snowflake Costs for all Airflow DAGs

You can use the following sql query to get a better understanding of your Airflow-related Snowflake costs:

```sql
// To know your effective credit cost, go to the `Admin` menu on the left and click on `Cost Management`. Copy the value from `Compute price/credit`.
SET SNOWFLAKE_CREDIT_COST=1.88;
// How many days you want to include
SET NUMBER_OF_DAYS=30;

WITH warehouse_sizes AS (
	SELECT 'X-Small'  AS warehouse_size, 1   AS credits_per_hour UNION ALL
	SELECT 'Small'    AS warehouse_size, 2   AS credits_per_hour UNION ALL
	SELECT 'Medium'   AS warehouse_size, 4   AS credits_per_hour UNION ALL
	SELECT 'Large'    AS warehouse_size, 8   AS credits_per_hour UNION ALL
	SELECT 'X-Large'  AS warehouse_size, 16  AS credits_per_hour UNION ALL
	SELECT '2X-Large' AS warehouse_size, 32  AS credits_per_hour UNION ALL
	SELECT '3X-Large' AS warehouse_size, 64  AS credits_per_hour UNION ALL
	SELECT '4X-Large' AS warehouse_size, 128 AS credits_per_hour
), query_history AS (
	SELECT
		qh.query_id,
		qh.query_text,
		qh.database_name,
		qh.schema_name,
		qh.warehouse_name,
		qh.warehouse_size,
		qh.warehouse_type,
		qh.user_name,
		qh.role_name,
		DATE(qh.start_time) AS execution_date,
		qh.error_code,
		qh.execution_status,
		qh.execution_time/(1000) AS execution_time_sec,
		qh.total_elapsed_time/(1000) AS total_elapsed_time_sec,
		qh.rows_deleted,
		qh.rows_inserted,
		qh.rows_produced,
		qh.rows_unloaded,
		qh.rows_updated,
		TRY_PARSE_JSON(qh.query_tag):dag_id::varchar AS airflow_dag_id,
		TRY_PARSE_JSON(qh.query_tag):task_id::varchar AS airflow_task_id,
		TRY_PARSE_JSON(qh.query_tag):run_id::varchar AS airflow_run_id,
		TRY_TO_TIMESTAMP(TRY_PARSE_JSON(qh.query_tag):logical_date::varchar) AS airflow_logical_date,
		TRY_TO_TIMESTAMP(TRY_PARSE_JSON(qh.query_tag):started::varchar) AS airflow_started,
		TRY_PARSE_JSON(qh.query_tag):operator::varchar AS airflow_operator,
		qh.execution_time/(1000*60*60)*wh.credits_per_hour AS credit_cost,
		credit_cost * $SNOWFLAKE_CREDIT_COST AS dollar_cost
	FROM snowflake.account_usage.query_history AS qh
	INNER JOIN warehouse_sizes AS wh
		ON qh.warehouse_size=wh.warehouse_size
	WHERE qh.start_time >= DATEADD(DAY, -($NUMBER_OF_DAYS), CURRENT_DATE())
	AND qh.WAREHOUSE_ID > 0
)
SELECT query_text,
	warehouse_name,
	warehouse_size,
	warehouse_type,
	MAX(airflow_dag_id) AS airflow_dag_id,
	MAX(airflow_task_id) AS airflow_task_id,
	MAX(airflow_run_id) AS airflow_run_id,
	MAX(airflow_logical_date) AS airflow_logical_date,
	MAX(airflow_started) AS airflow_started,
	MAX(airflow_operator) AS airflow_operator,
	COUNT(query_id) AS execution_count,
	MAX(execution_date) AS first_execution_date,
	MIN(execution_date) AS last_execution_date,
	SUM(dollar_cost) AS total_dollar_cost
FROM query_history
GROUP BY query_text,
	warehouse_name,
	warehouse_size,
	warehouse_type
ORDER BY total_dollar_cost DESC
```

## Support

For any questions, issues, or feature requests related to the Astronomer SnowPatrol Plugin,
please [open an issue](https://github.com/astronomer/astronomer-snowpatrol-plugin/issues) on the GitHub repository.

## Feedback

Give us your feedback, comments and ideas at https://github.com/astronomer/snowpatrol/discussions

## Contributing

Contributions to the Astronomer SnowPatrol Plugin are welcome! If you would like to contribute, please fork the
repository, make your changes, and submit a pull request.

## License

`astronomer-snowpatrol-plugin` is distributed under the terms of the [Apache 2](LICENSE.txt) license.
