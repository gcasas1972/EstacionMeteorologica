const fields = {
  temperature_bmp_c: { label: "Temperatura BMP", unit: "°C", color: "#287c72" },
  temperature_dht_c: { label: "Temperatura DHT", unit: "°C", color: "#df8b38" },
  pressure_hpa: { label: "Presión atmosférica", unit: "hPa", color: "#5577bd" },
  air_humidity_percent: { label: "Humedad del aire", unit: "%", color: "#6d67b2" },
  soil_humidity_percent: { label: "Humedad del suelo", unit: "%", color: "#5b9b61" },
};

const canvas = document.querySelector("#chart");
const context = canvas.getContext("2d");
const metricSelect = document.querySelector("#metric");
const tableBody = document.querySelector("#measurements");
let data = [];

function drawChart() {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * ratio));
  canvas.height = Math.max(1, Math.floor(rect.height * ratio));
  context.setTransform(ratio, 0, 0, ratio, 0, 0);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 16, right: 18, bottom: 38, left: 58 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  context.clearRect(0, 0, width, height);

  const empty = document.querySelector("#empty-chart");
  if (!data.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  const key = metricSelect.value;
  const field = fields[key];
  const values = data.map((item) => Number(item[key]));
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    min -= 1;
    max += 1;
  } else {
    const gap = (max - min) * 0.12;
    min -= gap;
    max += gap;
  }

  context.font = "12px system-ui, sans-serif";
  context.textAlign = "right";
  context.textBaseline = "middle";
  for (let tick = 0; tick <= 4; tick += 1) {
    const y = padding.top + (plotHeight * tick) / 4;
    const value = max - ((max - min) * tick) / 4;
    context.strokeStyle = "#e9eef0";
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
    context.fillStyle = "#71808b";
    context.fillText(`${value.toFixed(1)} ${field.unit}`, padding.left - 9, y);
  }

  const x = (index) => padding.left + (data.length < 2 ? plotWidth / 2 : (plotWidth * index) / (data.length - 1));
  const y = (value) => padding.top + ((max - value) / (max - min)) * plotHeight;
  context.strokeStyle = field.color;
  context.lineWidth = 2.5;
  context.beginPath();
  values.forEach((value, index) => {
    if (index === 0) context.moveTo(x(index), y(value));
    else context.lineTo(x(index), y(value));
  });
  context.stroke();
  values.forEach((value, index) => {
    context.fillStyle = field.color;
    context.beginPath();
    context.arc(x(index), y(value), 3, 0, Math.PI * 2);
    context.fill();
  });

  const first = new Date(data[0].measured_at.replace(" ", "T"));
  const last = new Date(data[data.length - 1].measured_at.replace(" ", "T"));
  context.fillStyle = "#71808b";
  context.textAlign = "left";
  context.textBaseline = "top";
  context.fillText(first.toLocaleString("es-AR"), padding.left, height - padding.bottom + 13);
  context.textAlign = "right";
  context.fillText(last.toLocaleString("es-AR"), width - padding.right, height - padding.bottom + 13);
}

function renderTable() {
  tableBody.replaceChildren();
  for (const item of [...data].reverse()) {
    const row = document.createElement("tr");
    const values = [
      item.measured_at,
      `${Number(item.temperature_bmp_c).toFixed(2)} °C`,
      `${Number(item.temperature_dht_c).toFixed(2)} °C`,
      `${Number(item.pressure_hpa).toFixed(2)} hPa`,
      `${Number(item.air_humidity_percent).toFixed(2)} %`,
      Math.round(Number(item.soil_raw)),
      `${Number(item.soil_humidity_percent).toFixed(2)} %`,
    ];
    for (const value of values) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    tableBody.append(row);
  }
  document.querySelector("#count").textContent = `${data.length} registros`;
  document.querySelector("#empty-table").hidden = data.length > 0;
}

async function loadMeasurements() {
  const error = document.querySelector("#error");
  const status = document.querySelector("#status");
  try {
    const response = await fetch("/api/measurements?limit=200");
    if (!response.ok) throw new Error("No se pudo consultar la base de datos MySQL.");
    data = await response.json();
    renderTable();
    drawChart();
    error.hidden = true;
    status.textContent = "Base de datos conectada";
    status.className = "status online";
  } catch (reason) {
    error.textContent = reason.message;
    error.hidden = false;
    status.textContent = "Sin conexión";
    status.className = "status offline";
  }
}

metricSelect.addEventListener("change", drawChart);
window.addEventListener("resize", drawChart);
loadMeasurements();
window.setInterval(loadMeasurements, 5000);
