document.addEventListener("DOMContentLoaded", function () {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Highlight the active link in the navbar based on the scroll position
    window.addEventListener('scroll', function () {
        const sections = document.querySelectorAll('.right-column > h2');
        let currentSectionId = '';

        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            if (rect.top <= 50 && rect.bottom >= 50) {
                currentSectionId = section.id;
            }
        });

        // Remove the 'active' class from all navbar links
        document.querySelectorAll('.navbar a').forEach(link => {
            link.classList.remove('active');
        });

        // Add the 'active' class to the corresponding navbar link
        const activeLink = document.querySelector(`.navbar a[href="#${currentSectionId}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    });
});

window.addEventListener('resize', function() {
    // Code to handle window resize event
});
