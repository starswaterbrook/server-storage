function convertBytes(n){
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  let l = 0
  while(n >= 1024 && ++l){
      n = n/1024;
  }
  return(n.toFixed(n < 10 && l > 0 ? 1 : 0) + ' ' + units[l]);
}

document.addEventListener("DOMContentLoaded", (e) => {
  const socket = io();

  const form = document.querySelector('#file-form');
  const progressBar = document.querySelector('#bar');
  const progressItem = document.querySelector('#progress');
  const textProgress = document.querySelector('#text-progress');
  const fileInput = document.querySelector('#file-field');


  socket.on("upload-progress", (data) => {
    progressBar.style.width = `${(data["uploaded"] / data["total"]) * 100}%`;
    textProgress.innerHTML = `${convertBytes(data["uploaded"])} / ${convertBytes(data["total"])}`;
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