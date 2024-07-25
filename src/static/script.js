function display_price(price_float) {
    return `${price_float.toFixed(2)}€`;
}


function display_time_as_float(seconds) {
    return `${(seconds / 3600).toFixed(1).replace(".", ",")}h`
}


function display_time(seconds) {
    hours = Math.floor(seconds / 3600)
    minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
}


function display_date(optional_iso_date) {
    if (optional_iso_date) {
        var date = new Date(optional_iso_date);
    } else {
        var date = new Date();
    }
    let month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][date.getMonth()];
    return `${date.getDate()} ${month}, ${date.getFullYear()}`
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
        if (searchValue.startsWith("https://steamcommunity.com/id/")) {
            profile_name_or_id = searchValue.split("https://steamcommunity.com/id/")[1].split("/")[0];
        } else {
            profile_name_or_id = searchValue;
        }
        // Clear results
        document.getElementById("result").innerHTML = "";
        // Get wishlist
        const wishlist = await await getRequest("/wishlist?profile_name_or_id=" + encodeURIComponent(profile_name_or_id));
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
        const searchInput = document.getElementById("search-input");
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
        let success = false;
        try {
            await search(mode, searchInput.value.trim(), progress);
            success = true;
        } catch (error) {
            console.error(error);
            // Show error message
            errorMessage.style.display = "block";
            errorMessage.innerText = error.message;
        }

        // Hide search progress
        document.getElementById("progress-container").style.display = "none";

        // Clear search bar
        if (success) {
            searchInput.value = "";
        }

        // Enable search bar
        Array.from(document.getElementById("search-bar").children).forEach(function(element) {
            element.disabled = false;
        })

        // Focus search input
        searchInput.focus();
    });

    // Search with Enter
    document.getElementById("search-input").addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            document.getElementById("search-button").click();
        }
    });

    // On mode change
    document.getElementById("mode-select").addEventListener("change", function() {
        searchInput = document.getElementById("search-input");
        // Change placeholder
        if (this.value === "single-game") {
            searchInput.placeholder = "Game: Name / ID / URL";
        } else {
            searchInput.placeholder = "Profile: Name / ID / URL";
        }
        // Reset search bar
        searchInput.value = "";
    });
    document.getElementById("mode-select").dispatchEvent(new Event("change"));
});
