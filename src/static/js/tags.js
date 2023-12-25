function AddTag() {
  const tag = document.getElementById("inpTag").value;
  var tags = document.getElementById("tags"); 
  if (tags.value.length === 0) 
    tags.value = tag;
  else 
    tags.value += ", " + tag;
}
