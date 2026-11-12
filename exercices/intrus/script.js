(() => {
  "use strict";

  // Pause avant de passer à la question suivante (en millisecondes)
  const DELAI_MS = 1500;

  const choicesEl = document.getElementById("choices");
  const progressEl = document.getElementById("progress");
  const srEl = document.getElementById("sr");

  let questions = [];
  let index = 0;

  function shuffle(array) {
    const a = [...array];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  const isImagePath = (s) => /\.(png|jpe?g|gif|svg|webp)$/i.test(s);

  // Normalise un élément de données (texte, emoji, chemin d'image ou { image, alt })
  // en { image, text, label } où label sert aux lecteurs d'écran.
  function normalize(item) {
    if (item && typeof item === "object") {
      return { image: item.image, text: item.texte || "", label: item.alt || item.texte || "image" };
    }
    if (isImagePath(item)) return { image: item, text: "", label: "image" };
    return { image: null, text: item, label: item };
  }

  // Construit les 5 propositions d'une question. Le booléen isIntrus identifie
  // la bonne réponse sans comparer de texte (utile quand ce sont des images).
  function buildChoices(q) {
    if (!Array.isArray(q.memes) || q.memes.length !== 4) {
      console.warn("Question à corriger : il faut exactement 4 éléments dans « memes »", q);
    }
    const items = [
      ...q.memes.map((m) => ({ ...normalize(m), isIntrus: false })),
      { ...normalize(q.intrus), isIntrus: true }
    ];
    return shuffle(items); // l'intrus change de place à chaque fois
  }

  function makeButton(item) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "choice";
    btn.dataset.intrus = item.isIntrus ? "1" : "0";

    if (item.image) {
      const img = document.createElement("img");
      img.src = item.image;
      img.alt = item.label;
      btn.append(img);
    } else {
      btn.textContent = item.text;
    }
    btn.addEventListener("click", () => answer(item));
    btn._item = item;
    return btn;
  }

  function showQuestion() {
    progressEl.textContent = `Question ${index + 1} / ${questions.length}`;
    srEl.textContent = "";
    choicesEl.innerHTML = "";
    buildChoices(questions[index]).forEach((item) => choicesEl.append(makeButton(item)));
  }

  function answer(item) {
    const buttons = [...choicesEl.children];

    // On verrouille les boutons et on met seulement la bonne réponse en évidence
    buttons.forEach((b) => {
      b.disabled = true;
      if (b._item.isIntrus) b.classList.add("correct");
    });

    const intrus = buttons.find((b) => b._item.isIntrus)._item;
    srEl.textContent = item.isIntrus
      ? "Bonne réponse."
      : `L'intrus était : ${intrus.label}.`;

    setTimeout(next, DELAI_MS);
  }

  function next() {
    index++;
    if (index < questions.length) return showQuestion();
    // Fin de l'exercice : exercice suivant, ou nouveau tour
    if (typeof SUIVANT === "string" && SUIVANT) window.location.href = SUIVANT;
    else start();
  }

  function start() {
    questions = shuffle(DATA);
    index = 0;
    showQuestion();
  }

  start();
})();
