import pandas as pd
from django.conf import settings
from .models import TravelStat

def clean_num(x):
    if pd.isna(x):
        return 0
    x = str(x).replace(",", "").replace("%", "").strip()
    if x == "" or x == "-":
        return 0
    try:
        return int(float(x))
    except:
        return 0


def load_csv_trip_table(path, region_name):
    df = pd.read_csv(path, header=None, encoding="utf-8-sig")

    # 1행 = 국가명, 2행 = 명수/전년대비
    header_country = df.iloc[1]   # 국가명 한글/영문 페어
    header_type = df.iloc[2]      # 명수/전년대비

    n_cols = df.shape[1]

    # ★ 국가명 & 명수열만 추출하는 규칙 ★
    country_cols = []  # (열번호, 국가명)

    for col in range(3, n_cols):
        col_type = str(header_type[col]).strip()
        col_country = str(header_country[col]).strip()

        # 명수 열만 선택 (전년대비 제외)
        if col_type != "명수":
            continue

        # 국가명은 한글/영문 페어 중 “한글쪽”만 이름으로 사용
        # 예: 4열=일본 / 5열=Japan → 우리는 4열의 "일본" 사용
        country_name = col_country
        if country_name.lower() == "nan" or country_name == "":
            continue

        country_cols.append((col, country_name))

    print(f"[{region_name}] 감지된 국가 수: {len(country_cols)}")
    print(f"[{region_name}] 국가 리스트 앞 10개:", country_cols[:10])

    output_rows = []
    current_year = None

    # 실제 데이터는 3행부터 시작
    for idx, row in df.iloc[3:].iterrows():
        year_cell = str(row.iloc[0]).strip()
        month_cell = str(row.iloc[1]).strip()

        # 연도 행
        if year_cell.endswith("년"):
            digits = "".join([c for c in year_cell if c.isdigit()])
            if digits:
                current_year = int(digits)
            continue

        if current_year is None:
            continue

        # 월 행
        if not month_cell.endswith("월"):
            continue

        month_digits = "".join([c for c in month_cell if c.isdigit()])
        if not month_digits:
            continue

        month = int(month_digits)

        # 국가별 명수 추출
        for col, country_name in country_cols:
            raw_val = row.iloc[col]
            departures = clean_num(raw_val)

            output_rows.append({
                "year": current_year,
                "month": month,
                "country": country_name,
                "region": region_name,
                "departures": departures
            })

    return pd.DataFrame(output_rows)


def load_all_departure_data():
    files = {
        "asia": settings.ASIA_CSV,
        "europe": settings.EUROPE_CSV,
        "africa": settings.AFRICA_CSV,
        "america": settings.AMERICA_CSV,
        "oceania": settings.OCEANIA_CSV,
    }

    outputs = []

    for region, path in files.items():
        print(f"=== {region.upper()} CSV 로드 시작 ===")
        try:
            df = load_csv_trip_table(path, region)
            print(df.head())
            outputs.append(df)
        except Exception as e:
            print(f"⚠ {region} CSV 로드 실패 → {e}")

    if not outputs:
        print("❌ CSV 데이터 없음")
        return pd.DataFrame()

    return pd.concat(outputs, ignore_index=True)

def save_to_db(df):
    count = 0
    for _, row in df.iterrows():
        TravelStat.objects.update_or_create(
            year=row["year"],
            month=row["month"],
            country=row["country"],
            region=row["region"],
            defaults={"departures": row["departures"]},
        )
        count += 1
    return count

