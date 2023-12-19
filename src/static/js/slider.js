function CheckFromSlider() {
  let fromLabel = document.getElementById('rangeval');
  let fromSlider = document.getElementById('sweep_range');
  fromLabel.innerText = fromSlider.value;
}

function CheckToSlider() {
  let toLabel = document.getElementById('to_rangeval');
  let toSlider = document.getElementById('sweep_range_to');
  toLabel.innerText = toSlider.value;
}
