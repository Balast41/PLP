(() => {
  "use strict";

  // Délais (en millisecondes)
  const DELAI_CARTES_DIFFERENTES_MS = 900; // avant de recacher deux cartes différentes
  const DELAI_FIN_MS = 1200;               // avant de passer à la suite une fois fini

  const grid = document.getElementById("grid");

  let first = null;   // première carte retournée
  let locked = false; // bloque les clics pendant la comparaison
  let matched = 0;
  let totalPairs = 0;

  function shuffle(array) {
    const a = [...array];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  const isImagePath = (s) => /\.(png|jpe?g|gif|svg|webp)$/i.test(s);

  function fillFace(face, value, isImage) {
    if (isImage && isImagePath(value)) {
      const img = document.createElement("img");
      img.src = value;
      img.alt = "";
      face.append(img);
    } else {
      face.textContent = value;
      if (isImage) face.classList.add("emoji");
    }
  }

  function makeCard(card) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "card";
    btn.dataset.pair = card.pairId;
    btn.dataset.label = card.type === "image" ? "image" : card.content;
    btn.setAttribute("aria-label", "Carte face cachée");

    const inner = document.createElement("span");
    inner.className = "inner";
    const back = document.createElement("span");
    back.className = "face back";
    back.textContent = "?";
    const front = document.createElement("span");
    front.className = "face front";
    fillFace(front, card.content, card.type === "image");
    inner.append(back, front);
    btn.append(inner);

    btn.addEventListener("click", () => flip(btn));
    return btn;
  }

  function flip(card) {
    if (locked || card.classList.contains("flipped") || card.classList.contains("matched")) return;
    card.classList.add("flipped");
    card.setAttribute("aria-label", "Carte retournée : " + card.dataset.label);

    if (!first) { first = card; return; }

    const second = card;
    if (first.dataset.pair === second.dataset.pair) {
      [first, second].forEach((c) => c.classList.add("matched"));
      first = null;
      matched++;
      if (matched === totalPairs) {
        locked = true;
        setTimeout(goNext, DELAI_FIN_MS);
      }
    } else {
      locked = true; // verrou : évite de retourner une 3e carte
      const a = first;
      first = null;
      setTimeout(() => {
        [a, second].forEach((c) => {
          c.classList.remove("flipped");
          c.setAttribute("aria-label", "Carte face cachée");
        });
        locked = false;
      }, DELAI_CARTES_DIFFERENTES_MS);
    }
  }

  function goNext() {
    if (typeof SUIVANT === "string" && SUIVANT) window.location.href = SUIVANT;
    else start();
  }

  function start() {
    first = null; locked = false; matched = 0;
    totalPairs = Math.min(NB_PAIRES, DATA.length);

    // On tire les paires, puis chaque paire donne 2 cartes (image + mot)
    const chosen = shuffle(DATA).slice(0, totalPairs);
    const cards = chosen.flatMap((p) => [
      { pairId: p.id, type: "image", content: p.image },
      { pairId: p.id, type: "word", content: p.mot }
    ]);
    grid.innerHTML = "";
    shuffle(cards).forEach((c) => grid.append(makeCard(c)));
  }

  start();
})();
