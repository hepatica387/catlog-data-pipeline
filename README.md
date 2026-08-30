# Catlog Data Collection Pipeline

## 1. 프로젝트 소개

고양이 분양 사이트의 데이터를 Selenium으로 수집하고,
HTML 파싱 → 데이터 전처리 → MySQL 적재까지 수행하는 데이터 수집 파이프라인입니다.

---

## 2. 주요 기능

- Selenium 기반 동적 크롤링
- 목록 페이지 페이지네이션 처리
- 상세 페이지 데이터 수집
- RAW HTML 저장
- BeautifulSoup 기반 HTML 파싱
- Pandas 기반 데이터 전처리
- 품종, 성별, 나이, 모색 정규화
- 결측값 및 중복 데이터 검증
- MySQL 데이터 적재

---

## 3. 데이터 파이프라인

```text
고양이 분양 사이트
        ↓
Selenium 크롤링
        ↓
RAW HTML
        ↓
BeautifulSoup 파싱
        ↓
Interim CSV
        ↓
데이터 전처리
        ↓
Processed CSV
        ↓
MySQL

---

## 4. 프로젝트 구조

project/
├── data/
│   ├── raw/
│   │   └── html/
│   ├── interim/
│   └── processed/
│
├── src/
│   ├── __init__.py
│   ├── crawling.py
│   ├── extract.py
│   ├── preprocess.py
│   └── load.py
│
├── main.py
├── .env
├── .gitignore
└── README.md

| 파일              | 역할                           |
| --------------- | ---------------------------- |
| `crawling.py`   | Selenium을 이용한 RAW HTML 수집    |
| `extract.py`    | RAW HTML 파싱 및 Interim CSV 생성 |
| `preprocess.py` | 데이터 정제 및 Processed CSV 생성    |
| `load.py`       | Processed CSV MySQL 적재       |
| `__init__.py`   | 실행 함수 노출                     |
| `main.py`       | 전체 파이프라인 실행                  |


---

## 5. 수집 및 처리 데이터

| 컬럼           | 설명         |
| ------------ | ---------- |
| `name`       | 고양이 이름     |
| `breed`      | 품종         |
| `gender`     | 성별         |
| `age`        | 원본 나이      |
| `age_month`  | 개월 단위 나이   |
| `color`      | 모색         |
| `feature`    | 특징         |
| `branch`     | 분양 지점      |
| `detail_url` | 상세 페이지 URL |
| `img_url`    | 이미지 URL    |

---

## 6. 데이터 전처리 및 검증

### 1. 성별 정규화
남아 → M
여아 → F

### 2. 나이 정규화
2개월령 → 2
3개월령 → 3

### 3. 품종 정규화
렉돌 → 랙돌
벵갈 → 뱅갈
브리티쉬숏헤어 → 브리티쉬 숏헤어

### 데이터 검증
- 필수 컬럼 존재 여부
- 필수 데이터 결측 여부
- detail_url 중복 여부
- 목록/상세 데이터 건수 확인
- DB 적재 건수 확인

---

## 7. 데이터 베이스
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
);

## 8. 실행 방법
### 패키지 설치
- pip install pandas selenium beautifulsoup4 pymysql python-dotenv

### .env 파일 생성
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=root
  DB_PASSWORD=your_password
  DB_NAME=catlog

### 전체 파이프라인 실행
- python main.py

### 실행 순서
run_crawling()
  → run_extract()
  → run_preprocess()
  → run_load()

---

### 9. 기술 스택
- Python
- Selenium
- BeautifulSoup
- Pandas
- MySQL
- PyMySQL
- python-dotenv
- Jupyter Notebook
- Git
- GitHub

---

## 10. 전체 파이프라인

```text
main.py
  │
  ├─ run_crawling()
  │      ↓
  │   Raw HTML
  │
  ├─ run_extract()
  │      ↓
  │   Interim CSV
  │
  ├─ run_preprocess()
  │      ↓
  │   Processed CSV
  │
  └─ run_load()
         ↓
      MySQL