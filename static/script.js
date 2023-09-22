document.addEventListener("DOMContentLoaded", (e) => {
  const socket = io();

  const form = document.querySelector('#file-form');
  const progressBar = document.querySelector('#bar');
  const progressItem = document.querySelector('#progress');
  const textProgress = document.querySelector('#text-progress');
  const fileInput = document.querySelector('#file-field');

  socket.on("upload-progress", (data) => {
    progressBar.style.width = `${(data["uploaded"] / data["total"]) * 100}%`;
    textProgress.innerHTML = `${data["uploaded"]} / ${data["total"]}`;
  });

  socket.on("upload-done", () => {
    window.location.href = ""
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (fileInput.files.length === 0)
    {
      return;
    }

    progressItem.style.display = "flex";
    textProgress.style.display = "flex";
    const formData = new FormData(form);
    const xhr = new XMLHttpRequest();

    xhr.open('POST', '/', true);
    xhr.send(formData);

  });

});