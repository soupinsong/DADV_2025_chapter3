from django.urls import path
from . import views

urlpatterns = [
    # 기본 페이지
    path("", views.index, name="index"),

    # API Key 테스트
    path("test/keys/", views.test_keys, name="test_keys"),

    # 사이버 사기 동기화
    path("sync/cyber/", views.sync_cyber_view, name="sync_cyber"),

    # 보이스피싱 동기화
    path("sync/voice/", views.sync_voice_view, name="sync_voice"),

    # 출입국 통계 동기화 (year, month GET 파라미터)
    path("sync/travel/", views.sync_travel_view, name="sync_travel"),

    # 사이버 사기 원본 데이터 테스트
    path("test/cyber/", views.test_cyber, name="test_cyber"),

    path("test/voice/", views.test_voice),

    path("debug/travel/", views.travel_debug_view, name="travel_debug"),

    path("sync/voiceall/", views.sync_voice_yearly_view, name="sync_voiceall"),

    path("analysis/data/", views.get_analysis_data, name="analysis_data"),

]