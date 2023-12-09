function DeleteRaw(dir, file) {
  fetch("/delete/raw", {"method": "POST", data: {dir: dir, file: file})
    .then(kj
}
