document.addEventListener("DOMContentLoaded", (event) => {
  const socket = io();

  const form = document.querySelector('#file-form');
  const progressBar = document.querySelector('#bar');
  const progressItem = document.querySelector('#progress');
  const fileInput = document.querySelector('#file-field');

  socket.on('upload-progress', (progress) => {
    progressBar.style.width = `${progress}%`;
  });

  socket.on('upload-done', () => {
    window.location.href = ''
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    progressItem.style.display = "flex";
    const formData = new FormData(form);
    const xhr = new XMLHttpRequest();

    xhr.open('POST', '/', true);
    xhr.send(formData);

  });

});