function Search(tags, search_location) {
  console.log("searching for tags: ", tags);
  fetch("/api/search/" + search_location + "/" + tags)
    .then(response => {
      if (response.ok) {
        response.text().then(text => document.getElementsByClassName("accordion")[0].innerHTML = text)
      } else {
        alert(response.status);
      }
    })
    .catch(error => alert(error));
}
