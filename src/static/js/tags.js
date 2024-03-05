function AddTag() {
  const tag = document.getElementById("inpTag").value;
  var tags = document.getElementById("tags"); 
  if (tags.value.length === 0) 
    tags.value = tag;
  else 
    tags.value += ", " + tag;
}

function InitAddTagModal(path) {
  document.getElementById("tag_modal_path").value = path;
}

function AddTagToPath() {
  let formData = new FormData();
  formData.append("path", document.getElementById("tag_modal_path").value);
  formData.append("tag", document.getElementById("inp_new_tag").value);
  fetch("/tags/update/", {method: "POST", body: formData})
    .then(_ => window.location.reload())
    .catch(error => alert(error));

}

function RemoveTagFromPath(path, tag) {
  let formData = new FormData();
  formData.append("path", path);
  formData.append("tag", tag);
  fetch("/tags/remove/", {method: "POST", body: formData})
    .then(_ => window.location.reload())
    .catch(error => alert(error));

}
