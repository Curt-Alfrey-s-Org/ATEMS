// Create an array of menu items
const menuItems = [
    { label: 'Home', url: '/' },
    { label: 'Admin', url: '/admin' },
    { label: 'Users', url: '/user' },
    { label: 'Tools', url: '/tools' },
    { label: 'Check-in/out', url: '/check-in-out' },
    { label: 'Contact', url: '/contact' },
    { label: 'Docs', url: '/docs' },
]    
// Function to generate the menu HTML
function generateMenu() {
    const menuContainer = document.getElementById('nav-menu');

    // Create a list element for each menu item
    const menuList = document.createElement('ul');
    menuList.classList.add('horizontal-menu'); 
    menuItems.forEach(item => {
        const listItem = document.createElement('li');
        const link = document.createElement('a');
        link.href = item.url;
        link.textContent = item.label;
        listItem.appendChild(link);
        menuList.appendChild(listItem);
    });

    // Create a login/logout button
    const loginButton = document.createElement('li');
    const loginLink = document.createElement('a');
    if (isLoggedIn()) {
        loginLink.href = '/logout';
        loginLink.textContent = 'Logout';
    } else {
        loginLink.href = '/login';
        loginLink.textContent = 'Login';
    }
    loginButton.appendChild(loginLink);
    menuList.appendChild(loginButton);

    // Append the menu to the container
    menuContainer.appendChild(menuList);
}

// Function to check if user is logged in
function isLoggedIn() {
    // Add your logic here to check if the user is logged in
    // Return true if logged in, false otherwise
}

// Call the generateMenu function to create the menu
generateMenu();
