import re
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[2]

INTERIM_DIR = PROJECT_DIR / "data" / "interim"

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

PARSED_FILE_NAME = "site_01_parsed_cats.csv"

GENDER_MAP = {
    "남아": "M",
    "여아": "F",
}

BREED_MAP = {
    "먼치": "먼치킨",
    "렉돌": "랙돌",
    "벵갈": "뱅갈",
    "브리티쉬롱헤어": "브리티쉬 롱헤어",
    "브리티쉬먼치킨": "브리티쉬 먼치킨",
    "브리티쉬숏헤어": "브리티쉬 숏헤어",
    "브리티쉿쇼헤어": "브리티쉬 숏헤어",
    "스코티쉬스트레이트": "스코티쉬 스트레이트",
    "스코티쉬폴드": "스코티쉬 폴드",
    "셀커크랙스": "셀커크렉스",
    "아메리칸숏헤어": "아메리칸 숏헤어",
    "아메리칸컬": "아메리칸 컬",
    "액죠틱 먼치킨": "엑죠틱 먼치킨",
    "터키시앙고라": "터키쉬앙고라",
    "하이랜드스트레이트": "하이랜드 스트레이트",
    "하이랜드폴드": "하이랜드 폴드",
}

COLOR_MAP = {
    "골드 태비": "골드태비",
    "골드 (ny11)": "골드(ny11)",
    "골드 (ny25)": "골드(ny25)",
    "레드 태비 앤 화이트": "레드태비앤화이트",
    "브라운 로젯": "브라운로젯",
    "블루바이 미티드": "블루바이미티드",
    "화이트 (오드아이)": "화이트(오드아이)",
    "화이트 스킨": "화이트스킨",
    "그래이앤화이트": "그레이앤화이트",
    "세피아 아쿠티": "세피아아구티",
    "세피아 아구티": "세피아아구티",
    "실버클랙식태비": "실버클래식태비",
    "쏘엘": "쏘렐",
    "치즈태앤화이트": "치즈태비앤화이트",
    "크림메커럴태비앤화이트": "크림매커럴태비앤화이트",
}

BRANCH_MAP = {
    "잠실 점": "잠실점",
    "왕십리 점": "왕십리점",
}

INVALID_AGE_VALUES = [
    "남아",
    "여아",
    "남아,여아",
]

REQUIRED_INPUT_COLUMNS = {
    "name",
    "breed",
    "gender",
    "age",
    "color",
    "feature",
    "branch",
    "detail_url",
    "img_url",
}

FINAL_COLUMNS = [
    "name",
    "breed",
    "gender",
    "age",
    "age_month",
    "color",
    "feature",
    "branch",
    "detail_url",
    "img_url",
]


def normalize_age(value):
    match = re.search(r"\d+", str(value))

    if match:
        return int(match.group())

    return None


def find_latest_interim_batch_directory(
    directory: Path = INTERIM_DIR,
) -> Path:

    batch_dirs = [path for path in directory.iterdir() if path.is_dir()]

    if not batch_dirs:
        raise FileNotFoundError("전처리할 interim 배치 폴더가 없습니다.")

    return max(
        batch_dirs,
        key=lambda path: path.name,
    )


def load_interim_csv(
    batch_dir: Path,
) -> pd.DataFrame:

    file_path = batch_dir / PARSED_FILE_NAME

    if not file_path.is_file():
        raise FileNotFoundError(f"파싱 CSV 파일이 없습니다. {file_path}")

    return pd.read_csv(file_path)


def preprocess_cats(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    TEXT_COLUMNS = [
        "name",
        "breed",
        "gender",
        "age",
        "color",
        "feature",
        "branch",
    ]

    for column in TEXT_COLUMNS:
        df[column] = df[column].astype("string").str.strip()

    df["gender"] = df["gender"].replace(GENDER_MAP)

    df["breed"] = df["breed"].replace(BREED_MAP)

    df["color"] = df["color"].replace(COLOR_MAP)

    df["branch"] = df["branch"].replace(BRANCH_MAP)

    df["age"] = df["age"].replace(INVALID_AGE_VALUES, pd.NA)

    mask = df["gender"].isna() & df["color"].isin(["남아", "여아"])

    df.loc[
        mask,
        "gender",
    ] = df.loc[
        mask,
        "color",
    ].map(GENDER_MAP)

    df.loc[
        mask,
        "color",
    ] = pd.NA

    df["age_month"] = df["age"].apply(normalize_age).astype("Int64")

    return df


def select_final_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    return df[FINAL_COLUMNS].copy()


def ensure_directory(
    directory: Path,
) -> Path:

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def validate_input_cats(
    df: pd.DataFrame,
) -> None:

    if df.empty:
        raise ValueError("전처리할 데이터가 비어 있습니다.")

    missing_columns = REQUIRED_INPUT_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(f"필수 컬럼이 누락되었습니다. " f"{sorted(missing_columns)}")


def validate_processed_cats(
    df: pd.DataFrame,
) -> None:

    if df.empty:
        raise ValueError("전처리 결과가 비어 있습니다.")

    required_columns = [
        "name",
        "breed",
        "detail_url",
        "img_url",
    ]

    null_counts = df[required_columns].isna().sum()

    invalid_nulls = null_counts[null_counts > 0]

    if not invalid_nulls.empty:
        raise ValueError(
            "필수 데이터에 결측값이 있습니다.\n" + invalid_nulls.to_string()
        )

    if df["detail_url"].duplicated().any():
        raise ValueError("중복된 detail_url이 존재합니다.")


def run_preprocess(
    interim_batch_dir: Path | None = None,
) -> Path:

    if interim_batch_dir is None:
        interim_batch_dir = find_latest_interim_batch_directory()

    cats_df = load_interim_csv(interim_batch_dir)

    validate_input_cats(cats_df)

    processed_df = preprocess_cats(cats_df)

    processed_df = select_final_columns(processed_df)

    validate_processed_cats(processed_df)

    ensure_directory(PROCESSED_DIR)

    output_file = PROCESSED_DIR / f"site_01_processed_cats_{interim_batch_dir.name}.csv"

    processed_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"전처리 데이터 수 : {len(processed_df)}")

    print(f"processed 저장 경로 : {output_file}")

    return output_file


if __name__ == "__main__":
    try:
        run_preprocess()

    except (
        FileNotFoundError,
        OSError,
        ValueError,
    ) as error:

        print("데이터 전처리 작업에 실패했습니다.")

        print(f"오류 내용 : {error}")

        raise SystemExit(1) from error
