let DATA = null;
let currentStep = 0;
let scaleFactor = 1.0;
let currentYear = 2025;

const width = 900;
const height = 520;
const margin = { top: 40, right: 30, bottom: 60, left: 70 };

const innerW = width - margin.left - margin.right;
const innerH = height - margin.top - margin.bottom;

const categories = [
  "shopping",
  "email_trade",
  "celebrity",
  "cyber_invest",
  "cyber_etc",
  "voice_phishing"
];

const root = d3.select("#graphic");
root.selectAll("*").remove();

const svg = root.append("svg")
  .attr("width", "100%")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .style("display", "block");

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const plot = g.append("g");

const title = svg.append("text")
  .attr("x", margin.left)
  .attr("y", 24)
  .attr("font-size", 16)
  .attr("font-weight", 700);

const subtitle = svg.append("text")
  .attr("x", margin.left)
  .attr("y", 42)
  .attr("font-size", 12)
  .attr("fill", "#666");

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

/* ==============================
   슬라이더
============================== */
const slider = document.getElementById("scaleSlider");
const scaleLabel = document.getElementById("scaleLabel");

slider.addEventListener("input", () => {
  scaleFactor = +slider.value;
  scaleLabel.textContent = `${scaleFactor.toFixed(2)}x`;
  if (currentStep === 2) drawStep3Radial();
});

const yearSlider = document.getElementById("yearSlider");
const yearLabel = document.getElementById("yearLabel");

yearSlider.addEventListener("input", () => {
  currentYear = +yearSlider.value;
  yearLabel.textContent = currentYear;
  if (currentStep === 2) drawStep3Radial();
});

function clearPlot() {
  plot.selectAll("*").remove();
}

function linreg(x, y) {
  const mx = d3.mean(x);
  const my = d3.mean(y);
  const num = d3.sum(x.map((d, i) => (d - mx) * (y[i] - my)));
  const den = d3.sum(x.map(d => (d - mx) ** 2));
  const slope = den === 0 ? 0 : num / den;
  return { slope, intercept: my - slope * mx };
}

/* ==============================
   STEP 1 – 절대량
============================== */
function drawAbsolute(data) {

  svg.selectAll(".step1-legend").remove();

  gx.style("display", null);
  gy.style("display", null);

  clearPlot();
  svg.selectAll(".step2-legend").remove();

  title.text("연도별 절대량 비교");
  subtitle.text("연도별 사이버 사기 및 보이스피싱 발생 건수의 절대적 증가룰 ");
  xLabel.text("연도");
  yLabel.text("발생 건수");

  const years = data.years;
  const cyber = data.cyber_scam_cases;
  const voice = data.voice_phishing_cases;

  const x = d3.scaleLinear().domain(d3.extent(years)).range([0, innerW]);
  const y = d3.scaleLinear()
    .domain([0, d3.max([...cyber, ...voice]) * 1.05])
    .range([innerH, 0]);

  gx.call(d3.axisBottom(x).tickFormat(d3.format("d")));
  gy.call(d3.axisLeft(y));

  const line = d3.line()
    .x((d, i) => x(years[i]))
    .y(d => y(d));

  plot.append("path")
    .datum(cyber)
    .attr("fill", "none")
    .attr("stroke", "#ff4d4d")
    .attr("stroke-width", 3)
    .attr("d", line);

  plot.append("path")
    .datum(voice)
    .attr("fill", "none")
    .attr("stroke", "#ff884d")
    .attr("stroke-width", 3)
    .attr("d", line);

  const legend = svg.append("g")
    .attr("class", "step1-legend")
    .attr("transform", `translate(${width - 220}, ${height - 150})`);

  [
    { label: "사이버 사기", color: "#ff4d4d" },
    { label: "보이스피싱", color: "#ff884d" }
  ].forEach((d, i) => {
    const g = legend.append("g")
      .attr("transform", `translate(0, ${i * 22})`);

    g.append("line")
      .attr("x1", 0)
      .attr("x2", 20)
      .attr("y1", 8)
      .attr("y2", 8)
      .attr("stroke", d.color)
      .attr("stroke-width", 3);

    g.append("text")
      .attr("x", 26)
      .attr("y", 12)
      .attr("font-size", 12)
      .attr("fill", "#333")
      .text(d.label);
  });

}

/* ==============================
   STEP 2 – 비율 vs 범죄
============================== */
function drawRatio(data) {
  gx.style("display", null);
  gy.style("display", null);

  clearPlot();
  svg.selectAll(".step2-legend").remove();

  title.text("범죄국 노출 비율(%)과 범죄율의 상관관계");
  subtitle.text("");
  xLabel.text("범죄국 출국자 비율(%)");
  yLabel.text("발생 건수");

  const n = Math.min(
    data.years.length,
    data.crime_ratio.length,
    data.voice_phishing_cases.length
  );

  const years = data.years.slice(0, n);
  const ratio = data.crime_ratio.slice(0, n);
  const yData = data.voice_phishing_cases.slice(0, n);

  const x = d3.scaleLinear().domain(d3.extent(ratio)).nice().range([0, innerW]);
  const y = d3.scaleLinear().domain([0, d3.max(yData) * 1.05]).nice().range([innerH, 0]);

  gx.call(d3.axisBottom(x));
  gy.call(d3.axisLeft(y));

  plot.selectAll("circle")
    .data(years.map((yr, i) => ({ yr, x: ratio[i], y: yData[i] })))
    .enter()
    .append("circle")
    .attr("cx", d => x(d.x))
    .attr("cy", d => y(d.y))
    .attr("r", 7)
    .attr("fill", "#ff884d");

  plot.selectAll(".year-label")
    .data(years.map((yr, i) => ({ yr, x: ratio[i], y: yData[i] })))
    .enter()
    .append("text")
    .attr("x", d => x(d.x) + 8)
    .attr("y", d => y(d.y) - 8)
    .attr("font-size", 11)
    .attr("fill", "#555")
    .text(d => d.yr);

  const { slope, intercept } = linreg(ratio, yData);
  const xs = d3.extent(ratio);

  plot.append("path")
    .datum(xs.map(v => ({ x: v, y: slope * v + intercept })))
    .attr("fill", "none")
    .attr("stroke", "#111")
    .attr("stroke-width", 2)
    .attr("d", d3.line().x(d => x(d.x)).y(d => y(d.y)));

  plot.append("text")
    .attr("x", innerW - 10)
    .attr("y", 20)
    .attr("text-anchor", "end")
    .attr("font-size", 12)
    .text(`y = ${slope.toFixed(1)}x + ${intercept.toFixed(0)}`);

  const legend = svg.append("g")
    .attr("class", "step2-legend")
    .attr("transform", `translate(${width - 220}, ${height - 120})`);

  [
    { label: "관측값", color: "#ff884d", type: "dot" },
    { label: "회귀선", color: "#111", type: "line" }
  ].forEach((d, i) => {
    const g = legend.append("g").attr("transform", `translate(0, ${i * 22})`);

    if (d.type === "dot") {
      g.append("circle").attr("cx", 10).attr("cy", 8).attr("r", 5).attr("fill", d.color);
    } else {
      g.append("line").attr("x1", 0).attr("x2", 20).attr("y1", 8).attr("y2", 8)
        .attr("stroke", d.color).attr("stroke-width", 2);
    }

    g.append("text")
      .attr("x", 26)
      .attr("y", 12)
      .attr("font-size", 12)
      .attr("fill", "#333")
      .text(d.label);
  });
}

/* ==============================
   STEP 3 – 원형 중첩 + 👤
============================== */
async function drawStep3Radial() {
  clearPlot();
  svg.selectAll(".crime-ratio-icons").remove();
  svg.selectAll(".step2-legend").remove();

  title.text("원형 중첩 그래프");
  subtitle.text("원형 반경은 피해 인구 수, 👤 크기는 범죄국 출국자 비율");

  gx.style("display", "none");
  gy.style("display", "none");
  xLabel.text("");
  yLabel.text("");

  const res = await fetch("/analysis/step3/");
  const { data, categories } = await res.json();

  const grouped = d3.rollups(
    data.filter(d => d.year <= currentYear),
    rows => {
      const obj = { year: rows[0].year };
      categories.forEach(c => obj[c] = d3.sum(rows, r => r[c]));
      return obj;
    },
    d => d.year
  );

  const filtered = grouped.map(d => d[1]);

  const center = plot.append("g")
    .attr("transform", `translate(${innerW / 2}, ${innerH / 2})`);

  const maxRadius = Math.min(innerW, innerH) * 0.42;

  const angle = d3.scaleBand().domain(categories).range([0, Math.PI * 2]);
  const angleCenter = d => angle(d) + angle.bandwidth() / 2;

  const valueMax = d3.max(filtered, d => d3.max(categories, c => d[c]));
  const radius = d3.scaleLinear().domain([0, valueMax]).range([0, maxRadius * scaleFactor]);

  [0.25, 0.5, 0.75, 1.0].forEach(p => {
    const v = Math.round(valueMax * p);
    center.append("circle").attr("r", radius(v)).attr("fill", "none")
      .attr("stroke", "#ddd").attr("stroke-dasharray", "3,3");
    center.append("text").attr("x", 4).attr("y", -radius(v)).attr("font-size", 11)
      .attr("fill", "#777").text(`약 ${d3.format(",")(v)}명`);
  });

  const radialLine = d3.lineRadial()
    .angle(d => angleCenter(d.category))
    .radius(d => radius(d.value))
    .curve(d3.curveLinearClosed);

  const color = d3.scaleOrdinal().domain(filtered.map(d => d.year)).range(d3.schemeTableau10);

  filtered.forEach(d => {
    const points = categories.map(k => ({ category: k, value: d[k] }));
    center.append("path")
      .datum(points)
      .attr("d", radialLine)
      .attr("fill", color(d.year))
      .attr("fill-opacity", 0.12)
      .attr("stroke", color(d.year))
      .attr("stroke-width", 2);
  });

  categories.forEach(c => {
    const a = angleCenter(c) - Math.PI / 2;
    const r = maxRadius + 26;
    center.append("text")
      .attr("x", Math.cos(a) * r)
      .attr("y", Math.sin(a) * r)
      .attr("text-anchor", "middle")
      .attr("font-size", 12)
      .text(c);
  });

  const iconGroup = svg.append("g")
    .attr("class", "crime-ratio-icons")
    .attr("transform", `translate(${width - 120}, ${margin.top + 80})`);

  const ratioData = DATA.years.map((yr, i) => ({
    year: yr,
    ratio: DATA.crime_ratio[i]
  })).filter(d => d.year <= currentYear);

  const iconSize = d3.scaleLinear()
    .domain(d3.extent(ratioData, d => d.ratio))
    .range([14, 36]);

  iconGroup.append("text")
    .attr("y", -16)
    .attr("font-size", 12)
    .attr("fill", "#666")

  iconGroup.selectAll(".person")
    .data(ratioData)
    .enter()
    .append("text")
    .attr("y", (d, i) => i * 38)
    .attr("font-size", d => iconSize(d.ratio))
    .text("👤");

  iconGroup.selectAll(".person-year")
    .data(ratioData)
    .enter()
    .append("text")
    .attr("x", 36)
    .attr("y", (d, i) => i * 38 + 12)
    .attr("font-size", 11)
    .text(d => d.year);
}

/* ==============================
   Render + Scroll
============================== */
function render(step) {
  currentStep = step;
  if (!DATA) return;

  if (step !== 0) svg.selectAll(".step1-legend").remove();
  if (step !== 2) svg.selectAll(".step2-legend").remove();
  if (step !== 2) svg.selectAll(".crime-ratio-icons").remove();

  if (step === 0) drawAbsolute(DATA);
  if (step === 1) drawRatio(DATA);
  if (step === 2) drawStep3Radial();
}

fetch("/analysis/data/")
  .then(res => res.json())
  .then(data => {
    DATA = data;
    render(0);

    const scroller = scrollama();
    scroller.setup({ step: "#sections .step", offset: 0.6 })
      .onStepEnter(r => render(+r.element.dataset.step))
      .onStepExit(r => {
        if (r.direction === "up")
          render(Math.max(0, +r.element.dataset.step - 1));
      });

    window.addEventListener("resize", scroller.resize);
  });
