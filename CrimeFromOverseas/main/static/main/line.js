// static/main/line.js
// ✅ d3 / scrollama 는 HTML에서 전역으로 이미 로드됨

const width = 900;
const height = 520;
const margin = { top: 40, right: 30, bottom: 60, left: 70 };

const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const root = d3.select("#graphic");
root.selectAll("*").remove();

const svg = root.append("svg")
  .attr("width", "100%")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .style("display", "block");

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const title = svg.append("text")
  .attr("x", margin.left)
  .attr("y", 24)
  .attr("font-size", 16)
  .attr("font-weight", 700)
  .text("");

const gx = g.append("g").attr("transform", `translate(0,${innerH})`);
const gy = g.append("g");

const xLabel = svg.append("text")
  .attr("x", margin.left + innerW / 2)
  .attr("y", height - 18)
  .attr("text-anchor", "middle")
  .attr("font-size", 12)
  .attr("fill", "#444");

const yLabel = svg.append("text")
  .attr("x", 18)
  .attr("y", margin.top + innerH / 2)
  .attr("transform", `rotate(-90, 18, ${margin.top + innerH / 2})`)
  .attr("text-anchor", "middle")
  .attr("font-size", 12)
  .attr("fill", "#444");

const plot = g.append("g");

const slider = document.getElementById("scaleSlider");
const scaleLabel = document.getElementById("scaleLabel");

let DATA = null;
let currentStep = 0;
let scaleFactor = 1.0;

slider.addEventListener("input", () => {
  scaleFactor = +slider.value;
  scaleLabel.textContent = `${scaleFactor.toFixed(2)}x`;
  render(currentStep); // ✅ 현재 step 유지한 채로 업데이트
});

// --------------------
// Utils
// --------------------
function linreg(x, y) {
  const n = x.length;
  const meanX = d3.mean(x);
  const meanY = d3.mean(y);
  const num = d3.sum(x.map((xi, i) => (xi - meanX) * (y[i] - meanY)));
  const den = d3.sum(x.map(xi => (xi - meanX) ** 2));
  const slope = den === 0 ? 0 : num / den;
  const intercept = meanY - slope * meanX;
  return { slope, intercept };
}

function clearPlot() {
  plot.selectAll("*").remove();
}

// --------------------
// STEP 0: absolute trend lines
// --------------------
function drawAbsolute(data) {
  clearPlot();
  title.text("STEP 1. 절대량(연도별) 변화");
  xLabel.text("연도");
  yLabel.text("발생 건수");

  const years = data.years;
  const cyber = data.cyber_scam_cases;
  const voice = data.voice_phishing_cases;

  const x = d3.scaleLinear()
    .domain(d3.extent(years))
    .range([0, innerW]);

  const y = d3.scaleLinear()
    .domain([0, d3.max([...cyber, ...voice]) * 1.05])
    .range([innerH, 0]);

  gx.call(d3.axisBottom(x).tickFormat(d3.format("d")));
  gy.call(d3.axisLeft(y));

  const line = d3.line()
    .x((d, i) => x(years[i]))
    .y(d => y(d));

  // cyber line
  plot.append("path")
    .datum(cyber)
    .attr("fill", "none")
    .attr("stroke", "#ff4d4d")
    .attr("stroke-width", 3)
    .attr("d", line);

  // voice line
  plot.append("path")
    .datum(voice)
    .attr("fill", "none")
    .attr("stroke", "#ff884d")
    .attr("stroke-width", 3)
    .attr("d", line);

  // legend
  const lg = plot.append("g").attr("transform", `translate(${innerW - 210}, 10)`);
  lg.append("rect").attr("width", 200).attr("height", 52).attr("rx", 10).attr("fill", "#fff").attr("stroke", "#eee");
  lg.append("circle").attr("cx", 16).attr("cy", 18).attr("r", 6).attr("fill", "#ff4d4d");
  lg.append("text").attr("x", 30).attr("y", 22).attr("font-size", 12).text("사이버사기(연도별 총합)");
  lg.append("circle").attr("cx", 16).attr("cy", 38).attr("r", 6).attr("fill", "#ff884d");
  lg.append("text").attr("x", 30).attr("y", 42).attr("font-size", 12).text("보이스피싱(연도별 총합)");
}

// --------------------
// STEP 1: ratio vs crime scatter + regression
// --------------------
function drawRatio(data) {
  clearPlot();
  title.text("STEP 2. 범죄국 출국자 비율(%) vs 범죄");
  xLabel.text("범죄국 출국자 비율(%)");
  yLabel.text("발생 건수");

  // 2018~2025 같이 길이 다를 수 있으니 "공통 길이"만 사용
  const n = Math.min(data.years.length, data.crime_ratio.length, data.voice_phishing_cases.length, data.cyber_scam_cases.length);
  const years = data.years.slice(0, n);
  const ratio = data.crime_ratio.slice(0, n);
  const cyber = data.cyber_scam_cases.slice(0, n);
  const voice = data.voice_phishing_cases.slice(0, n);

  // ✅ 선택: 여기서는 voice를 표시 (원하면 cyber로 바꿔도 됨)
  const yData = voice;

  const x = d3.scaleLinear()
    .domain(d3.extent(ratio))
    .nice()
    .range([0, innerW]);

  const y = d3.scaleLinear()
    .domain([0, d3.max(yData) * 1.05])
    .nice()
    .range([innerH, 0]);

  gx.call(d3.axisBottom(x));
  gy.call(d3.axisLeft(y));

  // points
  plot.selectAll("circle")
    .data(years.map((yr, i) => ({ yr, x: ratio[i], y: yData[i] })))
    .join("circle")
    .attr("cx", d => x(d.x))
    .attr("cy", d => y(d.y))
    .attr("r", 7)
    .attr("fill", "#ff884d")
    .attr("opacity", 0.9);

  // year labels
  plot.selectAll("text.pt")
    .data(years.map((yr, i) => ({ yr, x: ratio[i], y: yData[i] })))
    .join("text")
    .attr("class", "pt")
    .attr("x", d => x(d.x) + 9)
    .attr("y", d => y(d.y) + 4)
    .attr("font-size", 11)
    .attr("fill", "#333")
    .text(d => d.yr);

  // regression
  const { slope, intercept } = linreg(ratio, yData);
  const xLine = [d3.min(ratio), d3.max(ratio)];
  const yLine = xLine.map(v => slope * v + intercept);

  plot.append("path")
    .datum([{ x: xLine[0], y: yLine[0] }, { x: xLine[1], y: yLine[1] }])
    .attr("fill", "none")
    .attr("stroke", "#111")
    .attr("stroke-width", 2)
    .attr("d", d3.line().x(d => x(d.x)).y(d => y(d.y)));

  plot.append("text")
    .attr("x", 10)
    .attr("y", 12)
    .attr("font-size", 12)
    .attr("fill", "#111")
    .text(`회귀선: y = ${slope.toFixed(2)}x + ${intercept.toFixed(0)} (보이스피싱 기준)`);
}

// ================================
// STEP 3 : 원형 중첩(밀집) 구조 (FIXED)
// ================================
async function drawStep3Radial(maxYear, populationBase) {
  clearPlot();              // ✅ 전체 DOM 삭제 금지
  title.text("STEP 3. 원형 중첩(밀집) 구조");
  xLabel.text("");
  yLabel.text("");

  const res = await fetch("/analysis/step3/");
  const json = await res.json();

  const { data, categories } = json;
  const filtered = data.filter(d => d.year <= maxYear);

  const centerX = innerW / 2;
  const centerY = innerH / 2;

  const gRadial = plot.append("g")
    .attr("transform", `translate(${centerX}, ${centerY})`);

  const radiusMax = Math.min(innerW, innerH) * 0.35;

  const angle = d3.scalePoint()
    .domain(categories)
    .range([0, Math.PI * 2]);

  const valueMax = d3.max(filtered, d =>
    d3.max(categories, c => d[c])
  );

  const radius = d3.scaleLinear()
    .domain([0, valueMax])
    .range([0, radiusMax * (populationBase / 20000000)]);

  const yearColor = d3.scaleSequential()
    .domain([2018, maxYear])
    .interpolator(d3.interpolateRainbow);

  const line = d3.lineRadial()
    .angle(d => angle(d.category))
    .radius(d => radius(d.value))
    .curve(d3.curveCardinalClosed);

  filtered.forEach(yearData => {
    const points = categories.map(c => ({
      category: c,
      value: yearData[c]
    }));

    gRadial.append("path")
      .datum(points)
      .attr("d", line)
      .attr("fill", yearColor(yearData.year))
      .attr("fill-opacity", 0.1)
      .attr("stroke", yearColor(yearData.year))
      .attr("stroke-width", 2);
  });

  // 카테고리 라벨
  categories.forEach(c => {
    const a = angle(c) - Math.PI / 2;
    const r = radiusMax + 22;

    gRadial.append("text")
      .attr("x", Math.cos(a) * r)
      .attr("y", Math.sin(a) * r)
      .attr("text-anchor", "middle")
      .attr("font-size", 12)
      .attr("fill", "#333")
      .text(c);
  });
}

// --------------------
// Render dispatcher
// --------------------
function render(step) {
  if (!DATA) return;
  currentStep = step;

  if (step === 0) drawAbsolute(DATA);
  if (step === 1) drawRatio(DATA);
  if (step === 2) drawStep3Radial(currentYear, departureInputValue);
}

// --------------------
// Data load + scroller
// --------------------
fetch("/analysis/data/")
  .then(res => res.json())
  .then(data => {
    DATA = data;

    // ✅ 첫 화면
    render(0);

    // ✅ 스크롤
    const scroller = scrollama();

    scroller.setup({
      step: "#sections .step",
      offset: 0.6
    })
    .onStepEnter(resp => {
      const step = +resp.element.dataset.step;
      render(step);
    })
    .onStepExit(resp => {
      // ✅ 위로 스크롤 시 이전 단계로 되돌리기
      if (resp.direction === "up") {
        const step = +resp.element.dataset.step;
        render(Math.max(0, step - 1));
      }
    });

    window.addEventListener("resize", scroller.resize);
  })
  .catch(err => {
    console.error("Data load failed:", err);
    title.text("데이터 로딩 실패: 콘솔 확인");
  });




