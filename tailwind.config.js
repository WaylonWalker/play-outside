/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["templates/**/*.html"],
  plugins: [require("@tailwindcss/typography")],
  theme: {
    extend: {
      width: {
        128: "32rem",
      },
      boxShadow: {
        xlc: "0 0 60px 15px rgba(0, 0, 0, 0.3)",
        lgc: "0 0 20px 0px rgba(0, 0, 0, 0.3)",
      },

    },
  },
};
