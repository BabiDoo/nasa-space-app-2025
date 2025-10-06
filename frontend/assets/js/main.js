
window.addEventListener('scroll', () => {
    const header = document.querySelector('header');
    if (window.scrollY > 0) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});
document.addEventListener('DOMContentLoaded', carregarQuiz);

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
const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animarContador("confirmedKepler", 100, 2000);
            observer.unobserve(entry.target); // Para não animar de novo
        }
        });
    }, {
        threshold: 0.6 // 60% do elemento visível
});

function getDadosKepler() {   
  let req = fetch('/kepler')
  let dado = req.then((response) => {
    return response.json()
  })
  
  dado.then((dado) => {
    document.getElementById('confirmedKepler').innerHTML = `${dado.confirmed} %` 
    document.getElementById('notKepler').innerHTML = `${dado.notconfirmed} %`
    document.getElementById('candidatesKepler').innerHTML = `${dado.candidates} %`

    document.getElementById('confirmedKepler').style.width = `${dado.confirmed}%`;
    document.getElementById('notBarKepler').style.width = `${dado.notconfirmed}%`;
    document.getElementById('candidateBarKepler').style.width = `${dado.candidates}%`;

    observer.observe(document.getElementById("confirmedKepler"));
    observer.observe(document.getElementById("notKepler"));
    observer.observe(document.getElementById("candidatesKepler"));

  })
}

function getDadosK2() {   
  let req = fetch('/K2')
  let dado = req.then((response) => {
    return response.json()
  })
  
  dado.then((dado) => {
    document.getElementById('confirmedK2').innerHTML = `${dado.confirmed} %` 
    document.getElementById('notK2').innerHTML = `${dado.notconfirmed} %`
    document.getElementById('candidatesK2').innerHTML = `${dado.candidates} %`

    document.getElementById('confirmedK2').style.width = `${dado.confirmed}%`;
    document.getElementById('notBarK2').style.width = `${dado.notconfirmed}%`;
    document.getElementById('candidateBarK2').style.width = `${dado.candidates}%`;

    observer.observe(document.getElementById("confirmedK2"));
    observer.observe(document.getElementById("notK2"));
    observer.observe(document.getElementById("candidatesK2"));
  })
}
function getDadosTess() {   
  let req = fetch('/Tess')
  let dado = req.then((response) => {
    return response.json()
  })
  
  dado.then((dado) => {
    document.getElementById('confirmedTess').innerHTML = `${dado.confirmed} %` 
    document.getElementById('notTess').innerHTML = `${dado.notconfirmed} %`
    document.getElementById('candidatesTess').innerHTML = `${dado.candidates} %`
     
    document.getElementById('confirmedBarTess').style.width = `${dado.confirmed}%`;
    document.getElementById('notBarTess').style.width = `${dado.notconfirmed}%`;
    document.getElementById('candidateBarTess').style.width = `${dado.candidates}%`;

    observer.observe(document.getElementById("confirmedTess"));
    observer.observe(document.getElementById("notTess"));
    observer.observe(document.getElementById("candidatesTess"));
  })
}

async function carregarQuiz() {
  try {
    const response = await fetch('assets/js/quiz.json');
    if (!response.ok) throw new Error("Erro ao carregar o JSON");

    const data = await response.json();
    iniciarQuiz(data.questions);
  } catch (error) {
    document.getElementById('quiz-container').textContent = "Erro ao carregar o quiz.";
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
  const container = document.getElementById('quiz-container');

  // Cria barra de progresso
  const progressBarContainer = document.createElement('div');
  progressBarContainer.className = 'progress-container';
  const progressBar = document.createElement('div');
  progressBar.className = 'progress-bar';
  progressBarContainer.appendChild(progressBar);
  container.appendChild(progressBarContainer);

  function atualizarProgresso() {
    const progresso = ((indice) / perguntasSelecionadas.length) * 100;
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
      const botao = document.createElement('button');
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
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

const hamburger = document.getElementById('hamburger-btn');
const navMenu = document.getElementById('nav-menu');
hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('open');
    hamburger.classList.toggle('open');
});