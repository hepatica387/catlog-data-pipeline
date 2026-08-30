from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

TARGET_URL = "https://www.dalunacats.com/product/list.php"

PROJECT_DIR = Path(__file__).resolve().parents[2]

RAW_HTML_DIR = PROJECT_DIR / "data" / "raw" / "html"

INTERIM_DIR = PROJECT_DIR / "data" / "interim"

CAT_CARD_SELECTOR = "ul.cat_list li"

DETAIL_KEY_MAP = {
    "묘종": "breed_detail",
    "성별": "gender",
    "나이": "age",
    "모색": "color",
    "특징": "feature",
    "지점": "branch",
}


def parse_site_01_card(card):
    link_tag = card.select_one("a")
    img_tag = card.select_one(".cat_img img")
    text_tags = card.select(".cat_txt p")

    breed = text_tags[0].get_text(strip=True)
    name = text_tags[1].get_text(strip=True)

    detail_path = link_tag.get("href")
    img_path = img_tag.get("src")

    base_url = TARGET_URL

    detail_url = urljoin(
        base_url,
        detail_path,
    )

    img_url = urljoin(
        base_url,
        img_path,
    )

    return {
        "name": name,
        "breed": breed,
        "detail_url": detail_url,
        "img_url": img_url,
    }


def parse_site_01_detail(file_path):
    html = file_path.read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")

    spec_items = soup.select("ul.cat_spec li")

    detail_data = {}

    for item in spec_items:
        key_tag = item.select_one("span")
        value_tag = item.select_one("p")

        if key_tag is None or value_tag is None:
            continue

        key = key_tag.get_text(strip=True)
        value = value_tag.get_text(strip=True)

        column_name = DETAIL_KEY_MAP.get(key)

        if column_name is not None:
            detail_data[column_name] = value

    return detail_data


def parse_site_01_list_file(
    file_path: Path,
) -> list[dict]:

    html = file_path.read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(CAT_CARD_SELECTOR)

    return [parse_site_01_card(card) for card in cards]


def parse_site_01_list_files(
    file_paths: list[Path],
) -> pd.DataFrame:

    cats = []

    for file_path in file_paths:
        file_data = parse_site_01_list_file(file_path)

        cats.extend(file_data)

    return pd.DataFrame(cats)


def parse_site_01_detail_files(
    file_paths: list[Path],
) -> pd.DataFrame:

    details = []

    for file_path in file_paths:
        detail_data = parse_site_01_detail(file_path)

        details.append(detail_data)

    return pd.DataFrame(details)


def merge_site_01_data(
    list_df: pd.DataFrame,
    detail_df: pd.DataFrame,
) -> pd.DataFrame:

    merged_df = pd.concat(
        [
            list_df.reset_index(drop=True),
            detail_df.reset_index(drop=True),
        ],
        axis=1,
    )

    return merged_df


def finalize_site_01_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.drop(columns=["breed_detail"])

    return df


def find_latest_batch_directory(
    directory: Path = RAW_HTML_DIR,
) -> Path:

    batch_dirs = [path for path in directory.iterdir() if path.is_dir()]

    if not batch_dirs:
        raise FileNotFoundError("파싱할 RAW HTML 배치 폴더가 없습니다.")

    return max(
        batch_dirs,
        key=lambda path: path.name,
    )


def create_interim_batch_directory(
    batch_name: str,
) -> Path:

    interim_batch_dir = INTERIM_DIR / batch_name

    interim_batch_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return interim_batch_dir


def run_extract(
    batch_dir: Path | None = None,
) -> Path:

    if batch_dir is None:
        batch_dir = find_latest_batch_directory()

    list_files = sorted(batch_dir.glob("site_01_page_*.html"))

    detail_files = sorted(batch_dir.glob("site_01_detail_*.html"))

    if not list_files:
        raise FileNotFoundError("목록 HTML 파일이 없습니다.")

    if not detail_files:
        raise FileNotFoundError("상세 HTML 파일이 없습니다.")

    list_df = parse_site_01_list_files(list_files)

    detail_df = parse_site_01_detail_files(detail_files)

    if len(list_df) != len(detail_df):
        raise ValueError("목록 데이터와 상세 데이터의 행 수가 다릅니다.")

    merged_df = merge_site_01_data(
        list_df=list_df,
        detail_df=detail_df,
    )

    merged_df = finalize_site_01_columns(merged_df)

    interim_batch_dir = create_interim_batch_directory(batch_dir.name)

    output_file = interim_batch_dir / "site_01_parsed_cats.csv"

    merged_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"파싱 데이터 수 : {len(merged_df)}")
    print(f"interim 저장 경로 : {output_file}")

    return output_file


if __name__ == "__main__":
    try:
        run_extract()

    except (
        FileNotFoundError,
        OSError,
        ValueError,
    ) as error:
        print("HTML 파싱 작업에 실패했습니다.")
        print(f"오류 내용 : {error}")

        raise SystemExit(1) from error
