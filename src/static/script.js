document.addEventListener("DOMContentLoaded", function() {
    // Images
    Array.from(document.getElementsByClassName("images")).forEach(function(container) {
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

    // Search
    document.getElementById("search-button").addEventListener("click", async function() {
        const mode = document.getElementById("mode-select").value;
        const searchValue = document.getElementById("wishlist-search").value;
        const errorMessage = document.getElementById("error-message");
        const progress = document.getElementById("progress");

        // Disable search bar
        Array.from(document.getElementById("search-bar").children).forEach(function(element) {
            console.log(element);
            element.disabled = true;
        })

        // Hide error message
        errorMessage.style.display = "none";

        // Show search progress
        progress.value = 0;
        document.getElementById("progress-container").style.display = "flex";

        // Search
        try {
            await search(mode, searchValue, progress);
        } catch (error) {
            console.error(error);
            // Show error message
            errorMessage.style.display = "block";
            errorMessage.innerText = error.message;
        }

        // Hide search progress
        document.getElementById("progress-container").style.display = "none";

        // Enable search bar
        Array.from(document.getElementById("search-bar").children).forEach(function(element) {
            element.disabled = false;
        })
    });
    // Search with Enter
    document.getElementById("wishlist-search").addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            document.getElementById("search-button").click();
        }
    });
});
