// Apply the saved preference before paint. Storage may be blocked in private browsers.
try {
  const preference = localStorage.getItem("weekly-theme");
  document.documentElement.dataset.theme =
    preference === "dark" || preference === "light" ? preference : "light";
} catch {
  document.documentElement.dataset.theme = "light";
}
