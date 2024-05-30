from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.models import BaseOperator
from typing import Any, Dict

from plugin import QueryTag, SNOWFLAKE_HOOK_PARAMS, task_policy


def test_query_tag_initialization():
    qt = QueryTag()
    assert qt.dag_id == "{{ dag.dag_id }}"
    assert qt.task_id == "{{ task.task_id }}"
    assert qt.run_id == "{{ run_id }}"
    assert qt.logical_date == "{{ logical_date }}"
    assert qt.started == "{{ ti.start_date }}"
    assert qt.operator == "{{ ti.operator }}"


def test_query_tag_str():
    qt = QueryTag()
    expected_str = (
        "{"
        "'dag_id': '{{ dag.dag_id }}', "
        "'task_id': '{{ task.task_id }}', "
        "'run_id': '{{ run_id }}', "
        "'logical_date': '{{ logical_date }}', "
        "'started': '{{ ti.start_date }}', "
        "'operator': '{{ ti.operator }}'"
        "}"
    )
    assert str(qt) == expected_str


def test_task_policy_without_existing_hook_params():
    class DummyTask(SQLExecuteQueryOperator):
        template_fields: tuple = ()

    task = DummyTask(task_id="test", sql="SELECT * FROM information_schema.tables")
    task_policy(task)
    assert "hook_params" in task.template_fields
    assert task.hook_params == SNOWFLAKE_HOOK_PARAMS


def test_task_policy_with_existing_hook_params():
    class DummyTask(BaseOperator):
        template_fields: tuple = ()
        hook_params: Dict[str, Any] = {"existing_param": "existing_value"}

    task = DummyTask(task_id="test")
    task_policy(task)
    assert "hook_params" in task.template_fields
    expected_params = {"existing_param": "existing_value", **SNOWFLAKE_HOOK_PARAMS}
    assert task.hook_params == expected_params
