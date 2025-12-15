import requests
import json
from django.conf import settings

from .models import (
    CyberScamStat,
    VoicePhishingStat,
    TravelStat,
)


# =========================
# 1. 사이버 사기 (JSON 깨끗함)
# =========================
def fetch_cyber_scam(page=1, per_page=100):
    """경찰청 사이버사기 범죄 API에서 원본 JSON 가져오기"""

    url = f"{settings.SCAM_BASE_URL}{settings.SCAM_ENDPOINT}"

    params = {
        "page": page,
        "perPage": per_page,
        "serviceKey": settings.API_KEY,  # 공통 키
        "returnType": "JSON",
    }

    res = requests.get(url, params=params)
    res.raise_for_status()

    data = res.json()
    return data.get("data", [])


def sync_cyber_scam():
    """사이버 사기 데이터를 DB에 저장"""
    rows = fetch_cyber_scam(page=1, per_page=100)

    for row in rows:
        try:
            year = clean_int(row.get("연도"))
            category = row.get("구분", "")
        except Exception:
            continue  # 연도나 구분 이상하면 스킵

        CyberScamStat.objects.update_or_create(
            year=year,
            category=category,
            defaults={
                "direct_trade":  clean_int(row.get("직거래")),
                "shopping_mall": clean_int(row.get("쇼핑몰")),
                "game":          clean_int(row.get("게임")),
                "email_trade":   clean_int(row.get("이메일 무역")),
                "romance":       clean_int(row.get("연예빙자")),
                "investment":    clean_int(row.get("사이버투자")),
                "etc":           clean_int(row.get("사이버사기_기타")),
            },
        )



# =========================
# 2. 보이스피싱 월별 (문자열 JSON 방어 포함)
# =========================
def fetch_voice_phishing(page=1, per_page=200):
    """보이스피싱 월별 현황 API에서 데이터 가져오기"""

    url = f"{settings.VOICE_BASE_URL}{settings.VOICE_ENDPOINT}"

    params = {
        "page": page,
        "perPage": per_page,
        "serviceKey": settings.API_KEY,
        "returnType": "JSON",
    }

    res = requests.get(url, params=params)
    res.raise_for_status()

    # 1차 파싱: 최상위 JSON
    try:
        raw = res.json()
    except ValueError:
        raw = json.loads(res.text)

    # 경우에 따라 {"data": [...]} 이거나 그냥 [...] 일 수 있음
    rows = raw.get("data", raw)

    clean_rows = []

    for r in rows:
        obj = None

        # 문자열로 한 번 더 감싸져 있는 경우
        if isinstance(r, str):
            try:
                obj = json.loads(r)
            except ValueError:
                continue
        elif isinstance(r, dict):
            obj = r
        else:
            # dict도 문자열도 아니면 버림
            continue

        clean_rows.append(obj)

    return clean_rows


def sync_voice_phishing():
    """보이스피싱 월별 데이터를 DB에 저장"""

    rows = fetch_voice_phishing(page=1, per_page=500)

    for row in rows:
        # 안전하게 get + 검증
        year_raw = row.get("년")
        month_raw = row.get("월")
        cases_raw = row.get("전화금융사기 발생건수")

        # 하나라도 None / 빈 문자열이면 스킵
        if not year_raw or not month_raw or cases_raw is None or cases_raw == "":
            continue

        try:
            year = int(year_raw)
            month = int(month_raw)
            cases = int(cases_raw)
        except (TypeError, ValueError):
            # 숫자로 안 바뀌면 그냥 버리기
            continue

        VoicePhishingStat.objects.update_or_create(
            year=year,
            month=month,
            defaults={"cases": cases},
        )
    
    yearly = get_voice_phishing_yearly()
    return yearly

def get_voice_phishing_yearly():
    qs = VoicePhishingStat.objects.all().values("year", "month", "cases")
    if not qs:
        return None

    df = pd.DataFrame(qs)

    yearly = (
        df.groupby("year")["cases"]
        .sum()
        .reset_index()
        .rename(columns={"cases": "voice_year_total"})
    )

    return yearly



# =========================
# 3. 출입국 통계 – CSV 파일 기반으로 변경
# =========================
import pandas as pd


def load_csv(path, region_name):
    """CSV 파일을 로드하고 기본 전처리를 수행."""
    if path is None:
        print(f"[WARN] {region_name} CSV 경로가 없습니다.")
        return None

    try:
        df = pd.read_csv(path)
        df["region"] = region_name   # 지역(Asia/Europe 등) 태그 추가
        return df
    except Exception as e:
        print(f"[ERROR] {region_name} CSV 로딩 실패:", e)
        return None


def normalize_travel_dataframe(df):
    """
    수빈이가 만든 CSV 구조를 TravelStat 모델 형태로 통일하는 함수.
    CSV 형식 특징:
    - 첫 번째 컬럼: 연도 (예: 2018년, 2019년)
    - 두 번째 컬럼부터: 국가명 (열 제목)
    - 각 셀 값: 월별 출국자 수
    """

    records = []

    # 첫 번째 컬럼이 '연도' 또는 유사한 패턴이라고 가정
    year_col = df.columns[0]

    for _, row in df.iterrows():
        year_str = str(row[year_col])
        year = int(year_str.replace("년", "").strip())

        # 월 정보는 CSV에 포함됐으므로 따로 컬럼들을 월 단위로 읽기
        for col in df.columns[1:]:
            value = row[col]

            # 결측치나 NaN → 무시
            if pd.isna(value):
                continue

            # 국가명
            country_name = col.strip()

            # 값이 "123,456" 같은 형식이면 쉼표 제거
            try:
                departures = int(str(value).replace(",", ""))
            except:
                continue

            # TravelStat 모델 형식에 맞게 저장용 객체 만들기
            records.append({
                "year": year,
                "month": 0,  # 월 단위가 CSV에 없으면 0 또는 1로 통일
                "country": country_name,
                "country_name": country_name,
                "ed_cd": "D",
                "departures": departures,
            })

    return records


def sync_travel_stats_from_csv():
    """CSV 파일(아시아·유럽·아메리카·아프리카·오세아니아)을 모두 읽어 TravelStat DB에 저장"""

    csv_files = [
        (settings.ASIA_CSV, "Asia"),
        (settings.EUROPE_CSV, "Europe"),
        (settings.AFRICA_CSV, "Africa"),
        (settings.AMERICA_CSV, "America"),
        (settings.OCEANIA_CSV, "Oceania"),
    ]

    total_records = 0

    for path, region in csv_files:
        df = load_csv(path, region)
        if df is None:
            continue

        normalized = normalize_travel_dataframe(df)

        for rec in normalized:
            TravelStat.objects.update_or_create(
                year=rec["year"],
                month=rec["month"],       # 월 정보가 CSV에 없으므로 0 또는 1 고정
                country=rec["country"],
                ed_cd="D",
                defaults={
                    "country_name": rec["country_name"],
                    "departures": rec["departures"],
                }
            )

        total_records += len(normalized)

    return {"status": "csv_sync_ok", "saved_records": total_records}

def clean_int(value, default=0):
    """
    API에서 온 숫자 문자열을 안전하게 int로 변환.
    - "12,345" / " 123 " / "12.0" / None / "" / "-" 다 처리
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        s = value.strip()
        if s == "" or s == "-":
            return default
        # 쉼표, 공백, 퍼센트 등 제거
        s = s.replace(",", "").replace("%", "").replace(" ", "")
    else:
        s = str(value)

    try:
        return int(float(s))
    except Exception:
        return default

