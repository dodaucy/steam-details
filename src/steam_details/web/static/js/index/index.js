function changeWaitForSeconds() {
    const new_wait_for_seconds = prompt(
        "Enter number of seconds to wait to avoid rate limits and captchas:",
        localStorage.getItem("wait_for_seconds") || "3"
    )
    if (new_wait_for_seconds) {
        localStorage.setItem("wait_for_seconds", new_wait_for_seconds);
    }
}


function createResultItem(appendToTop) {
    // Create the result-item
    const resultItem = document.createElement("div");
    resultItem.className = "result-item";

    // Append the result-item to the #result div
    if (appendToTop) {
        document.getElementById("result").prepend(resultItem);
    } else {
        document.getElementById("result").appendChild(resultItem);
    }

    return resultItem;
}


async function fetchDetails(resultItem, appidOrName) {
    resultItem.innerText = `Getting details for '${appidOrName}'...`;
    addGame(await getRequest("details?use_cache=false&appid_or_name=" + encodeURIComponent(appidOrName)), resultItem);
}


async function search(mode, searchValue, progress) {
    const progressText = document.getElementById("progress-text");

    if (mode === "single-game") {

        // Try to get appid from url
        if (searchValue.startsWith("https://store.steampowered.com/app/")) {
            appidOrName = searchValue.split("https://store.steampowered.com/app/")[1].split("/")[0];
        } else if (searchValue.startsWith("https://store.steampowered.com/agecheck/app/")) {
            appidOrName = searchValue.split("https://store.steampowered.com/agecheck/app/")[1].split("/")[0];
        } else {
            appidOrName = searchValue;
        }

        // Get details
        progressText.innerText = `Getting details for '${appidOrName}'...`;
        addGame(await getRequest("details?appid_or_name=" + encodeURIComponent(appidOrName)), createResultItem(true));

    } else if (mode === "wishlist") {

        // Try to get profile name from url
        if (searchValue.startsWith("https://steamcommunity.com/id/")) {
            profile_name_or_id = searchValue.split("https://steamcommunity.com/id/")[1].split("/")[0];
        } else {
            profile_name_or_id = searchValue;
        }

        // Clear results
        document.getElementById("result").innerHTML = "";

        // Get wishlist
        progressText.innerText = `Getting wishlist for '${profile_name_or_id}'...`;
        const wishlist = await await getRequest("wishlist?profile_name_or_id=" + encodeURIComponent(profile_name_or_id));

        // Set progress bar to use percentage
        progress.value = 0;
        progress.max = 100;

        // Add games
        for (i = 0; i < wishlist.length; i++) {
            const appid = wishlist[i];

            // Get details
            progressText.innerText = `Getting details for '${appid}'...`;
            const details = await getRequest("details?appid_or_name=" + encodeURIComponent(appid));
            addGame(details, createResultItem(false));

            // Update progress
            progress.value = ((i + 1) / wishlist.length) * 100;

            // Wait a bit
            if (i < wishlist.length - 1) {
                if (details.from_cache) {

                    progressText.innerText = `Waiting only 0.5 seconds due to cache...`;
                    await new Promise(resolve => setTimeout(resolve, 500));

                } else {

                    let wait_for_seconds = parseInt(localStorage.getItem("wait_for_seconds"));
                    if (isNaN(wait_for_seconds)) {
                        wait_for_seconds = 3;
                        localStorage.setItem("wait_for_seconds", wait_for_seconds);
                    } else if (wait_for_seconds < 1) {
                        wait_for_seconds = 1;
                    }

                    progressText.innerHTML = `Waiting for <span id="wait_for_seconds" onclick="changeWaitForSeconds();">${wait_for_seconds}</span> seconds...`;
                    await new Promise(resolve => setTimeout(resolve, wait_for_seconds * 1000));

                }
            }
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
        document.getElementById("progress-text").innerText = "Loading...";
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
