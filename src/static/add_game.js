function addGame(game, appendToTop) {
    console.log(game);

    // Create the result-item div
    const resultItem = document.createElement("div");
    resultItem.className = "result-item";

    // Create the anchor element with images
    const anchorWithImages = document.createElement("a");
    anchorWithImages.href = game.steam.external_url;
    anchorWithImages.target = "_blank";
    anchorWithImages.className = "images";

    Array.from(game.steam.images).forEach((image_url) => {
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
    titleAnchor.href = game.steam.external_url;
    titleAnchor.target = "_blank";
    titleAnchor.className = "title";
    titleAnchor.textContent = game.steam.name
    contentDiv.appendChild(titleAnchor);

    // Create the details div
    const detailsDiv = document.createElement("div");
    detailsDiv.className = "details";

    // Create the details-grid div
    const detailsGridDiv = document.createElement("div");
    detailsGridDiv.className = "small-font details-grid";

    let detailsData = [];

    // Get release difference
    let releaseDifferenceInDays = null;
    let releaseDifferenceInYears = null;
    if (game.steam.released) {
        const date = new Date(game.steam.release_date.iso_date);
        const now = new Date();
        const dateDiff = now - date;
        releaseDifferenceInDays = Math.floor(dateDiff / (1000 * 60 * 60 * 24));
        releaseDifferenceInYears = Math.floor(releaseDifferenceInDays / 365 * 10) / 10;
    }

    // Price difference
    detailsData.push({
        label: "PRICE DIFFERENCE:",
        value: display_money(0.0),
        title: "Difference between lowest current price and lowest historical low"
    })

    // Release date
    let title = "Release date of the game";
    if (game.steam.released) {
        if (releaseDifferenceInYears >= 1) {
            title = `Released ${releaseDifferenceInYears} year${releaseDifferenceInYears !== 1 ? "s" : ""} ago`;
        } else if (releaseDifferenceInDays >= 0) {
            title = `Released ${releaseDifferenceInDays} day${releaseDifferenceInDays !== 1 ? "s" : ""} ago`;
        }
    }
    detailsData.push({
        label: "RELEASE DATE:",
        value: game.steam.release_date.display_string,
        title: title
    });

    // Game length
    if (game.game_length === null){
        detailsData.push({
            label: "GAME LENGTH:",
            value: null
        });
    } else {
        let title_list = [];
        if (game.game_length.main !== null) {
            title_list.push(`Main Story: ${display_time(game.game_length.main)}`);
        }
        if (game.game_length.plus !== null) {
            title_list.push(`Main + Extras: ${display_time(game.game_length.plus)}`);
        }
        if (game.game_length.completionist !== null) {
            title_list.push(`Completionist: ${display_time(game.game_length.completionist)}`);
        }
        if (title_list.length > 0) {
            if (game.game_length.plus === null) {
                detailsData.push({
                    label: "GAME LENGTH:",
                    value: "Hover for info",
                    title: `${title_list.join("\n")}\nFrom: howlongtobeat.com`
                });
            } else {
                const hours = game.game_length.plus / 3600;
                if (hours >= 10) {
                    class_name = "green";
                } else if (hours >= 5) {
                    class_name = "yellow";
                } else if (hours >= 1) {
                    class_name = "orange";
                } else {
                    class_name = "red";
                }
                detailsData.push({
                    label: "GAME LENGTH:",
                    value: display_time_as_float(game.game_length.plus),
                    title: `${title_list.join("\n")}\nFrom: howlongtobeat.com`,
                    color_class: class_name
                });
            }
        } else {
            detailsData.push({
                label: "GAME LENGTH:",
                value: null
            });
        }
    }

    // Achievements
    if (game.steam.released) {
        if (game.steam.achievement_count >= 20) {
            color_class = "green";
        } else if (game.steam.achievement_count >= 10) {
            color_class = "yellow";
        } else if (game.steam.achievement_count > 1) {
            color_class = "orange";
        } else {
            color_class = "red";
        }
        detailsData.push({
            label: "ACHIEVEMENTS:",
            value: game.steam.achievement_count,
            title: "Number of achievements in the game",
            color_class: color_class
        });
    } else {
        detailsData.push({
            label: "ACHIEVEMENTS:",
            value: null
        });
    }

    // Linux support
    if (game.steam.native_linux_support) {
        detailsData.push({
            label: "LINUX SUPPORT:",
            value: "NATIVE",
            title: "The game is natively supported on Linux",
            color_class: "green"
        });
    } else {
        if (game.linux_support == null || game.linux_support.tier == "PENDING") {
            detailsData.push({
                label: "LINUX SUPPORT:",
                value: null
            });
        } else {
            let color_class = "grey";
            if (["moderate", "good", "strong"].includes(game.linux_support.confidence)) {
                if (game.linux_support.tier == "PLATINUM" || game.linux_support.tier == "GOLD") {
                    color_class = "green";
                } else if (game.linux_support.tier == "SILVER") {
                    color_class = "yellow";
                } else if (game.linux_support.tier == "BRONZE") {
                    color_class = "orange";
                } else if (game.linux_support.tier == "BORKED") {
                    color_class = "red";
                }
            }
            detailsData.push({
                label: "LINUX SUPPORT:",
                value: game.linux_support.tier,
                title: `Confidence: ${game.linux_support.confidence}\nReports: ${game.linux_support.report_count}\nFrom: protondb.com`,
                color_class: color_class
            });
        }
    }

    // Add details
    detailsData.forEach(detail => {
        const labelDiv = document.createElement("div");
        labelDiv.textContent = detail.label;
        detailsGridDiv.appendChild(labelDiv);

        const valueDiv = document.createElement("div");
        if (detail.value === null) {
            valueDiv.textContent = "N/A";
            valueDiv.classList.add("grey");
            labelDiv.title = "Not available";
            valueDiv.title = "Not available";
        } else {
            valueDiv.textContent = detail.value;
            if (detail.color_class !== undefined) {
                valueDiv.classList.add(detail.color_class);
            }
            labelDiv.title = detail.title;
            valueDiv.title = detail.title;
        }
        detailsGridDiv.appendChild(valueDiv);
    });

    detailsDiv.appendChild(detailsGridDiv);

    // Create the purchase-area-container div
    const purchaseAreaContainerDiv = document.createElement("div");
    purchaseAreaContainerDiv.className = "purchase-area-container";

    if (game.steam.released) {

        if (game.steam.price === null) {

            const purchaseAreaDiv = document.createElement("div");
            purchaseAreaDiv.className = "purchase-area";

            const priceDiv = document.createElement("div");
            priceDiv.className = "price";
            priceDiv.textContent = "Not available";

            purchaseAreaDiv.appendChild(priceDiv);

            purchaseAreaContainerDiv.appendChild(purchaseAreaDiv);

        } else {

            const purchaseData = [
                {
                    historicalLowTitle: "From steamdb.info",
                    historicalLowPrice: 0.0,
                    priceTitle: null,
                    price: game.steam.price,
                    buttonText: "Buy on Steam",
                    buttonURL: game.steam.external_url,
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

        }

    } else {
        const purchaseAreaDiv = document.createElement("div");
        purchaseAreaDiv.className = "purchase-area";

        const priceDiv = document.createElement("div");
        priceDiv.className = "price";
        priceDiv.textContent = "Coming soon";

        purchaseAreaDiv.appendChild(priceDiv);

        purchaseAreaContainerDiv.appendChild(purchaseAreaDiv);
    }

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
