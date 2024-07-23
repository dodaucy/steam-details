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
    let lowest_price_color_class = null;
    let lowest_price = null;
    if (game.steam_historical_low !== null || game.key_and_gift_sellers !== null) {  // ProtonDB OR KeyForSteam data available
        if (game.steam_historical_low !== null && game.key_and_gift_sellers !== null) {  // ProtonDB AND KeyForSteam dara available
            lowest_price = Math.min(game.steam.price, game.key_and_gift_sellers.cheapest_offer.price);
            var lowest_historical_low = Math.min(game.steam_historical_low, game.key_and_gift_sellers.historical_low.price);

        } else if (game.steam_historical_low !== null) {  // ProtonDB data available
            lowest_price = game.steam.price;
            var lowest_historical_low = game.steam_historical_low;

        } else if (game.key_and_gift_sellers !== null) {  // KeyForSteam data available
            lowest_price = game.key_and_gift_sellers.cheapest_offer.price;
            var lowest_historical_low = game.key_and_gift_sellers.historical_low.price;

        }

        const price_difference = lowest_price - lowest_historical_low;

        let title = `How much money you could save if you wait longer\n\nHow this is calculated:\nlowest price (${display_price(lowest_price)}) - lowest historical low (${display_price(lowest_historical_low)})`;
        if (releaseDifferenceInYears >= 1) {
            if (price_difference > 10) {
                var color_class = "red-text";
            } else if (price_difference > 5) {
                var color_class = "orange-text";
            } else if (price_difference > 3) {
                var color_class = "yellow-text";
            } else if (price_difference > 0.5) {
                var color_class = "green-text";
                lowest_price_color_class = "green-purchase-area";
            } else {
                var color_class = "rainbow-text";
                lowest_price_color_class = "rainbow-purchase-area";
            }
        } else {
            var color_class = "grey-text";
            title += "\n\nThe game was released less than a year ago:\nYou might be able to save more money if you wait longer!!";
        }

        detailsData.push({
            label: "PRICE DIFFERENCE:",
            value: display_price(price_difference),
            title: title,
            color_class: color_class
        });
    } else {
        detailsData.push({
            label: "PRICE DIFFERENCE:",
            value: null
        });
    }

    // Release date
    let title = "Release date of the game";
    if (game.steam.released) {
        if (releaseDifferenceInYears >= 1) {
            title = `Released ${releaseDifferenceInYears.toString().replace(".", ",")} year${releaseDifferenceInYears !== 1 ? "s" : ""} ago`;
        } else if (releaseDifferenceInDays >= 0) {
            title = `Released ${releaseDifferenceInDays} day${releaseDifferenceInDays !== 1 ? "s" : ""} ago`;
        }
    }
    detailsData.push({
        label: "RELEASE DATE:",
        value: game.steam.release_date.display_string,
        title: title
    });

    // Reviews
    if (game.steam.released) {
        let color_class = "red-text";
        if (game.steam.overall_reviews.score >= 75) {
            color_class = "green-text";
        } else if (game.steam.overall_reviews.score >= 50) {
            color_class = "yellow-text";
        } else if (game.steam.overall_reviews.score >= 25) {
            color_class = "orange-text";
        }
        detailsData.push({
            label: "OVERALL REVIEWS:",
            value: `${game.steam.overall_reviews.desc} (${game.steam.overall_reviews.score}%)`,
            title: `${game.steam.overall_reviews.score}% of ${game.steam.overall_reviews.total_reviews.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")} reviews are positive`,
            color_class: color_class
        });
    } else {
        detailsData.push({
            label: "OVERALL REVIEWS:",
            value: null
        });
    }

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
                    color_class = "green-text";
                } else if (hours >= 5) {
                    color_class = "yellow-text";
                } else if (hours >= 1) {
                    color_class = "orange-text";
                } else {
                    color_class = "red-text";
                }
                detailsData.push({
                    label: "GAME LENGTH:",
                    value: display_time_as_float(game.game_length.plus),
                    title: `${title_list.join("\n")}\nFrom: howlongtobeat.com`,
                    color_class: color_class
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
            color_class = "green-text";
        } else if (game.steam.achievement_count >= 10) {
            color_class = "yellow-text";
        } else if (game.steam.achievement_count >= 1) {
            color_class = "orange-text";
        } else {
            color_class = "red-text";
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
            color_class: "green-text"
        });
    } else {
        if (game.linux_support == null || game.linux_support.tier == "PENDING") {
            detailsData.push({
                label: "LINUX SUPPORT:",
                value: null
            });
        } else {
            let color_class = "grey-text";
            if (["moderate", "good", "strong"].includes(game.linux_support.confidence)) {
                if (game.linux_support.tier == "PLATINUM" || game.linux_support.tier == "GOLD") {
                    color_class = "green-text";
                } else if (game.linux_support.tier == "SILVER") {
                    color_class = "yellow-text";
                } else if (game.linux_support.tier == "BRONZE") {
                    color_class = "orange-text";
                } else if (game.linux_support.tier == "BORKED") {
                    color_class = "red-text";
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
            valueDiv.classList.add("grey-text");
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

            let purchaseData = [{
                historicalLowPrice: game.steam_historical_low,
                historicalLowTitle: game.steam_historical_low === null ? "Not available" : "From steamdb.info",

                price: game.steam.price,
                priceTitle: null,

                buttonText: "Buy on Steam",
                buttonClass: "steam-button",
                buttonURL: game.steam.external_url,
            }];

            if (game.key_and_gift_sellers !== null) {
                purchaseData.push({
                    historicalLowPrice: game.key_and_gift_sellers.historical_low.price,
                    historicalLowTitle: `Seller: ${game.key_and_gift_sellers.historical_low.seller}`,

                    price: game.key_and_gift_sellers.cheapest_offer.price,
                    priceTitle: `Form: ${game.key_and_gift_sellers.cheapest_offer.form}\nSeller: ${game.key_and_gift_sellers.cheapest_offer.seller}\nEdition: ${game.key_and_gift_sellers.cheapest_offer.edition}`,

                    buttonText: "Buy Key or Gift",
                    buttonClass: "keyforsteam-button",
                    buttonURL: game.key_and_gift_sellers.external_url
                })
            }

            purchaseData.forEach(purchase => {
                const purchaseAreaDiv = document.createElement("div");
                purchaseAreaDiv.className = "purchase-area";
                if (lowest_price !== null && purchase.price == lowest_price && lowest_price_color_class !== null) {
                    purchaseAreaDiv.classList.add(lowest_price_color_class);
                }

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
                if (purchase.historicalLowPrice === null) {
                    historicalLowValueDiv.textContent = "N/A";
                    historicalLowDiv.classList.add("grey-text");
                } else {
                    historicalLowValueDiv.textContent = display_price(purchase.historicalLowPrice);
                }
                historicalLowDiv.appendChild(historicalLowValueDiv);

                purchaseAreaDiv.appendChild(historicalLowDiv);

                const priceDiv = document.createElement("div");
                priceDiv.className = "price";
                if (purchase.priceTitle !== null) {
                    priceDiv.title = purchase.priceTitle;
                }
                priceDiv.textContent = display_price(purchase.price);
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
