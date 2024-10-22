function ToggleScaleBarOptions() {
  if (!document.getElementById('show_scalebar').checked) {
    document.getElementById("scale_bar_opt_ticks").style.display="none";
    document.getElementById("scale_bar_opt_y").style.display="none";
    document.getElementById("for_scale_y_size").style.display="none";
    document.getElementById("scale_bar_opt_x").style.display="none";
    document.getElementById("for_scale_x_size").style.display="none";
  } else {
    document.getElementById("scale_bar_opt_ticks").style.display="block";
    document.getElementById("scale_bar_opt_y").style.display="block";
    document.getElementById("for_scale_y_size").style.display="block";
    document.getElementById("scale_bar_opt_x").style.display="block";
    document.getElementById("for_scale_x_size").style.display="block";
  }
}
