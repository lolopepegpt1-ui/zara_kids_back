(function () {
  try {
    window.localStorage.setItem('adminTheme', JSON.stringify('light'))
  } catch (error) {
    // Ignore browsers where localStorage is disabled.
  }

  document.documentElement.classList.remove('dark')
  document.documentElement.classList.add('light')
  document.documentElement.style.colorScheme = 'light'
})()
