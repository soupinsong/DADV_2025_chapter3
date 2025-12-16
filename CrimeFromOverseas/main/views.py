from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings 
from .utils_csv_import import load_all_departure_data
from .models import TravelStat
from django.db.models import Count
from django.http import JsonResponse
from .api_client import get_voice_phishing_yearly
from .models import CyberScamStat

def test_departure_csv(request):
    df, year_totals, crime_totals, total_all_years = load_all_departure_data()


    return JsonResponse({
        "rows": len(df),
        "columns": list(df.columns),
        "sample": df.head(20).to_dict(orient="records")
    }, safe=False)


from .api_client import (
    sync_cyber_scam,
    sync_voice_phishing,
    sync_travel_stats_from_csv,
    fetch_cyber_scam,
)


def test_voice(request):
    from .api_client import fetch_voice_phishing
    return JsonResponse(fetch_voice_phishing(), safe=False)


# 메인 페이지
def index(request):
    return render(request, 'main/index.html')


# API Key 테스트 (현재 구조에 맞춤)
def test_keys(request):
    return JsonResponse({
        "API_KEY": settings.API_KEY is not None,
        "SCAM_BASE_URL": settings.SCAM_BASE_URL,
        "VOICE_BASE_URL": settings.VOICE_BASE_URL,
    })

from .utils_csv_import import load_all_departure_data, save_yearly_to_db

def sync_travel_view(request):
    df, year_totals, crime_totals, crime_ratio, total_all_years = load_all_departure_data()

    saved = save_yearly_to_db(df)

    return JsonResponse({
        "status": "ok",
        "saved_rows": saved,
        "total_rows": len(df),
        "year_totals": year_totals.to_dict(),          # 연도별 출국자 합계
        "crime_totals": crime_totals.to_dict(),        # 범죄국 연도별 합계
        "crime_ratio": crime_ratio.to_dict(orient="records"),
        "total_all_years": int(total_all_years),       # 전체 합계
    })


# 사이버사기 API 동기화
def sync_cyber_view(request):
    sync_cyber_scam()
    return JsonResponse({"status": "cyber_scam_sync_ok"})


# 보이스피싱 API 동기화
def sync_voice_view(request):
    sync_voice_phishing()
    return JsonResponse({"status": "voice_phishing_sync_ok"})


from .api_client import sync_voice_phishing, get_voice_phishing_yearly


def sync_voice_yearly_view(request):
    """
    보이스피싱 월별 데이터를 DB로 저장하고,
    연도별 합계(yearly)를 JSON으로 반환한다.
    """
    # 월별 데이터 저장
    sync_voice_phishing()

    # 연도별 합계 계산
    yearly_df = get_voice_phishing_yearly()

    if yearly_df is None:
        return JsonResponse({"status": "no_voice_data"})

    return JsonResponse({
        "status": "ok",
        "yearly_voice_stats": yearly_df.to_dict(orient="records"),
    })


# 사이버사기 원본 데이터 테스트 조회
def test_cyber(request):
    data = fetch_cyber_scam()
    return JsonResponse(data, safe=False)


def travel_debug_view(request):
    stats_limit = 100

    total = TravelStat.objects.count()

    if total == 0:
        return render(request, "main/travel_debug.html", {
            "total_count": 0,
            "regions": [],
            "stats": [],
            "stats_limit": stats_limit,
            "empty": True,
        })

    stats = (
        TravelStat.objects
        .order_by("-year", "-month", "region", "country")[:stats_limit]
    )

    regions = (
        TravelStat.objects
        .values("region")
        .annotate(count=Count("id"))
        .order_by("region")
    )

    context = {
        "total_count": TravelStat.objects.count(),
        "regions": regions,
        "stats": stats,
        "stats_limit": stats_limit,
    }
    return render(request, "main/travel_debug.html", context)


def get_analysis_data(request):
    """
    범죄국 비율, 사이버 사기 yearly, 보이스피싱 yearly
    모두 JSON으로 반환
    """

    # 👉 1) 출국자 통계 (CSV 기반)
    df, total_by_year, crime_by_year, total2018_2024 = load_all_departure_data()

    # 연도: 2018~2024 슬라이싱
    target_years = list(range(2018, 2025))

    # 전체 출국자
    total_year_dict = total_by_year.set_index("year")["year_total"].to_dict()

    # 범죄국 출국자
    crime_year_dict = crime_by_year.set_index("year")["crime_country_total"].to_dict()

    # 👉 1-1) 범죄국 출국자 비율 (%) 계산
    crime_ratio = []
    for y in target_years:
        if y in total_year_dict and y in crime_year_dict:
            ratio = (crime_year_dict[y] / total_year_dict[y]) * 100
            crime_ratio.append(round(ratio, 3))
        else:
            crime_ratio.append(None)

    # 👉 2) 보이스피싱 연도별 합계
    vp_df = get_voice_phishing_yearly()
    vp_dict = vp_df.set_index("year")["voice_year_total"].to_dict()
    voice_cases = [vp_dict.get(y, None) for y in target_years]

    # 👉 3) 사이버사기 연도별 total_cases 계산
    scam_qs = CyberScamStat.objects.all()
    scam_yearly = {}

    for obj in scam_qs:
        scam_yearly.setdefault(obj.year, 0)
        scam_yearly[obj.year] += obj.total_cases

    cyber_scam_cases = [scam_yearly.get(y, None) for y in target_years]

    return JsonResponse({
        "years": target_years,
        "crime_ratio": crime_ratio,
        "cyber_scam_cases": cyber_scam_cases,
        "voice_phishing_cases": voice_cases
    })

from django.http import JsonResponse
from .utils_csv_import import load_all_departure_data
from .api_client import get_voice_phishing_yearly, fetch_cyber_scam

import pandas as pd
from django.http import JsonResponse

from .utils_csv_import import load_all_departure_data
from .api_client import get_voice_phishing_yearly
from .models import CyberScamStat


def build_analysis_data():
    """
    그래프용 분석 데이터를 생성하여 JSON 형태로 반환.
    기간은 공통된 2018~2025로 통일.
    """

    # 1) 출입국 CSV 데이터에서 연도별 합계, 범죄국 합계 불러오기
    df, year_totals, crime_totals, country_yearly, total_2018_2024 = load_all_departure_data()


    # 2) 분석 공통 연도 구간 설정
    valid_years = list(range(2018, 2026))  # 2018~2025

    # 3) 출국자 데이터 필터링
    year_totals_filtered = year_totals[year_totals["year"].isin(valid_years)]
    crime_totals_filtered = crime_totals[crime_totals["year"].isin(valid_years)]

    years = year_totals_filtered["year"].tolist()

    # 4) 범죄국 비율(%)
    crime_ratio = (
        crime_totals_filtered["crime_country_total"].values /
        year_totals_filtered["year_total"].values * 100
    ).tolist()

    # 5) 사이버사기 연도별 합계 (이미 연도별 total 필드 있다고 가정)
    cyber_rows = CyberScamStat.objects.filter(year__in=valid_years).values(
        "year",
        "direct_trade",
        "shopping_mall",
        "game",
        "email_trade",
        "romance",
        "investment",
        "etc",
    )

    # 연도별 total 계산
    cyber_yearly = {}
    for row in cyber_rows:
        year = row["year"]
        total = (
            row["direct_trade"] +
            row["shopping_mall"] +
            row["game"] +
            row["email_trade"] +
            row["romance"] +
            row["investment"] +
            row["etc"]
        )
        cyber_yearly[year] = total

    cyber_scam_cases = [cyber_yearly.get(y, 0) for y in years]

    # 6) 보이스피싱 연도별 합계
    voice_df = get_voice_phishing_yearly()
    voice_df = voice_df[voice_df["year"].isin(valid_years)].sort_values("year")
    voice_phishing_cases = voice_df["voice_year_total"].tolist()

    # 7) 길이 확인 후 패딩/정렬 (혹시 DB 누락된 연도가 있어도 안전)
    def align_to_years(values, years_list):
        """values 길이가 years_list와 다르면 빈 값(0)으로 보정"""
        data = []
        year_to_value = dict(zip(years_list, values))
        for y in years_list:
            data.append(year_to_value.get(y, 0))
        return data

    cyber_scam_cases = align_to_years(cyber_scam_cases, years)
    voice_phishing_cases = align_to_years(voice_phishing_cases, years)

    # 8) 최종 JSON 데이터 반환
    return {
        "years": years,
        "crime_ratio": crime_ratio,
        "cyber_scam_cases": [cyber_yearly.get(y, 0) for y in valid_years],
        "voice_phishing_cases": voice_phishing_cases,
    }




def get_analysis_data(request):
    """HTML에서 호출하는 /analysis/data/ API"""
    data = build_analysis_data()
    return JsonResponse(data)

from django.shortcuts import render

def analysis_view(request):
    """
    분석 시각화 메인 페이지 (HTML)
    """
    return render(request, "main/analysis_data.html")

# views.py (하단에 추가)

from django.http import JsonResponse
from .models import CyberScamStat

def step3_radial_data(request):
    qs = CyberScamStat.objects.order_by("year")

    voice_df = get_voice_phishing_yearly()
    voice_dict = dict(
        zip(voice_df["year"], voice_df["voice_year_total"])
    )

    categories = [
        "shopping",
        "email_trade",
        "celebrity",
        "cyber_invest",
        "cyber_etc",
        "voice_phishing",
        "total"
    ]

    data = []

    for row in qs:
        year = row.year

        year_data = {
            "year": year,
            "shopping": row.shopping_mall,
            "email_trade": row.email_trade,
            "celebrity": row.romance,
            "cyber_invest": row.investment,
            "cyber_etc": row.etc,
            "voice_phishing": voice_dict.get(year, 0),  # ✅ API에서 합침
        }

        year_data["total"] = sum(
            v for k, v in year_data.items() if k != "year"
        )

        data.append(year_data)

    return JsonResponse({
        "categories": categories,
        "data": data
    })

