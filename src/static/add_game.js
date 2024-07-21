function addGame(data, appendToTop) {
    console.log(data);

    // Create the result-item div
    const resultItem = document.createElement("div");
    resultItem.className = "result-item";

    // Create the anchor element with images
    const anchorWithImages = document.createElement("a");
    anchorWithImages.href = data.game.external_url;
    anchorWithImages.target = "_blank";
    anchorWithImages.className = "images";

    Array.from(data.wishlist.images).forEach((image_url) => {
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
    titleAnchor.href = data.game.external_url;
    titleAnchor.target = "_blank";
    titleAnchor.className = "title";
    titleAnchor.textContent = data.game.name
    contentDiv.appendChild(titleAnchor);

    // Create the description
    const descriptionDiv = document.createElement("div");
    descriptionDiv.className = "small-font";
    descriptionDiv.textContent = data.game.description
    contentDiv.appendChild(descriptionDiv);

    // Create the details div
    const detailsDiv = document.createElement("div");
    detailsDiv.className = "details";

    // Create the details-grid div
    const detailsGridDiv = document.createElement("div");
    detailsGridDiv.className = "small-font details-grid";

    const detailsData = [
        { title: "Difference between lowest current price and lowest historical low", label: "PRICE DIFFERENCE:", value: display_money(0.0) },
        { title: "Main Story: 30,5 hours\nMain + Extras: 40,7 hours\nCompletionist: 80,0 hours\nAll Styles: 40,7 hours", label: "GAME LENGTH:", value: "40,7 hours" },
        { title: "Release date of the game", label: "RELEASE DATE:", value: "18 JUL, 2024" },
        { title: "69% of the 100,000 user reviews are positive", label: "OVERALL REVIEWS:", value: "VERY POSITIVE" },
        { title: "From protondb.com", label: "LINUX SUPPORT:", value: "PLATINUM" }
    ];

    detailsData.forEach(detail => {
        const labelDiv = document.createElement("div");
        labelDiv.title = detail.title;
        labelDiv.textContent = detail.label;
        detailsGridDiv.appendChild(labelDiv);

        const valueDiv = document.createElement("div");
        valueDiv.title = detail.title;
        valueDiv.textContent = detail.value;
        detailsGridDiv.appendChild(valueDiv);
    });

    detailsDiv.appendChild(detailsGridDiv);

    // Create the purchase-area-container div
    const purchaseAreaContainerDiv = document.createElement("div");
    purchaseAreaContainerDiv.className = "purchase-area-container";

    const purchaseData = [
        {
            historicalLowTitle: "From steamdb.info",
            historicalLowPrice: 0.0,
            priceTitle: null,
            price: data.game.price,
            buttonText: "Buy on Steam",
            buttonURL: data.game.external_url,
            buttonClass: "steam-button"
        },
        {
            historicalLowTitle: "Shop: Kinguin",
            historicalLowPrice: 0.0,
            priceTitle: "Form: GIFT EU\nShop: Kinguin\nEdition: Early Access",
            price: 0.0,
            buttonText: "Buy Key or Gift",
            buttonURL: "https://example.com",
            buttonClass: "keyforsteam-button"
        }
    ];

    purchaseData.forEach(purchase => {
        const purchaseAreaDiv = document.createElement("div");
        purchaseAreaDiv.className = "purchase-area";

        const historicalLowDiv = document.createElement("div");
        if (purchase.historicalLowTitle !== null) {
            historicalLowDiv.title = purchase.historicalLowTitle;
        }
        historicalLowDiv.className = "historical-low";

        const historicalLowLabelDiv = document.createElement("div");
        historicalLowLabelDiv.className = "small-font historical-low-label";
        historicalLowLabelDiv.textContent = "Historical low";
        historicalLowDiv.appendChild(historicalLowLabelDiv);

        const historicalLowValueDiv = document.createElement("div");
        historicalLowValueDiv.className = "small-font historical-low-value";
        historicalLowValueDiv.textContent = display_money(purchase.historicalLowPrice);
        historicalLowDiv.appendChild(historicalLowValueDiv);

        purchaseAreaDiv.appendChild(historicalLowDiv);

        const priceDiv = document.createElement("div");
        priceDiv.className = "price";
        if (purchase.priceTitle !== null) {
            priceDiv.title = purchase.priceTitle;
        }
        priceDiv.textContent = display_money(purchase.price);
        purchaseAreaDiv.appendChild(priceDiv);

        const purchaseButton = document.createElement("a");
        purchaseButton.href = purchase.buttonURL;
        purchaseButton.target = "_blank";
        purchaseButton.className = purchase.buttonClass;
        purchaseButton.textContent = purchase.buttonText;
        purchaseAreaDiv.appendChild(purchaseButton);

        purchaseAreaContainerDiv.appendChild(purchaseAreaDiv);
    });

    detailsDiv.appendChild(purchaseAreaContainerDiv);
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



    // Append the result-item to the #result div
    if (appendToTop) {
        document.getElementById("result").prepend(resultItem);
    } else {
        document.getElementById("result").appendChild(resultItem);
    }
}
