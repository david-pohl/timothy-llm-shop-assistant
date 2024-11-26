/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      keyframes: {
        staggeredPulseA: {
          "0%, 100%": { transform: 'scale(1)', opacity: '0.8' },
          "15%": { transform: 'scale(1.35)', opacity: '1' },
          "25%": { transform: 'scale(1)', opacity: '0.8' }
        },
        staggeredPulseB: {
          "0%, 15%, 100%": { transform: 'scale(1)', opacity: '0.8' },
          "30%": { transform: 'scale(1.35)', opacity: '1' },
          "40%": { transform: 'scale(1)', opacity: '0.8' }
        },
        staggeredPulseC: {
          "0%, 30%, 100%": { transform: 'scale(1)', opacity: '0.8' },
          "45%": { transform: 'scale(1.35)', opacity: '1' },
          "55%": { transform: 'scale(1)', opacity: '0.8' }
        },
      },
      animation: {
        staggeredPulseA: 'staggeredPulseA 1.5s ease-in-out infinite',
        staggeredPulseB: 'staggeredPulseB 1.5s ease-in-out infinite',
        staggeredPulseC: 'staggeredPulseC 1.5s ease-in-out infinite',
      },
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        timoBg: "#2D5986",
        userBg: "#3084DA",
        msgText: "#F0F2F4",
        grayText: "#888888",
        chatBg: "#18191B",
        buttonBg: "#29333D",
        buttonPlaceholder: "#808080",
        buttonText: "#FFFFFF",
        toggleActiveBg: "#8099B2",
      },
    },
  },
  plugins: [],
};

