// Kept in a file rather than inline so the Content-Security-Policy can forbid inline scripts.
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-confirm]");
  if (button && !confirm(button.dataset.confirm)) event.preventDefault();
});

document.addEventListener("change", (event) => {
  if (event.target.matches("[data-autosubmit]")) event.target.form.submit();
});
