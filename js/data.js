/* ============================================================
   DS LAB — Dynamic build (Flask + SQLite backend, browser fallback).
   Everything (experiments, sub-experiments, modules, tools,
   profile, home text, about text) is created/edited in the UI.
   Relationship: Experiment -> subs[] (1-to-many), mirrored in
   SQLite tables `experiments` / `subs`.
   This file only holds: CSV starter templates + factory defaults.
   ============================================================ */

const CSV_TEMPLATES = {
  blank: { name: "data.csv", text: `col1,col2,col3\n1,2,3\n4,5,6` },
  students: { name: "students.csv", text: `name,maths,physics,attendance\nAarav,82,78,92\nDiya,91,88,96\nKabir,67,,75\nAnanya,74,71,88\nVivaan,88,84,90\nIshita,59,62,70\nArjun,95,91,98\nMeera,73,69,85` },
  houses: { name: "houses.csv", text: `area_bhk,area_sqft,price_lakh\n2,950,48\n2,1100,55\n3,1400,72\n3,1600,85\n4,2100,120\n2,1000,52\n3,1500,78\n4,1900,105` },
  sales: { name: "sales.csv", text: `month,sales,ad_spend\nJan,120,10\nFeb,135,12\nMar,150,14\nApr,145,13\nMay,170,18\nJun,190,22` },
};

const DEFAULT_TOOLS = [
  { id: "t1", icon: "🐍", name: "Python", desc: "Core language" },
  { id: "t2", icon: "🐼", name: "Pandas", desc: "DataFrames & EDA" },
  { id: "t3", icon: "🔢", name: "NumPy", desc: "Arrays & maths" },
  { id: "t4", icon: "📊", name: "Matplotlib", desc: "Charts & plots" },
  { id: "t5", icon: "🌊", name: "Seaborn", desc: "Statistical viz" },
  { id: "t6", icon: "🌲", name: "Scikit-learn", desc: "ML models" },
  { id: "t7", icon: "📓", name: "Jupyter", desc: "Lab notebooks" },
  { id: "t8", icon: "🐙", name: "GitHub", desc: "Code record" },
];

/* Personal details are NOT hardcoded: enter them in the profile editor. */
const DEFAULT_PROFILE = {
  name: "", roll: "", cls: "",
  uni: "", photo: "",
  faculty: "", designation: "",
  linkedin: "", github: "", youtube: "", email: "", site: ""
};

const DEFAULT_HOME = {
  title: "Data Science",
  subtitle: "Your Digital Library for Learning, Experiments and Projects"
};

/* Default website logo (used until you upload your own) */
const DEFAULT_LOGO = "data:image/svg+xml," + encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1d9bf0"/><stop offset="1" stop-color="#6d5dfc"/></linearGradient></defs>
    <rect width="64" height="64" rx="16" fill="url(#g)"/>
    <path d="M26 12h12v4h-2v11.5l10.2 17.4A6 6 0 0 1 41 54H23a6 6 0 0 1-5.2-9.1L28 27.5V16h-2z" fill="none" stroke="#fff" stroke-width="3.2" stroke-linejoin="round"/>
    <path d="M23.5 42h17l3.2 5.4A2.6 2.6 0 0 1 41.5 51h-19a2.6 2.6 0 0 1-2.2-3.6z" fill="#fff" opacity=".9"/>
    <circle cx="33" cy="36" r="2" fill="#fff"/><circle cx="38" cy="32" r="1.4" fill="#fff"/>
  </svg>`);

function blankExperiment() {
  return {
    id: "e" + Date.now().toString(36) + Math.floor(Math.random() * 999),
    title: "", tagline: "", image: "",
    github: "", videoUrl: "", youtube: [],
    needsFile: false, sampleName: "data.csv", sampleText: "",
    code: "# Write your experiment code here\nprint('Hello DS Lab')",
    expectedOutput: "",
    subs: []
  };
}

function blankSub() {
  return {
    id: "s" + Date.now().toString(36) + Math.floor(Math.random() * 999),
    title: "", desc: "", image: "",
    github: "", videoUrl: "", youtube: [],
    needsFile: false, sampleName: "data.csv", sampleText: "",
    code: "# Sub-experiment code\nprint('Sub-experiment output')",
    expectedOutput: ""
  };
}

function defaultState() {
  return {
    version: 2,
    profile: Object.assign({}, DEFAULT_PROFILE),
    home: Object.assign({}, DEFAULT_HOME),
    tools: JSON.parse(JSON.stringify(DEFAULT_TOOLS)),
    experiments: [],
    modules: [],
    resources: [],
    projects: [],
    logo: "",
    outputs: {},
    videos: {}
  };
}
