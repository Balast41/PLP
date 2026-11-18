(() => {
  "use strict";

  const board = document.getElementById("board");
  const colImages = document.getElementById("col-images");
  const colWords = document.getElementById("col-words");
  const answersList = document.getElementById("answers-list");
  const nextButton = document.getElementById("next-exercise");
  const exerciseFrame = board.closest(".exercise-frame");

  let completedPairs = 0;
  let dragState = null;

  // Mélange de Fisher-Yates (non biaisé, contrairement à sort(random)).
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
    btn.setAttribute(
      "aria-label",
      side === "image" ? "Image à déplacer vers son mot" : `Mot à déplacer : ${pair.mot}`
    );

    if (side === "image") {
      if (isImagePath(pair.image)) {
        const img = document.createElement("img");
        img.src = pair.image;
        img.alt = "Image à associer";
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

    btn.addEventListener("pointerdown", (event) => startDrag(event, btn));
    return btn;
  }

  function startDrag(event, source) {
    if (source.disabled || event.button !== 0 || dragState) return;

    event.preventDefault();
    const rect = source.getBoundingClientRect();
    const ghost = source.cloneNode(true);
    ghost.classList.add("drag-ghost");
    ghost.style.width = `${rect.width}px`;
    ghost.style.height = `${rect.height}px`;
    document.body.append(ghost);

    dragState = {
      source,
      ghost,
      pointerId: event.pointerId,
      offsetX: event.clientX - rect.left - rect.width / 2,
      offsetY: event.clientY - rect.top - rect.height / 2,
      target: null
    };
    source.classList.add("dragging");
    source.setPointerCapture(event.pointerId);
    moveDrag(event);
  }

  function moveDrag(event) {
    if (!dragState || event.pointerId !== dragState.pointerId) return;

    const { ghost } = dragState;
    ghost.style.left = `${event.clientX - ghost.offsetWidth / 2 - dragState.offsetX}px`;
    ghost.style.top = `${event.clientY - ghost.offsetHeight / 2 - dragState.offsetY}px`;

    const element = document.elementFromPoint(event.clientX, event.clientY);
    const target = element?.closest(".item");
    const validTarget = target
      && target !== dragState.source
      && !target.disabled
      && target.dataset.side !== dragState.source.dataset.side
      ? target
      : null;

    if (dragState.target !== validTarget) {
      dragState.target?.classList.remove("drop-target");
      dragState.target = validTarget;
      dragState.target?.classList.add("drop-target");
    }
  }

  function finishDrag(event) {
    if (!dragState || event.pointerId !== dragState.pointerId) return;

    const { source, target, ghost } = dragState;
    target?.classList.remove("drop-target");
    source.classList.remove("dragging");
    ghost.remove();
    dragState = null;

    if (!target) return;
    if (source.dataset.id === target.dataset.id) {
      completePair(source, target);
      return;
    }

    source.classList.add("wrong");
    target.classList.add("wrong");
    setTimeout(() => {
      source.classList.remove("wrong");
      target.classList.remove("wrong");
    }, 400);
  }

  function cancelDrag(event) {
    if (!dragState || event.pointerId !== dragState.pointerId) return;
    const { source, target, ghost } = dragState;
    target?.classList.remove("drop-target");
    source.classList.remove("dragging");
    ghost.remove();
    dragState = null;
  }

  function completePair(first, second) {
    const imageEl = first.dataset.side === "image" ? first : second;
    const wordEl = first.dataset.side === "word" ? first : second;

    [imageEl, wordEl].forEach((el) => {
      el.disabled = true;
      el.classList.add("done");
    });

    const pair = document.createElement("div");
    pair.className = "answer-pair";
    pair.append(imageEl, wordEl);
    answersList.prepend(pair);
    completedPairs += 1;

    if (completedPairs === DATA.length) {
      nextButton.hidden = false;
    }
  }

  function start() {
    completedPairs = 0;
    nextButton.hidden = true;
    exerciseFrame.style.setProperty("--association-rows", DATA.length);
    colImages.innerHTML = "";
    colWords.innerHTML = "";
    answersList.innerHTML = "";

    shuffle(DATA).forEach((p) => colImages.append(makeItem(p, "image")));
    shuffle(DATA).forEach((p) => colWords.append(makeItem(p, "word")));
  }

  document.addEventListener("pointermove", moveDrag);
  document.addEventListener("pointerup", finishDrag);
  document.addEventListener("pointercancel", cancelDrag);
  nextButton.addEventListener("click", () => window.location.reload());

  start();
})();
