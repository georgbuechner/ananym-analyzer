function Favorite(elem, path) {
  var favorites = localStorage.getItem('favorites');
  console.log(elem, encodeURIComponent(path));
  if (elem.classList.contains("favorite")) {
    elem.classList.remove("favorite");
    fetch("/api/favorites/remove/" + encodeURIComponent(path), {method: "POST"})
      .catch(error => alert(error));
  }
  else {
    elem.classList.add("favorite");
    fetch("/api/favorites/add/" + encodeURIComponent(path), {method: "POST"})
      .catch(error => alert(error));
  }
}

function ShowOnlyFavorites() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("only_favorites") === "True")
    urlParams.delete('only_favorites');
  else
    urlParams.set('only_favorites', 'True');
  window.location.search = urlParams;
}
