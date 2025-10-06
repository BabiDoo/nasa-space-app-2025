const API_URL = "127.0.0.1/api";

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

function animarContador(id, valorFinal, duracao) {
  const elemento = document.getElementById(id);
  let inicio = 0;
  const incremento = valorFinal / (duracao / 16); // Aproximadamente 60 FPS
  const atualizar = () => {
    inicio += incremento;
    if (inicio >= valorFinal) {
      elemento.textContent = valorFinal;
    } else {
      elemento.textContent = Math.floor(inicio);
      requestAnimationFrame(atualizar);
    }
  };
  requestAnimationFrame(atualizar);
}

// Observa quando o contador entra na tela
const observer = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animarContador("confirmedKepler", 100, 2000);
        observer.unobserve(entry.target); // Para não animar de novo
      }
    });
  },
  {
    threshold: 0.6, // 60% do elemento visível
  }
);

function getDadosKepler() {
  let req = fetch("/kepler");
  let dado = req.then((response) => {
    return response.json();
  });

  dado.then((dado) => {
    document.getElementById(
      "confirmedKepler"
    ).innerHTML = `${dado.confirmed} %`;
    document.getElementById("notKepler").innerHTML = `${dado.notconfirmed} %`;
    document.getElementById(
      "candidatesKepler"
    ).innerHTML = `${dado.candidates} %`;

    document.getElementById(
      "confirmedKepler"
    ).style.width = `${dado.confirmed}%`;
    document.getElementById(
      "notBarKepler"
    ).style.width = `${dado.notconfirmed}%`;
    document.getElementById(
      "candidateBarKepler"
    ).style.width = `${dado.candidates}%`;

    observer.observe(document.getElementById("confirmedKepler"));
    observer.observe(document.getElementById("notKepler"));
    observer.observe(document.getElementById("candidatesKepler"));
  });
}

function getDadosK2() {
  let req = fetch("/K2");
  let dado = req.then((response) => {
    return response.json();
  });

  dado.then((dado) => {
    document.getElementById("confirmedK2").innerHTML = `${dado.confirmed} %`;
    document.getElementById("notK2").innerHTML = `${dado.notconfirmed} %`;
    document.getElementById("candidatesK2").innerHTML = `${dado.candidates} %`;

    document.getElementById("confirmedK2").style.width = `${dado.confirmed}%`;
    document.getElementById("notBarK2").style.width = `${dado.notconfirmed}%`;
    document.getElementById(
      "candidateBarK2"
    ).style.width = `${dado.candidates}%`;

    observer.observe(document.getElementById("confirmedK2"));
    observer.observe(document.getElementById("notK2"));
    observer.observe(document.getElementById("candidatesK2"));
  });
}
function getDadosTess() {
  let req = fetch("/Tess");
  let dado = req.then((response) => {
    return response.json();
  });

  dado.then((dado) => {
    document.getElementById("confirmedTess").innerHTML = `${dado.confirmed} %`;
    document.getElementById("notTess").innerHTML = `${dado.notconfirmed} %`;
    document.getElementById(
      "candidatesTess"
    ).innerHTML = `${dado.candidates} %`;

    document.getElementById(
      "confirmedBarTess"
    ).style.width = `${dado.confirmed}%`;
    document.getElementById("notBarTess").style.width = `${dado.notconfirmed}%`;
    document.getElementById(
      "candidateBarTess"
    ).style.width = `${dado.candidates}%`;

    observer.observe(document.getElementById("confirmedTess"));
    observer.observe(document.getElementById("notTess"));
    observer.observe(document.getElementById("candidatesTess"));
  });
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

// async function getMissions() {
//   const res = await fetch(`${API_URL}/missions`);
//   return await res.json();
// }

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
