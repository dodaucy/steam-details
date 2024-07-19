function add_game(game_data) {
    console.log(game_data);
}


async function get_request(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    })
    if (response.status !== 200) {
        try {
            error_message = (await response.json()).detail;
        } catch (error) {
            error_message = response.statusText;
        }
        throw new Error(error_message);
    }
    return response.json();
}


async function search(mode, searchValue, progress) {
    if (mode === "single-game") {
        if (searchValue.startsWith("https://store.steampowered.com/app/")) {
            appid = searchValue.split("https://store.steampowered.com/app/")[1].split("/")[0];
        } else {
            appid = searchValue;
        }
        const game_data = await get_request("/details?appid=" + encodeURIComponent(appid));
        add_game({
            "wishlist_data": {
                "appid": appid,
                "images": [game_data.steam.fallback.image],
                "review_score": null,
                "review_count": null
            },
            "game_data": game_data.steam.data
        })
    } else if (mode === "wishlist") {
        progress.value = 0;
        progress.max = 100;
        const wishlist = await await get_request("/wishlist?profile_id=" + encodeURIComponent(searchValue));
        for (i = 0; i < wishlist.length; i++) {
            progress.value = (i / wishlist.length) * 100;
            const game = wishlist[i];
            add_game({
                "wishlist_data": game,
                "game_data": (await get_request("/details?appid=" + encodeURIComponent(game.appid))).steam.data
            })
        }
    }
}


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
        const searchValue = document.getElementById("search-input").value;
        const errorMessage = document.getElementById("error-message");
        const progress = document.getElementById("progress");

        // Disable search bar
        Array.from(document.getElementById("search-bar").children).forEach(function(element) {
            element.disabled = true;
        })

        // Hide error message
        errorMessage.style.display = "none";

        // Show search progress
        progress.removeAttribute("value");
        progress.removeAttribute("max");
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
    document.getElementById("search-input").addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            document.getElementById("search-button").click();
        }
    });

    // On mode change
    document.getElementById("mode-select").addEventListener("change", function() {
        search_input = document.getElementById("search-input");
        // Change placeholder
        if (this.value === "wishlist") {
            search_input.placeholder = "Steam ID / Profile";
        } else {
            search_input.placeholder = "Enter Game ID / URL";
        }
        // Reset search bar
        search_input.value = "";
    });
    document.getElementById("mode-select").dispatchEvent(new Event("change"));
});
