/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,js}", "./templates/components/**/*.{html,js}"],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
      },
      colors: {
        // "chat-gray": "#262527"
        // "base-100": "#e2ddd9"
      },
    },
  },
  daisyui: {
    themes: [
      {
        animation: {
          'none': 'none',
        },
      },
      "light",
      "dark",
      "autumn",
      "corporate"
    ],
  },
  plugins: [
    require("@tailwindcss/typography"),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
    require('@tailwindcss/container-queries'),
    require('daisyui'),
    require('tailwindcss-font-inter'),
  ],
}
