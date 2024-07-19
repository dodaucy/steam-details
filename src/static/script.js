document.addEventListener("DOMContentLoaded", function() {
    const containers = document.getElementsByClassName("images");

    Array.from(containers).forEach(function(container) {
        const images = container.getElementsByClassName("image");
        let currentIndex = 0;
        let nextImageTimeout;
        let mouseIsOver = false;

        function showImage(index) {
            images[currentIndex].classList.remove("active");
            currentIndex = index;
            images[currentIndex].classList.add("active");
        }

        function showNextImage() {
            showImage((currentIndex + 1) % images.length);
        }

        // Show the first image initially
        showImage(0);

        container.addEventListener("mouseover", () => {
            mouseIsOver = true;
            // Start the rotation when the mouse enters the container
            nextImageTimeout = setTimeout(showNextImage, 1000);  // Change image every 1 second
        });

        container.addEventListener("mouseout", () => {
            mouseIsOver = false;
            setTimeout(() => {
                if (!mouseIsOver) {
                    // Stop the rotation when the mouse leaves the container
                    clearTimeout(nextImageTimeout)
                    // Reset the image to the first one
                    showImage(0);
                }
            }, 50);
        });
    });
});
