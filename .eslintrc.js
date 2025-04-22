module.exports = {
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:import/errors",
    "plugin:import/warnings",
    "prettier",
  ],
  plugins: ["react", "import"],
  env: { browser: true, es2021: true },
  settings: { react: { version: "detect" } },
}
