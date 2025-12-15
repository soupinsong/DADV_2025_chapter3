from django.db import models

class TravelStat(models.Model):
    """
    해외 출국 통계 (월별 OR 연도별)
    - month가 NULL이면 연도별 합계 데이터
    - month가 숫자(1~12)면 월별 데이터
    """
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=100)

    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)   # ⭐ 연도별 합계는 None

    departures = models.IntegerField(help_text="출국자 수")
    ratio = models.FloatField(blank=True, null=True)

    class Meta:
        # 이제 month를 unique에서 제거!
        unique_together = ("region", "country", "year")
        ordering = ["year", "month", "region", "country"]

    def __str__(self):
        if self.month:
            return f"{self.year}-{self.month:02d} {self.region}/{self.country}: {self.departures}명"
        return f"{self.year} 연도합계 {self.region}/{self.country}: {self.departures}명"


class VoicePhishingStat(models.Model):
    """월별 보이스피싱 발생 건수"""
    year = models.IntegerField()
    month = models.IntegerField()
    cases = models.IntegerField()  # 발생 건수

    class Meta:
        unique_together = ("year", "month")

    def __str__(self):
        return f"{self.year}-{self.month:02d}: {self.cases}건"


class CyberScamStat(models.Model):
    """
    연도별 사이버 사기 범죄 (유형별 분리 저장)
    API 필드 구성:
      - 연도
      - 구분 (발생건수 / 검거건수)
      - 직거래
      - 쇼핑몰
      - 게임
      - 이메일 무역
      - 연예빙자
      - 사이버투자
      - 사이버사기_기타
    """
    year = models.IntegerField()
    category = models.CharField(max_length=50)  # 발생건수 / 검거건수 등

    direct_trade = models.IntegerField()        # 직거래
    shopping_mall = models.IntegerField()       # 쇼핑몰
    game = models.IntegerField()                # 게임
    email_trade = models.IntegerField()         # 이메일 무역
    romance = models.IntegerField()             # 연예빙자
    investment = models.IntegerField()          # 사이버투자
    etc = models.IntegerField()                 # 사이버사기_기타

    class Meta:
        unique_together = ("year", "category")

    @property
    def total_cases(self):
        return (
            self.direct_trade +
            self.shopping_mall +
            self.game +
            self.email_trade +
            self.romance +
            self.investment +
            self.etc
        )

    def __str__(self):
        return f"{self.year} {self.category}: 총 {self.total_cases}건"
