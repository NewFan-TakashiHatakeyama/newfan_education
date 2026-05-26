import nextVitals from "eslint-config-next/core-web-vitals";

const config = [
  {
    ignores: ["_template_import/**", ".next/**", "dist/**"]
  },
  ...nextVitals
];

export default config;
