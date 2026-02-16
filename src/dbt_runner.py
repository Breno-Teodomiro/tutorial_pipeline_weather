import logging
import os
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _execute_dbt_command(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if stdout:
        logging.info(stdout)
    if stderr:
        logging.warning(stderr)

    return result.returncode, stdout, stderr


def run_dbt_build() -> None:
    project_dir = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt_weather")
    profiles_dir = os.getenv("DBT_PROFILES_DIR", project_dir)
    target = os.getenv("DBT_TARGET", "dev")
    auto_full_refresh = os.getenv("DBT_AUTO_FULL_REFRESH_ON_SCHEMA_CHANGE", "true").lower() == "true"

    cmd = [
        "dbt",
        "run",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        profiles_dir,
        "--target",
        target,
    ]

    logging.info("→ Executando dbt: %s", " ".join(cmd))
    code, stdout, stderr = _execute_dbt_command(cmd)

    if code == 0:
        logging.info("✅ dbt run finalizado com sucesso.")
        return

    output = f"{stdout}\n{stderr}".lower()
    schema_change_error = "column" in output and "does not exist" in output
    relation_state_error = "relation" in output and "does not exist" in output
    should_retry_full_refresh = schema_change_error or relation_state_error

    if auto_full_refresh and should_retry_full_refresh:
        cmd_full_refresh = [*cmd, "--full-refresh"]
        logging.warning(
            "⚠️ Falha por incompatibilidade de schema detectada. Executando fallback com full-refresh: %s",
            " ".join(cmd_full_refresh),
        )
        code, _, _ = _execute_dbt_command(cmd_full_refresh)
        if code == 0:
            logging.info("✅ dbt run com full-refresh finalizado com sucesso.")
            return

    raise RuntimeError("Falha ao executar dbt run. Verifique logs acima.")
