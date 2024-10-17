document.addEventListener('DOMContentLoaded', function() {
  var header = document.querySelector('.md-header-nav');
  if (header) {
      var button = document.createElement('a');
      button.textContent = 'Sign Out';
      button.className = 'md-header-nav__button md-icon signout-button';

      // Button Click Event Listener
      button.addEventListener('click', function(event) {
        event.preventDefault();
        try {
          // Handle sign-out logic here
          window.location.href = '/signout';
        } catch (error) {
          console.error('Error during sign-out:', error);
        }
      });
      header.appendChild(button);
  }
});
