function addRetryButton(text, appid, resultItem) {
    const retryButton = document.createElement("a");
    retryButton.className = "retry-button error-button";
    retryButton.textContent = text;
    retryButton.href = "javascript:void(0)";

    retryButton.onclick = async () => {
        resultItem.removeChild(retryButton);
        try {
            await fetchDetails(resultItem, appid);
        } catch (error) {
            console.error(error);
            addRetryButton(`Retry (${error.message})`, appid, resultItem);
        }
    }

    resultItem.appendChild(retryButton);
}


function addGame(game, resultItem) {
    console.log(game);

    // Clear the result-item
    resultItem.innerHTML = "";

    // Check if steam data is available
    if (!game.services.steam.success) {  // This should never happen
        throw new Error(`Steam error: ${game.services.steam.error}`);
    }

    // Retry Button
    for (const service in game.services) {
        if (!game.services[service].success) {
            addRetryButton("Retry", game.services.steam.data.appid, resultItem);
            break;
        }
    }

    // Create the anchor element with images
    const anchorWithImages = document.createElement("a");
    anchorWithImages.href = game.services.steam.data.external_url;
    anchorWithImages.target = "_blank";
    anchorWithImages.className = "images";

    Array.from(game.services.steam.data.images).forEach((image_url) => {
        const image = document.createElement("img");
        image.className = "image";
        image.src = image_url;
        anchorWithImages.appendChild(image);
    });

    resultItem.appendChild(anchorWithImages);

    // Create the content div
    const contentDiv = document.createElement("div");
    contentDiv.className = "content";

    // Create the title anchor
    const titleAnchor = document.createElement("a");
    titleAnchor.href = game.services.steam.data.external_url;
    titleAnchor.target = "_blank";
    titleAnchor.className = "title";
    titleAnchor.textContent = game.services.steam.data.name
    contentDiv.appendChild(titleAnchor);

    // Create the details div
    const detailsDiv = document.createElement("div");
    detailsDiv.className = "details";

    let[detailsGridDiv, lowest_price, lowest_price_color_class] = createDetailsGrid(game);

    detailsDiv.appendChild(detailsGridDiv);

    detailsDiv.appendChild(createPurchaseAreas(game, lowest_price, lowest_price_color_class));
    contentDiv.appendChild(detailsDiv);
    resultItem.appendChild(contentDiv);

    // Update images
    const images = anchorWithImages.getElementsByClassName("image");
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

    anchorWithImages.addEventListener("mouseover", () => {
        mouseIsOver = true;
        // Start the rotation when the mouse enters the container
        nextImageTimeout = setTimeout(showNextImage, 1000);  // Change image every 1 second
    });

    anchorWithImages.addEventListener("mouseout", () => {
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
}
