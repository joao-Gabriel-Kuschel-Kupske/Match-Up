// Este bloco DEVE ser adicionado ao seu arquivo JavaScript
var modal = document.getElementById("modalContato");
var btn = document.getElementById("abrirModal");
var span = document.querySelector(".fechar");

// Abre a modal
btn.onclick = function() {
  modal.style.display = "block";
}

// Fecha pelo 'X'
span.onclick = function() {
  modal.style.display = "none";
}

// Fecha ao clicar fora da modal
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}