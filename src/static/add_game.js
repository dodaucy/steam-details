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
    if (game.steam_historical_low !== null) {  // SteamDB data available
        if (game.key_and_gift_sellers !== null) {  // KeyForSteam data also available
            lowest_price = Math.min(game.steam.price, game.key_and_gift_sellers.cheapest_offer.price);
            var lowest_historical_low = Math.min(game.steam_historical_low.price, game.key_and_gift_sellers.historical_low.price);
        } else {  // Only SteamDB data available
            lowest_price = game.steam.price;
            var lowest_historical_low = game.steam_historical_low.price;
        }

        const price_difference = lowest_price - lowest_historical_low;

        let title = `How much money you could save if you wait longer\n\nHow this is calculated:\nlowest price (${display_price(lowest_price)}) - lowest historical low (${display_price(lowest_historical_low)})`;
        if (game.steam.price === 0.0) {
            var color_class = "rainbow-text";
            lowest_price_color_class = "rainbow-purchase-area";
        } else if (releaseDifferenceInYears >= 1) {
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
        if (game.key_and_gift_sellers !== null && !game.key_and_gift_sellers.id_verified) {
            title += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
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
        var value = display_date(game.steam.release_date.iso_date);
    } else {
        var value = game.steam.release_date.display_string;
    }
    detailsData.push({
        label: "RELEASE DATE:",
        value: value,
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
                    title: `${title_list.join("\n")}\n\nFrom: howlongtobeat.com\nClick to visit site`,
                    url: game.game_length.external_url
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
                    title: `${title_list.join("\n")}\n\nFrom: howlongtobeat.com\nClick to visit site`,
                    color_class: color_class,
                    url: game.game_length.external_url
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
                title: `Confidence: ${game.linux_support.confidence}\nReports: ${game.linux_support.report_count}\n\nFrom: protondb.com\nClick to visit site`,
                color_class: color_class,
                url: game.linux_support.external_url
            });
        }
    }

    // Add details
    detailsData.forEach(detail => {
        if (detail.url !== undefined) {
            var base_element = document.createElement("a");
            base_element.href = detail.url;
            base_element.target = "_blank";
        } else {
            var base_element = document.createElement("div");
        }

        const labelElement = base_element.cloneNode(false);
        labelElement.textContent = detail.label;
        detailsGridDiv.appendChild(labelElement);

        const valueElement = base_element.cloneNode(false);
        if (detail.value === null) {
            valueElement.textContent = "N/A";
            valueElement.classList.add("grey-text");
            labelElement.title = "Not available";
            valueElement.title = "Not available";
        } else {
            valueElement.textContent = detail.value;
            if (detail.color_class !== undefined) {
                valueElement.classList.add(detail.color_class);
            }
            labelElement.title = detail.title;
            valueElement.title = detail.title;
        }
        detailsGridDiv.appendChild(valueElement);
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

            // Steam price
            let historicalLowPrice = null;
            let historicalLowTitle = null;
            let historicalLowURL = undefined;
            if (game.steam_historical_low !== null) {
                historicalLowPrice = game.steam_historical_low.price;
                historicalLowTitle = `At Discount: ${game.steam_historical_low.discount}%\nDate: ${game.steam_historical_low.iso_date === null ? "Today": display_date(game.steam_historical_low.iso_date)}\n\nFrom: steamdb.info\nClick to visit site`;
                historicalLowURL = game.steam_historical_low.external_url;
            }
            let purchaseData = [{
                historicalLowPrice: historicalLowPrice,
                historicalLowTitle: historicalLowTitle,
                historicalLowURL: historicalLowURL,

                price: game.steam.price,
                priceTitle: `Discount: ${game.steam.discount}%`,

                buttonText: "Buy on Steam",
                buttonClass: "steam-button",
                buttonURL: game.steam.external_url
            }];

            // Key and gift sellers price
            if (game.key_and_gift_sellers !== null) {
                let historicalLowTitle = `Date: ${game.key_and_gift_sellers.historical_low.iso_date === null ? "Today": display_date(game.key_and_gift_sellers.historical_low.iso_date)}\nSeller: ${game.key_and_gift_sellers.historical_low.seller}`;
                let priceTitle = `Form: ${game.key_and_gift_sellers.cheapest_offer.form}\nSeller: ${game.key_and_gift_sellers.cheapest_offer.seller}\nEdition: ${game.key_and_gift_sellers.cheapest_offer.edition}`;
                if (!game.key_and_gift_sellers.id_verified) {
                    historicalLowTitle += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
                    priceTitle += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
                }
                purchaseData.push({
                    historicalLowPrice: game.key_and_gift_sellers.historical_low.price,
                    historicalLowTitle: historicalLowTitle,

                    price: game.key_and_gift_sellers.cheapest_offer.price,
                    priceTitle: priceTitle,

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

                if (purchase.historicalLowURL !== undefined) {
                    var historicalLowElement = document.createElement("a");
                    historicalLowElement.href = purchase.historicalLowURL;
                    historicalLowElement.target = "_blank";
                } else {
                    var historicalLowElement = document.createElement("div");
                }
                historicalLowElement.title = purchase.historicalLowTitle;
                historicalLowElement.className = "historical-low";

                const historicalLowLabelDiv = document.createElement("div");
                historicalLowLabelDiv.className = "small-font historical-low-label";
                historicalLowLabelDiv.textContent = "Historical low";
                historicalLowElement.appendChild(historicalLowLabelDiv);

                const historicalLowValueDiv = document.createElement("div");
                historicalLowValueDiv.className = "small-font historical-low-value";
                if (purchase.historicalLowPrice === null) {
                    historicalLowValueDiv.textContent = "N/A";
                    historicalLowElement.classList.add("grey-text");
                } else {
                    historicalLowValueDiv.textContent = display_price(purchase.historicalLowPrice);
                }
                historicalLowElement.appendChild(historicalLowValueDiv);

                purchaseAreaDiv.appendChild(historicalLowElement);

                const priceDiv = document.createElement("div");
                priceDiv.className = "price";
                priceDiv.title = purchase.priceTitle;
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
