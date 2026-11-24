(() => {
  "use strict";

  const templates = new Map();

  function shuffle(array) {
    const result = [...array];
    for (let i = result.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }

  async function loadTemplate(type) {
    if (templates.has(type)) return templates.get(type);
    const response = await fetch(`/generateur/donnees/${type}.json`);
    if (!response.ok) throw new Error(`Catalogue ${type} indisponible.`);
    const template = await response.json();
    templates.set(type, template);
    return template;
  }

  function identifier() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    return `${Date.now().toString(16)}-${Math.random().toString(16).slice(2)}`;
  }

  async function generateAssociation(difficulty) {
    const template = await loadTemplate("association");
    const model = template.modeles[Math.floor(Math.random() * template.modeles.length)];
    const count = template.difficultes[String(difficulty)].nombre_paires;
    const pairs = shuffle([...model.paires]).slice(0, count);
    const elements = shuffle(pairs.map(([left]) => left));
    const correspondances = shuffle(pairs.map(([, right]) => right));

    return {
      identifiant: identifier(),
      type: "association",
      difficulte: difficulty,
      enonce: template.enonce,
      propositions: { elements, correspondances },
      bonne_reponse: Object.fromEntries(pairs)
    };
  }

  async function generateIntrus(difficulty) {
    const template = await loadTemplate("intrus");
    const model = template.modeles[Math.floor(Math.random() * template.modeles.length)];
    const count = template.difficultes[String(difficulty)].nombre_elements;
    const choices = shuffle([...model.elements.slice(0, count), model.intrus]);

    return {
      identifiant: identifier(),
      type: "intrus",
      difficulte: difficulty,
      enonce: template.enonce,
      propositions: choices,
      bonne_reponse: model.intrus
    };
  }

  async function generateMemory(difficulty) {
    const template = await loadTemplate("memory");
    const model = template.modeles[Math.floor(Math.random() * template.modeles.length)];
    const count = template.difficultes[String(difficulty)].nombre_paires;
    const pairs = shuffle([...model.paires]).slice(0, count);
    const elements = shuffle(pairs.map(([left]) => left));
    const correspondances = shuffle(pairs.map(([, right]) => right));

    return {
      identifiant: identifier(),
      type: "memory",
      difficulte: difficulty,
      enonce: template.enonce,
      propositions: { elements, correspondances },
      bonne_reponse: Object.fromEntries(pairs)
    };
  }

  async function generate(type, difficulty = null) {
    const level = difficulty === null
      ? 1 + Math.floor(Math.random() * 3)
      : ([1, 2, 3].includes(difficulty) ? difficulty : 1);
    if (type === "association") return generateAssociation(level);
    if (type === "intrus") return generateIntrus(level);
    if (type === "memory") return generateMemory(level);
    throw new Error(`Type d'exercice non disponible : ${type}`);
  }

  window.ExerciseGenerator = { generate };
})();
