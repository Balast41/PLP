(() => {
  "use strict";

  // Si la dernière paire a dû être corrigée, on laisse l'élève la voir un instant.
  const DELAI_APRES_CORRECTION_MS = 1500;

  const board = document.getElementById("board");
  const colImages = document.getElementById("col-images");
  const colWords = document.getElementById("col-words");
  const svg = document.getElementById("lines");

  let selected = null; // bouton actuellement sélectionné
  let matches = [];    // [{ imgEl, wordEl, color }]

  // Mélange de Fisher-Yates (non biaisé, contrairement à sort(random))
  function shuffle(array) {
    const a = [...array];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  const isImagePath = (s) => /\.(png|jpe?g|gif|svg|webp)$/i.test(s);

  function makeItem(pair, side) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "item " + side;
    btn.dataset.id = pair.id;
    btn.dataset.side = side;

    if (side === "image") {
      if (isImagePath(pair.image)) {
        const img = document.createElement("img");
        img.src = pair.image;
        img.alt = "Image à associer"; // ne pas révéler la réponse
        btn.append(img);
      } else {
        const span = document.createElement("span");
        span.className = "emoji";
        span.setAttribute("role", "img");
        span.setAttribute("aria-label", "Image à associer");
        span.textContent = pair.image;
        btn.append(span);
      }
    } else {
      btn.textContent = pair.mot;
    }
    btn.addEventListener("click", () => choose(btn));
    return btn;
  }

  function select(btn) {
    selected = btn;
    btn.classList.add("selected");
  }

  function deselect() {
    if (selected) selected.classList.remove("selected");
    selected = null;
  }

  function choose(btn) {
    if (btn.disabled) return;

    if (!selected) return select(btn);
    if (selected === btn) return deselect();
    // Même colonne : on change simplement de sélection
    if (selected.dataset.side === btn.dataset.side) {
      deselect();
      return select(btn);
    }

    const first = selected;
    deselect();
    if (first.dataset.id === btn.dataset.id) {
      link(first, btn, false);
    } else {
      onWrong(first, btn);
    }
  }

  // Erreur : on montre tout de suite la bonne réponse pour l'élément choisi en premier
  function onWrong(first, clicked) {
    clicked.classList.add("wrong");
    setTimeout(() => clicked.classList.remove("wrong"), 400);

    const otherCol = first.dataset.side === "image" ? colWords : colImages;
    const partner = otherCol.querySelector(`.item[data-id="${first.dataset.id}"]`);
    link(first, partner, true);
  }

  // Relie deux éléments (association réussie ou corrigée)
  function link(a, b, corrected) {
    const imgEl = a.dataset.side === "image" ? a : b;
    const wordEl = a.dataset.side === "word" ? a : b;
    // Corrigée : orange, pour la distinguer d'une association réussie par l'élève
    const color = corrected
      ? "hsl(28 90% 48%)"
      : `hsl(${(matches.length * 47 + 200) % 360} 65% 45%)`;

    [imgEl, wordEl].forEach((el) => {
      el.disabled = true;
      el.classList.add("done");
      if (corrected) el.classList.add("corrected");
      el.style.setProperty("--c", color);
    });
    matches.push({ imgEl, wordEl, color });
    drawLines();

    if (matches.length === DATA.length) {
      // Passage direct à la suite, sans message ni animation
      setTimeout(goNext, corrected ? DELAI_APRES_CORRECTION_MS : 0);
    }
  }

  function goNext() {
    if (typeof SUIVANT === "string" && SUIVANT) window.location.href = SUIVANT;
    else start();
  }

  // Dessine un trait SVG par association
  function drawLines() {
    svg.innerHTML = "";
    const base = board.getBoundingClientRect();
    matches.forEach(({ imgEl, wordEl, color }) => {
      const r1 = imgEl.getBoundingClientRect();
      const r2 = wordEl.getBoundingClientRect();
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", r1.right - base.left);
      line.setAttribute("y1", r1.top + r1.height / 2 - base.top);
      line.setAttribute("x2", r2.left - base.left);
      line.setAttribute("y2", r2.top + r2.height / 2 - base.top);
      line.setAttribute("stroke", color);
      line.setAttribute("stroke-width", "4");
      line.setAttribute("stroke-linecap", "round");
      svg.append(line);
    });
  }

  function start() {
    selected = null;
    matches = [];
    svg.innerHTML = "";
    colImages.innerHTML = "";
    colWords.innerHTML = "";
    // Chaque colonne est mélangée séparément
    shuffle(DATA).forEach((p) => colImages.append(makeItem(p, "image")));
    shuffle(DATA).forEach((p) => colWords.append(makeItem(p, "word")));
  }

  // Les traits dépendent de la taille de l'écran : on les redessine
  window.addEventListener("resize", drawLines);
  if (window.ResizeObserver) new ResizeObserver(drawLines).observe(board);

  start();
})();
