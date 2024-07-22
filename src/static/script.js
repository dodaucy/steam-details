function display_money(money) {
    return `${money.toFixed(2)}€`;
}


async function getRequest(url) {
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    })
    if (response.status !== 200) {
        try {
            errorMessage = (await response.json()).detail;
        } catch (error) {
            errorMessage = response.statusText;
        }
        throw new Error(errorMessage);
    }
    return response.json();
}


async function search(mode, searchValue, progress) {
    if (mode === "single-game") {
        if (searchValue.startsWith("https://store.steampowered.com/app/")) {
            appid_or_name = searchValue.split("https://store.steampowered.com/app/")[1].split("/")[0];
        } else {
            appid_or_name = searchValue;
        }
        addGame(await getRequest("/details?appid_or_name=" + encodeURIComponent(appid_or_name)), true);
    } else if (mode === "wishlist") {
        // Clear results
        document.getElementById("result").innerHTML = "";
        // Get wishlist
        const wishlist = await await getRequest("/wishlist?profile_id=" + encodeURIComponent(searchValue));
        // Set progress bar to use percentage
        progress.value = 0;
        progress.max = 100;
        // Add games
        for (i = 0; i < wishlist.length; i++) {
            progress.value = (i / wishlist.length) * 100;
            const appid = wishlist[i];
            addGame(await getRequest("/details?appid_or_name=" + encodeURIComponent(appid)), false);
        }
    }
}


document.addEventListener("DOMContentLoaded", function() {
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
            search_input.placeholder = "Name / ID / URL";
        }
        // Reset search bar
        search_input.value = "";
    });
    document.getElementById("mode-select").dispatchEvent(new Event("change"));
});
