document.addEventListener('DOMContentLoaded', function() {
  var header = document.querySelector('.md-header-nav');
  if (header) {
      var button = document.createElement('a');
      button.textContent = 'Sign Out';
      button.className = 'md-header-nav__button md-icon signout-button';
      button.href = '/signout';
      header.appendChild(button);
  }
});
