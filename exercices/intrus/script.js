(() => {
  "use strict";

  // Pause avant de passer à la question suivante (en millisecondes)
  const DELAI_MS = 1500;

  const choicesEl = document.getElementById("choices");
  const progressEl = document.getElementById("progress");
  const srEl = document.getElementById("sr");
  const nextButton = document.getElementById("next-exercise");

  let questions = [];
  let index = 0;
  let exercise = null;

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

  function isSameChoice(left, right) {
    if (left === right) return true;
    if (left && right && typeof left === "object" && typeof right === "object") {
      return left.image === right.image;
    }
    return normalize(left).label === normalize(right).label;
  }

  // Construit les 5 propositions d'une question. Le booléen isIntrus identifie
  // la bonne réponse sans comparer de texte (utile quand ce sont des images).
  function buildChoices(q) {
    if (!Array.isArray(q.memes) || q.memes.length < 1) {
      console.warn("Question à corriger : il faut au moins un élément dans « memes »", q);
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

    buttons.forEach((b) => {
      b.disabled = true;
      const isIntrus = exercise
        ? isSameChoice(
            b._item.image ? { image: b._item.image, alt: b._item.label } : b._item.text,
            exercise.bonne_reponse
          )
        : b._item.isIntrus;
      if (isIntrus) b.classList.add("correct");
    });

    const intrus = exercise
      ? exercise.bonne_reponse
      : buttons.find((b) => b._item.isIntrus)._item.label;
    const isCorrect = exercise
      ? isSameChoice(
          item.image ? { image: item.image, alt: item.label } : item.text,
          exercise.bonne_reponse
        )
      : item.isIntrus;
    srEl.textContent = isCorrect
      ? "Bonne réponse."
      : `L'intrus était : ${typeof intrus === "string" ? intrus : intrus.alt || intrus.image}.`;

    nextButton.hidden = false;
  }

  function next() {
    nextButton.hidden = true;
    index++;
    if (index < questions.length) return showQuestion();

  }

  async function start() {
    index = 0;
    nextButton.hidden = true;
    try {
      exercise = await ExerciseGenerator.generate("intrus");
      questions = [{
        memes: exercise.propositions.filter((choice) => choice !== exercise.bonne_reponse),
        intrus: exercise.bonne_reponse
      }];
    } catch (error) {
      console.warn("Générateur indisponible, données locales utilisées.", error);
      exercise = null;
      questions = shuffle(DATA);
    }
    showQuestion();
  }
  nextButton.addEventListener("click", () => {
    if (index < questions.length - 1) {
      next();
    } else{
      window.location.reload();
    }
  });

  start();
})();