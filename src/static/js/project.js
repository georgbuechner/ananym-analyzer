function AddToProject(select, path) {
  const project = select.options[select.selectedIndex].value;
  console.log("Adding to project: ", path, project);
  fetch("/api/projects/add_analysis?project=" + project + "&path=" + path, { method: "POST"})
    .then(response => {
        response.text().then(text => alert(text));
    })
    .catch(error => alert(error));
}

function RemoveFromProject(project, path) {
  console.log("Adding to project: ", path, project);
  fetch("/api/projects/remove_analysis?project=" + project + "&path=" + path, { method: "POST"})
    .then(response => {
      if (response.ok) {
        window.location.reload();
      } else {
        response.text().then(text => alert(text));
      }
    })
    .catch(error => alert(error));
}
