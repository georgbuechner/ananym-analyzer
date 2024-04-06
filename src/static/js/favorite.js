function Favorite(elem) {
  var favorites = localStorage.getItem('favorites');
  console.log(elem);
  if (elem.classList.contains("favorite"))
    elem.classList.remove("favorite");
  else 
    elem.classList.add("favorite");
}
