// URL de l'exercice suivant (ex. "../memory/index.html").
// Mettre null pour rejouer l'exercice avec un nouveau mélange.
const SUIVANT = null;

// Une question = 4 éléments qui vont ensemble ("memes") + 1 intrus ("intrus").
// Soit 5 propositions affichées, dans un ordre mélangé.
//
// Chaque élément peut être :
//   - un texte                              : "chat"
//   - un emoji                              : "🐱"
//   - un chemin d'image (png, jpg, gif, svg, webp) : "img/chat.png"
//   - un objet { image, alt } pour décrire l'image aux lecteurs d'écran :
//       { image: "img/chat.png", alt: "un chat" }
// Texte et images peuvent être mélangés dans une même question.

const DATA = [
  /*
  { memes: ["chat", "chien", "lapin", "cheval"], intrus: "voiture" },
  { memes: ["pomme", "poire", "banane", "fraise"], intrus: "carotte" },
  { memes: ["rouge", "bleu", "vert", "jaune"], intrus: "table" },
  { memes: ["marteau", "tournevis", "pince", "scie"], intrus: "oreiller" },
  { memes: ["Paris", "Lyon", "Marseille", "Toulouse"], intrus: "Madrid" },
  { memes: ["violon", "guitare", "piano", "flûte"], intrus: "crayon" },
  { memes: ["été", "hiver", "printemps", "automne"], intrus: "lundi" },
  { memes: ["avion", "train", "bateau", "bus"], intrus: "fromage" },
  */

  // Exemple avec des images : 4 cercles et 1 triangle (fichiers dans img/)
  {
    memes: [
      { image: "/exercices/intrus/img/filled_circle.png", alt: "cercle noir" },
      { image: "/exercices/intrus/img/filled_circle.png", alt: "cercle noir" },
      { image: "/exercices/intrus/img/filled_circle.png", alt: "cercle noir" },
      { image: "/exercices/intrus/img/filled_circle.png", alt: "cercle noir" }
    ],
    intrus: { image: "/exercices/intrus/img/filled_triangle.png", alt: "triangle noir" }
  },
  {
    memes: [ //4 triangles et un carre
      { image: "/exercices/intrus/img/filled_triangle.png", alt: "triangle noir" },
      { image: "/exercices/intrus/img/filled_triangle.png", alt: "triangle noir" },
      { image: "/exercices/intrus/img/filled_triangle.png", alt: "triangle noir" },
      { image: "/exercices/intrus/img/filled_triangle.png", alt: "triangle noir" }
    ],
    intrus: { image: "/exercices/intrus/img/filled_square.png", alt: "carre noir" }
  },
  {
    memes: [ //4 carrés et un cercle
      { image: "/exercices/intrus/img/filled_square.png", alt: "carre noir" },
      { image: "/exercices/intrus/img/filled_square.png", alt: "carre noir" },
      { image: "/exercices/intrus/img/filled_square.png", alt: "carre noir" },
      { image: "/exercices/intrus/img/filled_square.png", alt: "carre noir" }
    ],
    intrus: { image: "/exercices/intrus/img/filled_circle.png", alt: "cercle noir" }
  },
    {
    memes: [ //4 cercles vide et un triangle vide
      { image: "/exercices/intrus/img/empty_circle.png", alt: "cercle vide" },
      { image: "/exercices/intrus/img/empty_circle.png", alt: "cercle vide" },
      { image: "/exercices/intrus/img/empty_circle.png", alt: "cercle vide" },
      { image: "/exercices/intrus/img/empty_circle.png", alt: "cercle vide" }
    ],
    intrus: { image: "/exercices/intrus/img/empty_triangle.png", alt: "triangle vide" }
  },
  {
    memes: [ //4 triangles vide et un carre vide
      { image: "/exercices/intrus/img/empty_triangle.png", alt: "triangle vide" },
      { image: "/exercices/intrus/img/empty_triangle.png", alt: "triangle vide" },
      { image: "/exercices/intrus/img/empty_triangle.png", alt: "triangle vide" },
      { image: "/exercices/intrus/img/empty_triangle.png", alt: "triangle vide" }
    ],
    intrus: { image: "/exercices/intrus/img/empty_square.png", alt: "carre vide" }
  },
];
