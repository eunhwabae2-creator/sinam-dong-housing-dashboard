# 동대구역 인근 아파트 데이터보드

해움부동산중개용 대구 동구 아파트 대시보드입니다. 공공데이터포털 국토교통부 아파트 매매 및 전월세 실거래 API 자료를 GitHub Actions로 받아 `data/transactions.json`을 갱신합니다.

## API 키 설정

1. 공공데이터포털에서 [아파트 매매 실거래가 API](https://www.data.go.kr/data/15126469/openapi.do)와 [아파트 전월세 실거래가 API](https://www.data.go.kr/data/15126474/openapi.do)를 활용 신청하고 개인 서비스키를 발급합니다.
2. GitHub 저장소의 **Settings → Secrets and variables → Actions**에서 `MOLIT_SERVICE_KEY`라는 저장소 비밀을 만들고 서비스키를 값으로 입력합니다.
3. **Actions → Refresh apartment transaction data → Run workflow**를 실행합니다. 이후 매일 자동으로 최근 13개월 자료를 갱신합니다.

서비스키는 공개 HTML이나 저장소 파일에 넣지 마세요. 키가 설정되기 전까지 화면에는 예시 시세를 표시하지 않습니다.

## 제공 데이터와 범위

- `index.html`: GitHub Pages 공개 화면
- `sinam-dong-housing-dashboard.html`: 편집용 원본
- `haeum-real-estate-logo.jpg`: 로고
- `scripts/fetch_molit_data.py`: API 수집 스크립트
- `data/transactions.json`: 자동 갱신되는 거래자료

공공데이터포털 API는 동구 법정동 코드(27140)와 계약월 기준으로 조회합니다. 동대구역 생활권은 신암동·신천동·효목동 거래를 모아 보며, 신암1~5동은 API의 법정동 단위 한계로 신암동 전체 거래를 공유합니다. 월별 가격지수는 수집한 실거래의 면적당 평균을 기준월과 비교해 계산한 자체 지수이며, 한국부동산원·KB의 공식 가격지수와는 다릅니다.
