import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TARGET_URL = "https://www.dalunacats.com/product/list.php"

WAIT_TIMEOUT = 10

PAGE_INTERVAL = 1

HEADLESS = False

PROJECT_DIR = Path(__file__).resolve().parents[2]

RAW_HTML_DIR = PROJECT_DIR / "data" / "raw" / "html"

CAT_CARD_SELECTOR = "ul.cat_list li"
SITE_01_DETAIL_SELECTOR = "ul.cat_spec"


def create_driver(
    headless: bool = HEADLESS,
) -> webdriver.Chrome:
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver


def ensure_directory(
    directory: Path,
) -> Path:

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def create_batch_directory(
    directory: Path,
    collected_at: datetime,
) -> Path:
    batch_name = collected_at.strftime("%Y%m%d_%H%M%S")

    batch_dir = directory / batch_name

    return ensure_directory(batch_dir)


def save_raw_html(
    html: str,
    batch_dir: Path,
    site_no: int,
    source_page: int,
) -> Path:

    file_path = batch_dir / f"site_{site_no:02d}_page_{source_page:03d}.html"

    file_path.write_text(
        html,
        encoding="utf-8",
    )

    return file_path


def save_detail_html(
    html: str,
    batch_dir: Path,
    site_no: int,
    detail_no: int,
) -> Path:
    file_path = batch_dir / f"site_{site_no:02d}_detail_{detail_no:04d}.html"

    file_path.write_text(html, encoding="utf-8")

    return file_path


def load_all_cats(
    driver: webdriver.Chrome,
    batch_dir: Path,
    site_no: int,
):
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    current_page = 1

    while True:
        try:
            cat_cards = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, CAT_CARD_SELECTOR)
                )
            )

            print(
                f"{site_no}번 사이트 "
                f"{current_page}페이지 "
                f"고양이 카드 수 : {len(cat_cards)}"
            )

            save_raw_html(
                html=driver.page_source,
                batch_dir=batch_dir,
                site_no=site_no,
                source_page=current_page,
            )

            first_card = cat_cards[0]

            next_page = current_page + 1

            try:
                next_button = driver.find_element(
                    By.XPATH,
                    f'//div[contains(@class, "paginate")]'
                    f'//a[normalize-space()="{next_page}"]',
                )

            except NoSuchElementException:
                next_button = driver.find_element(
                    By.XPATH,
                    '//div[contains(@class, "paginate")]'
                    '//img[contains(@src, "/images/paging/right.jpg")]'
                    "/ancestor::a[1]",
                )

            next_button.click()

            wait.until(EC.staleness_of(first_card))

            current_page = next_page

            time.sleep(PAGE_INTERVAL)

        except (TimeoutException, NoSuchElementException):
            print(f"{site_no}번 사이트 " f"{current_page}페이지에서 수집 종료")
            break


def collect_detail_urls(
    driver: webdriver.Chrome,
) -> list[str]:
    wait = WebDriverWait(
        driver,
        WAIT_TIMEOUT,
    )

    detail_urls = []

    current_page = 1

    while True:
        try:
            cat_cards = wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        CAT_CARD_SELECTOR,
                    )
                )
            )

            for card in cat_cards:
                link_tag = card.find_element(
                    By.CSS_SELECTOR,
                    "a",
                )

                detail_url = link_tag.get_attribute("href")

                detail_urls.append(detail_url)

            first_card = cat_cards[0]
            next_page = current_page + 1

            try:
                next_button = driver.find_element(
                    By.XPATH,
                    f'//div[contains(@class, "paginate")]'
                    f'//a[normalize-space()="{next_page}"]',
                )

            except NoSuchElementException:
                next_button = driver.find_element(
                    By.XPATH,
                    '//div[contains(@class, "paginate")]'
                    '//img[contains(@src, "/images/paging/right.jpg")]'
                    "/ancestor::a[1]",
                )

            next_button.click()

            wait.until(EC.staleness_of(first_card))

            current_page = next_page

            time.sleep(PAGE_INTERVAL)

        except (
            TimeoutException,
            NoSuchElementException,
        ):
            break

    unique_detail_urls = list(dict.fromkeys(detail_urls))

    return unique_detail_urls


def save_all_detail_html(
    driver: webdriver.Chrome,
    detail_urls: list[str],
    batch_dir: Path,
    site_no: int,
):
    wait = WebDriverWait(
        driver,
        WAIT_TIMEOUT,
    )

    for detail_no, detail_url in enumerate(
        detail_urls,
        start=1,
    ):
        driver.get(detail_url)

        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    SITE_01_DETAIL_SELECTOR,
                )
            )
        )

        save_detail_html(
            html=driver.page_source,
            batch_dir=batch_dir,
            site_no=site_no,
            detail_no=detail_no,
        )

        print(f"{detail_no}번째 상세페이지 저장 완료")

        time.sleep(PAGE_INTERVAL)


def run_crawling():
    KST = timezone(timedelta(hours=9))

    collected_at = datetime.now(KST)

    batch_dir = create_batch_directory(
        RAW_HTML_DIR,
        collected_at,
    )

    driver = create_driver()

    try:
        driver.get(TARGET_URL)

        load_all_cats(
            driver=driver,
            batch_dir=batch_dir,
            site_no=1,
        )

        driver.get(TARGET_URL)

        detail_urls = collect_detail_urls(driver)

        print(f"상세 URL 수 : {len(detail_urls)}")

        save_all_detail_html(
            driver=driver,
            detail_urls=detail_urls,
            batch_dir=batch_dir,
            site_no=1,
        )

        return batch_dir

    finally:
        driver.quit()


if __name__ == "__main__":
    try:
        run_crawling()

    except (
        TimeoutException,
        NoSuchElementException,
        OSError,
        ValueError,
    ) as error:
        print("크롤링 작업에 실패했습니다.")
        print(f"오류 내용 : {error}")

        raise SystemExit(1) from error
