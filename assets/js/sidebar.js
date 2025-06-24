document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const siteContent = document.getElementById('siteContent');
  
  // Mobile sidebar toggle
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      sidebar.classList.toggle('show');
      siteContent.classList.toggle('sidebar-open');
    });
  }
  
  // Add arrows to items with dropdowns and handle toggles
  const dropdownItems = document.querySelectorAll('.sidebar-nav li > .nav-item');
  
  dropdownItems.forEach(item => {
    const dropdown = item.parentNode.querySelector('.dropdown');
    if (dropdown) {
      // Add arrow indicator
      const arrow = document.createElement('span');
      arrow.className = 'dropdown-arrow';
      arrow.innerHTML = '▼';
      item.appendChild(arrow);
      
      item.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Toggle current dropdown only
        this.classList.toggle('active');
        dropdown.classList.toggle('show');
        arrow.classList.toggle('rotated');
      });
    }
  });
  
  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', function(e) {
    if (window.innerWidth <= 992 && 
        !e.target.closest('.sidebar') && 
        !e.target.closest('.sidebar-toggle')) {
      sidebar.classList.remove('show');
      siteContent.classList.remove('sidebar-open');
    }
  });
  
  // Handle window resize
  window.addEventListener('resize', function() {
    if (window.innerWidth > 992) {
      sidebar.classList.remove('show');
      siteContent.classList.remove('sidebar-open');
    }
  });
  
  // Highlight current page
  const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
  const navLinks = Array.from(document.querySelectorAll('.sidebar-nav a.nav-item[href]'));
  
  // Sort by path length (longest first) to prioritize specific matches
  navLinks.sort((a, b) => b.getAttribute('href').length - a.getAttribute('href').length);
  
  let matched = false;
  navLinks.forEach(link => {
    if (matched) return;
    
    const linkPath = link.getAttribute('href').replace(/\/$/, '') || '/';
    if (linkPath === currentPath) {
      link.classList.add('active');
      matched = true;
      
      // Expand parent dropdowns and rotate arrows
      let parent = link.closest('.dropdown');
      while (parent) {
        parent.classList.add('show');
        const parentItem = parent.parentNode.querySelector('.nav-item');
        if (parentItem) {
          parentItem.classList.add('active');
          const arrow = parentItem.querySelector('.dropdown-arrow');
          if (arrow) arrow.classList.add('rotated');
        }
        parent = parent.parentNode.closest('.dropdown');
      }
    }
  });
});
