// craco.config.js
module.exports = {
  style: {
    postcss: {
      plugin: [
        require('tailwindcss'),
        require('autoprefixer'),
      ],
    },
  },
}  
