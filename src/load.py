import os
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

ENV_FILE = PROJECT_DIR / ".env"

PROCESSED_FILE_PATTERN = "site_01_processed_cats_*.csv"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cat_adoption_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    breed VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NULL,
    age VARCHAR(50) NULL,
    age_month INT NULL,
    color VARCHAR(100) NULL,
    feature VARCHAR(255) NULL,
    branch VARCHAR(100) NULL,
    detail_url VARCHAR(500) NOT NULL,
    img_url VARCHAR(500) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_detail_url (detail_url)
)
"""

INSERT_SQL = """
INSERT INTO cat_adoption_data (
    name,
    breed,
    gender,
    age,
    age_month,
    color,
    feature,
    branch,
    detail_url,
    img_url
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s
)
"""

load_dotenv(dotenv_path=ENV_FILE)

required_env_names = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
]

missing_names = [name for name in required_env_names if not os.getenv(name)]

if missing_names:
    raise ValueError(f"필수 환경 변수가 없습니다. {missing_names}")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}


def load_processed_csv(
    file_path: Path,
) -> pd.DataFrame:

    if not file_path.is_file():
        raise FileNotFoundError(f"processed CSV가 없습니다. {file_path}")

    return pd.read_csv(file_path)


def find_latest_processed_csv(
    directory: Path = PROCESSED_DIR,
) -> Path:

    if not directory.is_dir():
        raise FileNotFoundError(f"processed 폴더가 없습니다. {directory}")

    processed_files = list(directory.glob(PROCESSED_FILE_PATTERN))

    if not processed_files:
        raise FileNotFoundError("DB에 저장할 processed CSV가 없습니다.")

    return max(
        processed_files,
        key=lambda path: path.name,
    )


def create_connection():
    return pymysql.connect(**DB_CONFIG)


def create_table(
    connection,
):
    with connection.cursor() as cursor:
        cursor.execute(CREATE_TABLE_SQL)


def prepare_insert_data(
    cats_df: pd.DataFrame,
) -> list[tuple]:

    insert_data = []

    for row in cats_df.itertuples(index=False):
        insert_data.append(
            (
                row.name,
                row.breed,
                None if pd.isna(row.gender) else row.gender,
                None if pd.isna(row.age) else row.age,
                None if pd.isna(row.age_month) else int(row.age_month),
                None if pd.isna(row.color) else row.color,
                None if pd.isna(row.feature) else row.feature,
                None if pd.isna(row.branch) else row.branch,
                row.detail_url,
                row.img_url,
            )
        )

    return insert_data


def load_cats(
    connection,
    cats_df: pd.DataFrame,
):
    insert_data = prepare_insert_data(cats_df)

    with connection.cursor() as cursor:
        cursor.executemany(
            INSERT_SQL,
            insert_data,
        )

    print(f"{len(insert_data)}건 INSERT 완료")


def run_load(
    processed_csv_file: Path | None = None,
):

    if processed_csv_file is None:
        processed_csv_file = find_latest_processed_csv()

    cats_df = load_processed_csv(processed_csv_file)

    connection = create_connection()

    try:
        create_table(connection)

        load_cats(
            connection,
            cats_df,
        )

        connection.commit()

        validate_load(
            connection,
            cats_df,
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def validate_load(
    connection,
    cats_df: pd.DataFrame,
):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM cat_adoption_data")

        db_count = cursor.fetchone()[0]

    df_count = len(cats_df)

    print(f"DataFrame 행 수 : {df_count}")
    print(f"DB 저장 행 수    : {db_count}")

    if df_count == db_count:
        print("DB 적재 검증 성공")
    else:
        print("DB 적재 검증 실패")


if __name__ == "__main__":
    try:
        run_load()

    except (
        FileNotFoundError,
        OSError,
        ValueError,
        pymysql.MySQLError,
    ) as error:

        print("DB 적재 작업에 실패했습니다.")
        print(f"오류 내용 : {error}")

        raise SystemExit(1) from error
