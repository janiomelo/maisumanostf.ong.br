function startCountdown() {
  const box = document.querySelector('.countdown-box');
  if (!box) return;

  const targetRaw = box.dataset.alvo;
  const target = new Date(targetRaw);
  if (Number.isNaN(target.getTime())) return;

  const daysEl = document.getElementById('cdDays');
  const hoursEl = document.getElementById('cdHours');
  const minEl = document.getElementById('cdMinutes');
  const secEl = document.getElementById('cdSeconds');

  const tick = () => {
    const now = new Date();
    let diff = Math.floor((target - now) / 1000);
    if (diff < 0) diff = 0;

    const days = Math.floor(diff / 86400);
    diff -= days * 86400;
    const hours = Math.floor(diff / 3600);
    diff -= hours * 3600;
    const mins = Math.floor(diff / 60);
    const secs = diff - mins * 60;

    daysEl.textContent = String(days);
    hoursEl.textContent = String(hours).padStart(2, '0');
    minEl.textContent = String(mins).padStart(2, '0');
    secEl.textContent = String(secs).padStart(2, '0');
  };

  tick();
  setInterval(tick, 1000);
}

function startRepresentationChart() {
  const canvas = document.getElementById('representationChart');
  const payload = window.homeChartPayload;
  if (!canvas || !payload || !window.Chart) return;

  const styles = getComputedStyle(document.documentElement);
  const axisColor = styles.getPropertyValue('--border').trim() || '#d4d9e1';
  const textColor = styles.getPropertyValue('--text').trim() || '#1a1a1a';
  const mutedColor = styles.getPropertyValue('--muted').trim() || '#5a5a5a';
  const campaignColor = styles.getPropertyValue('--ok').trim() || '#155724';
  const gridColor = 'rgba(128, 136, 149, .22)';

  const datasetByKey = Object.fromEntries(payload.datasets.map((item) => [item.key, item]));

  const formatFractionYear = (value) => {
    const year = Math.floor(value);
    const fraction = value - year;
    const month = Math.max(1, Math.min(12, Math.round(fraction * 12) + 1));
    return `${String(month).padStart(2, '0')}/${year}`;
  };

  const annotatePlugin = {
    id: 'campaignAnnotations',
    afterDatasetsDraw(chart) {
      const annotations = payload.annotations || [];
      if (!annotations.length) return;

      const { ctx, scales, chartArea } = chart;
      ctx.save();
      ctx.font = '13px Georgia, serif';
      ctx.textBaseline = 'middle';

      annotations.forEach((item, index) => {
        const x = scales.x.getPixelForValue(item.x);
        const y = scales.y.getPixelForValue(item.y);
        const text = item.text;
        const paddingX = 8;
        const h = 24;
        const w = ctx.measureText(text).width + (paddingX * 2);
        const offsetY = index === 1 ? -14 : -30;
        const preferredX = x + 10;
        const maxLeft = chartArea.right - w - 8;
        const minLeft = chartArea.left + 8;
        const boxX = Math.max(minLeft, Math.min(maxLeft, preferredX));
        const boxY = Math.max(chartArea.top + 6, y + offsetY - 12);

        ctx.fillStyle = 'rgba(255, 255, 255, .88)';
        ctx.strokeStyle = 'rgba(120, 130, 145, .55)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(boxX, boxY, w, h, 6);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = textColor;
        ctx.fillText(text, boxX + paddingX, boxY + (h / 2));
      });

      ctx.restore();
    },
  };

  new Chart(canvas, {
    type: 'line',
    data: {
      datasets: [
        {
          label: datasetByKey.history.label,
          data: datasetByKey.history.data,
          parsing: false,
          borderColor: '#6f7785',
          stepped: false,
          borderWidth: 2.2,
          pointRadius: 1.4,
          pointHoverRadius: 4,
          tension: 0.24,
          cubicInterpolationMode: 'monotone',
        },
        {
          label: datasetByKey.inertia.label,
          data: datasetByKey.inertia.data,
          parsing: false,
          borderColor: 'rgba(178, 59, 59, .88)',
          stepped: false,
          borderWidth: 2,
          borderDash: [7, 6],
          pointRadius: 1.5,
          pointHoverRadius: 4,
          tension: 0.24,
          cubicInterpolationMode: 'monotone',
        },
        {
          label: datasetByKey.campaign.label,
          data: datasetByKey.campaign.data,
          parsing: false,
          borderColor: campaignColor,
          borderDash: [7, 6],
          stepped: false,
          borderWidth: 2,
          pointRadius: 1.5,
          pointHoverRadius: 4,
          tension: 0.24,
          cubicInterpolationMode: 'monotone',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 20,
          right: 24,
          bottom: 6,
          left: 4,
        },
      },
      interaction: {
        mode: 'nearest',
        intersect: false,
      },
      scales: {
        x: {
          type: 'linear',
          min: payload.xMin,
          max: payload.xMax,
          grid: { color: gridColor },
          ticks: {
            color: mutedColor,
            callback: (value) => {
              if (Number.isInteger(value) && value % 2 === 0) return String(value);
              return '';
            },
            maxTicksLimit: 12,
          },
          title: {
            display: true,
            text: 'Ano',
            color: textColor,
          },
        },
        y: {
          min: payload.yMin,
          max: payload.yMax,
          grid: { color: gridColor },
          ticks: {
            color: mutedColor,
            stepSize: 1,
            precision: 0,
            callback: (value) => (Number.isInteger(value) ? String(value) : ''),
            maxTicksLimit: 5,
          },
          title: {
            display: true,
            text: 'Número de ministras',
            color: textColor,
          },
        },
      },
      plugins: {
        legend: {
          display: false,
          labels: {
            color: textColor,
            boxWidth: 24,
            usePointStyle: true,
            pointStyle: 'line',
          },
        },
        tooltip: {
          callbacks: {
            title: (items) => `Data: ${formatFractionYear(items[0].raw.x)}`,
            label: (context) => `${context.dataset.label}: ${context.raw.y}`,
          },
        },
      },
    },
    plugins: [annotatePlugin],
  });
}

document.addEventListener('DOMContentLoaded', () => {
  startCountdown();
  startRepresentationChart();
});