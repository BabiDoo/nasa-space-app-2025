const API_URL = "localhost:8000/api";
const MISSION_STATS_ENDPOINT = `${API_URL}/mission-stats`;

window.addEventListener("scroll", () => {
  const header = document.querySelector("header");
  if (window.scrollY > 0) {
    header.classList.add("scrolled");
  } else {
    header.classList.remove("scrolled");
  }
});
document.addEventListener("DOMContentLoaded", carregarQuiz);
document.addEventListener("DOMContentLoaded", () => {
  // Initialize the dynamic database stats (progress bars)
  initMissionStats();
});
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggle-search-btn");
  const formWrapper = document.getElementById("search-form");
  const form = document.getElementById("exoplanet-search-form");

  if (toggleBtn && formWrapper) {
    toggleBtn.addEventListener("click", () => {
      const isHidden = formWrapper.classList.toggle("hidden");
      toggleBtn.setAttribute("aria-expanded", String(!isHidden));
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const params = {};
      const data = new FormData(form);
      for (const [key, value] of data.entries()) {
        if (value !== null && String(value).trim() !== "") {
          params[key] = value;
        }
      }

      try {
        const results = await getExo(params);
        renderSearchResults(results);
        scrollToElemen("results");
      } catch (err) {
        console.error("Failed to fetch exoplanets", err);
      }
    });
  }
});

function animarContador(
  id,
  valorFinal,
  duracao = 1200,
  prefix = "",
  suffix = ""
) {
  const elemento = document.getElementById(id);
  if (!elemento) return;
  let inicio = 0;
  const incremento = valorFinal / (duracao / 16); // Aproximadamente 60 FPS
  const atualizar = () => {
    inicio += incremento;
    if (inicio >= valorFinal) {
      elemento.textContent = `${prefix}${Math.round(valorFinal)}${suffix}`;
    } else {
      elemento.textContent = `${prefix}${Math.floor(inicio)}${suffix}`;
      requestAnimationFrame(atualizar);
    }
  };
  requestAnimationFrame(atualizar);
}

// ===== Databases: dynamic progress bars =====
const MISSION_UI = {
  Kepler: {
    values: {
      confirmed: "confirmedKepler",
      not_planet: "notKepler",
      candidate: "candidatesKepler",
    },
    bars: {
      confirmed: "confirmedBarKepler",
      not_planet: "notBarKepler",
      candidate: "candidateBarKepler",
    },
  },
  K2: {
    values: {
      confirmed: "confirmedK2",
      not_planet: "notK2",
      candidate: "candidatesK2",
    },
    bars: {
      confirmed: "confirmedBarK2",
      not_planet: "notBarK2",
      candidate: "candidateBarK2",
    },
  },
  TESS: {
    values: {
      confirmed: "confirmedTess",
      not_planet: "notTess",
      candidate: "candidatesTess",
    },
    bars: {
      confirmed: "confirmedBarTess",
      not_planet: "notBarTess",
      candidate: "candidateBarTess",
    },
  },
};

function normalizeMissionKey(name) {
  if (!name) return name;
  const n = String(name).trim().toLowerCase();
  if (n === "k2") return "K2";
  if (n === "tess") return "TESS";
  if (n === "kepler") return "Kepler";
  return name;
}

function computePercentsFromTotals(totals) {
  const confirmed = Number(totals.confirmed || 0);
  const notp = Number(
    totals.not_planet || totals.not || totals.notconfirmed || 0
  );
  const candidate = Number(totals.candidate || totals.candidates || 0);
  const sum = confirmed + notp + candidate;
  if (!sum) return { confirmed: 0, not_planet: 0, candidate: 0 };
  return {
    confirmed: Math.round((confirmed / sum) * 100),
    not_planet: Math.round((notp / sum) * 100),
    candidate: Math.round((candidate / sum) * 100),
  };
}

function normalizeMissionStats(raw) {
  // Expected shapes supported:
  // 1) { missions: [{ mission: 'Kepler', totals: { confirmed, not_planet, candidate }, percents?: {...} }, ...] }
  // 2) { kepler: { percents|totals }, k2: {...}, tess: {...} }
  const out = [];
  if (!raw) return out;
  if (Array.isArray(raw.missions)) {
    for (const m of raw.missions) {
      const key = normalizeMissionKey(m.mission);
      const percents =
        m.percents || computePercentsFromTotals(m.totals || m.counts || {});
      out.push({ mission: key, percents });
    }
    return out;
  }
  // object map style
  for (const k of Object.keys(raw)) {
    const key = normalizeMissionKey(k);
    const v = raw[k] || {};
    const percents =
      v.percents || computePercentsFromTotals(v.totals || v.counts || {});
    out.push({ mission: key, percents });
  }
  return out;
}

async function getMissionStats() {
  try {
    const res = await fetch(MISSION_STATS_ENDPOINT);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return normalizeMissionStats(data);
  } catch (e) {
    // Mock fallback so the UI works before the API exists
    return getMockMissionStats();
  }
}

function getMockMissionStats() {
  return [
    {
      mission: "Kepler",
      percents: { confirmed: 62, not_planet: 28, candidate: 10 },
    },
    {
      mission: "K2",
      percents: { confirmed: 48, not_planet: 32, candidate: 20 },
    },
    {
      mission: "TESS",
      percents: { confirmed: 41, not_planet: 36, candidate: 23 },
    },
  ];
}

async function initMissionStats() {
  const stats = await getMissionStats();
  if (!Array.isArray(stats) || stats.length === 0) return;

  // Animate numbers only once when visible
  const seen = new Set();
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.id;
        if (seen.has(id)) return;
        const targetValue =
          Number(entry.target.getAttribute("data-target")) || 0;
        animarContador(id, targetValue, 1000, "", " %");
        seen.add(id);
        io.unobserve(entry.target);
      });
    },
    { threshold: 0.5 }
  );

  for (const m of stats) {
    const ui = MISSION_UI[m.mission];
    if (!ui) continue;
    const p = m.percents || {};
    // Set text values (with data-target for animation) and bar widths
    for (const key of ["confirmed", "not_planet", "candidate"]) {
      const valueId = ui.values[key];
      const barId = ui.bars[key];
      const percent = Math.max(0, Math.min(100, Number(p[key] || 0)));

      const valueEl = document.getElementById(valueId);
      const barEl = document.getElementById(barId);
      if (valueEl) {
        valueEl.textContent = "0 %"; // start from 0 for animation
        valueEl.setAttribute("data-target", String(Math.round(percent)));
        io.observe(valueEl);
      }
      if (barEl) {
        // Let CSS transition animate the width
        requestAnimationFrame(() => {
          barEl.style.width = `${percent}%`;
        });
      }
    }
  }
}

async function carregarQuiz() {
  try {
    const response = await fetch("assets/js/quiz.json");
    if (!response.ok) throw new Error("Erro ao carregar o JSON");

    const data = await response.json();
    iniciarQuiz(data.questions);
  } catch (error) {
    document.getElementById("quiz-container").textContent =
      "Erro ao carregar o quiz.";
    console.error(error);
  }
}

function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

function iniciarQuiz(perguntas) {
  const perguntasSelecionadas = shuffle([...perguntas]).slice(0, 10);
  let indice = 0;
  let pontuacao = 0;
  const resultados = [];
  const container = document.getElementById("quiz-container");

  // Cria barra de progresso
  const progressBarContainer = document.createElement("div");
  progressBarContainer.className = "progress-container";
  const progressBar = document.createElement("div");
  progressBar.className = "progress-bar";
  progressBarContainer.appendChild(progressBar);
  container.appendChild(progressBarContainer);

  function atualizarProgresso() {
    const progresso = (indice / perguntasSelecionadas.length) * 100;
    progressBar.style.width = `${progresso}%`;
  }

  function mostrarPergunta() {
    if (indice >= perguntasSelecionadas.length) {
      mostrarResultadoFinal();
      return;
    }

    const atual = perguntasSelecionadas[indice];
    container.innerHTML = `
      <div class="question-box">
        <h2> ${indice + 1} / ${perguntasSelecionadas.length}</h2>
        <p><strong>${atual.question}</strong></p>
      </div>
    `;

    // adiciona a barra novamente (recriada no innerHTML)
    container.prepend(progressBarContainer);
    atualizarProgresso();

    atual.answerOptions.forEach((opcao) => {
      const botao = document.createElement("button");
      botao.textContent = opcao.text;
      botao.onclick = () => {
        const correta = opcao.isCorrect;
        resultados.push({ pergunta: atual.question, correta });
        if (correta) pontuacao++;
        indice++;
        mostrarPergunta();
      };
      container.appendChild(botao);
    });
  }

  function mostrarResultadoFinal() {
    container.innerHTML = `
    <h2>Final Result</h2>
    <p>You got <strong>${pontuacao}</strong> out of <strong>${perguntasSelecionadas.length}</strong> questions!</p>
    <button class="finish-btn" onclick="location.reload()">Refresh</button>
  `;
  }
  mostrarPergunta();
}

function scrollToElemen(sec) {
  const section = document.getElementById(sec);
  if (section) {
    section.scrollIntoView({ behavior: "smooth" });
  }
}

const hamburger = document.getElementById("hamburger-btn");
const navMenu = document.getElementById("nav-menu");
hamburger.addEventListener("click", () => {
  navMenu.classList.toggle("open");
  hamburger.classList.toggle("open");
});

async function getExo(params) {
  const queryParams = new URLSearchParams(params);
  const res = await fetch(`${API_URL}/catalog?${queryParams.toString()}`);
  return await res.json();
}

function renderSearchResults(response) {
  const container = document.getElementById("search-results");
  if (!container) return;

  const {
    items = [],
    page = 1,
    page_size = items.length || 0,
    total = 0,
  } = response || {};

  if (!Array.isArray(items) || items.length === 0) {
    container.innerHTML = `<p class="text">No results found.</p>`;
    return;
  }

  const headers = [
    { key: "mission", label: "Mission" },
    { key: "object_id", label: "Object ID" },
    { key: "alt_designations", label: "Alt. Designations" },
    { key: "final_classification", label: "Final Classification" },
    { key: "final_confidence", label: "Confidence" },
    { key: "longitude", label: "Longitude" },
    { key: "latitude", label: "Latitude" },
    { key: "stellar_temperature", label: "Teff (K)" },
    { key: "stellar_radius", label: "R★ (R☉)" },
    { key: "planet_radius", label: "Rₚ (R⊕)" },
    { key: "eq_temperature", label: "T_eq (K)" },
    { key: "distance", label: "Distance (pc)" },
    { key: "stellar_sur_gravity", label: "log g" },
    { key: "orbital_period", label: "Period (d)" },
    { key: "insol_flux", label: "Flux (F⊕)" },
    { key: "depth", label: "Depth (ppm)" },
  ];

  const tableHead = `
    <thead>
      <tr>
        ${headers.map((h) => `<th>${h.label}</th>`).join("")}
      </tr>
    </thead>
  `;
  const tableBody = `
    <tbody>
      ${items
        .map((it) => {
          return `<tr>
              ${headers
                .map(({ key }) => {
                  const v = it[key];
                  if (v === null || v === undefined) return `<td>-</td>`;
                  const isNum = typeof v === "number";
                  const formatted = isNum
                    ? Number(v).toLocaleString()
                    : String(v);
                  return `<td>${formatted}</td>`;
                })
                .join("")}
            </tr>`;
        })
        .join("")}
    </tbody>
  `;

  const totalPages = page_size ? Math.ceil(total / page_size) : 1;
  const pager = `
    <div class="pager">
      <button class="btn pager-btn" data-page="${Math.max(1, page - 1)}" ${
    page <= 1 ? "disabled" : ""
  }>Prev</button>
      <span class="pager-info">Page ${page} of ${totalPages} (${total.toLocaleString()} results)</span>
      <button class="btn pager-btn" data-page="${Math.min(
        totalPages,
        page + 1
      )}" ${page >= totalPages ? "disabled" : ""}>Next</button>
    </div>
  `;

  container.innerHTML = `
    <div class="table-wrap">
      <table class="results-table">${tableHead}${tableBody}</table>
    </div>
    ${pager}
  `;

  // Attach pagination events to re-query using the current form values
  container.querySelectorAll(".pager-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const targetPage = Number(e.currentTarget.getAttribute("data-page"));
      const form = document.getElementById("exoplanet-search-form");
      if (!form) return;
      const data = new FormData(form);
      const params = {};
      for (const [key, value] of data.entries()) {
        if (value !== null && String(value).trim() !== "") params[key] = value;
      }
      params.page = targetPage;
      params.page_size = page_size || 50;
      try {
        const resp = await getExo(params);
        renderSearchResults(resp);
        scrollToElemen("results");
      } catch (err) {
        console.error("Pagination fetch failed", err);
      }
    });
  });
}
