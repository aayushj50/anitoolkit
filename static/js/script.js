function toggleTheme() {
  const body = document.body;
  const isDark = body.classList.toggle("light-theme");
  localStorage.setItem("theme", isDark ? "light" : "dark");
}

window.onload = () => {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light") {
    document.body.classList.add("light-theme");
  }
};
