function createPurchaseAreas(game, lowest_price, lowest_price_color_class) {
    const purchaseAreaContainerDiv = document.createElement("div");
    purchaseAreaContainerDiv.className = "purchase-area-container";

    if (game.services.steam.data.released) {
        if (game.services.steam.data.price === null) {
            const purchaseAreaDiv = document.createElement("div");
            purchaseAreaDiv.className = "purchase-area";

            const priceDiv = document.createElement("div");
            priceDiv.className = "price";
            priceDiv.textContent = "Not available";

            purchaseAreaDiv.appendChild(priceDiv);

            purchaseAreaContainerDiv.appendChild(purchaseAreaDiv);
        } else {
            // Steam price
            let historicalLowError = null;
            let historicalLowErrorURL = null;
            let historicalLowPrice = null;
            let historicalLowTitle = null;
            let historicalLowURL = null;
            if (game.services.steam_historical_low.success) {
                if (game.services.steam_historical_low.data !== null) {
                    historicalLowPrice = game.services.steam_historical_low.data.price;
                    historicalLowTitle = `At Discount: ${game.services.steam_historical_low.data.discount}%\nDate: ${game.services.steam_historical_low.data.iso_date === null ? "Today": display_date(game.services.steam_historical_low.data.iso_date)}\n\nFrom: steamdb.info\nClick to visit site`;
                    historicalLowURL = game.services.steam_historical_low.data.external_url;
                }
            } else {
                historicalLowError = game.services.steam_historical_low.error;
                historicalLowErrorURL = game.services.steam_historical_low.url;
            }
            let purchaseData = [{
                historicalLowError: historicalLowError,
                historicalLowErrorURL: historicalLowErrorURL,
                historicalLowPrice: historicalLowPrice,
                historicalLowTitle: historicalLowTitle,
                historicalLowURL: historicalLowURL,

                priceError: null,
                priceErrorURL: null,
                price: game.services.steam.data.price,
                priceTitle: `Discount: ${game.services.steam.data.discount}%`,

                buttonText: "Buy on Steam",
                buttonClass: "steam-button",
                buttonURL: game.services.steam.data.external_url
            }];

            // Key and gift sellers price
            if (game.services.key_and_gift_sellers.success) {
                if (game.services.key_and_gift_sellers.data !== null) {
                    let historicalLowTitle = `Date: ${game.services.key_and_gift_sellers.data.historical_low.iso_date === null ? "Today": display_date(game.services.key_and_gift_sellers.data.historical_low.iso_date)}\nSeller: ${game.services.key_and_gift_sellers.data.historical_low.seller}`;
                    let priceTitle = `Form: ${game.services.key_and_gift_sellers.data.cheapest_offer.form}\nSeller: ${game.services.key_and_gift_sellers.data.cheapest_offer.seller}\nEdition: ${game.services.key_and_gift_sellers.data.cheapest_offer.edition}`;
                    if (!game.services.key_and_gift_sellers.data.id_verified) {
                        historicalLowTitle += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
                        priceTitle += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
                    }
                    purchaseData.push({
                        historicalLowError: null,
                        historicalLowErrorURL: null,
                        historicalLowPrice: game.services.key_and_gift_sellers.data.historical_low.price,
                        historicalLowTitle: historicalLowTitle,
                        historicalLowURL: null,

                        priceError: null,
                        priceErrorURL: null,
                        price: game.services.key_and_gift_sellers.data.cheapest_offer.price,
                        priceTitle: priceTitle,

                        buttonText: "Buy Key or Gift",
                        buttonClass: "keyforsteam-button",
                        buttonURL: game.services.key_and_gift_sellers.data.external_url
                    })
                }
            } else {
                purchaseData.push({
                    historicalLowError: game.services.key_and_gift_sellers.error,
                    historicalLowErrorURL: game.services.key_and_gift_sellers.url,
                    historicalLowPrice: null,
                    historicalLowTitle: null,
                    historicalLowURL: null,

                    priceError: game.services.key_and_gift_sellers.error,
                    priceErrorURL: game.services.key_and_gift_sellers.url,
                    price: null,
                    priceTitle: null,

                    buttonText: null,
                    buttonClass: "keyforsteam-button",
                    buttonURL: null
                })
            }

            purchaseData.forEach(purchase => {
                const purchaseAreaDiv = document.createElement("div");
                purchaseAreaDiv.className = "purchase-area";
                if (lowest_price !== null && purchase.price !== null && purchase.price == lowest_price && lowest_price_color_class !== null) {
                    purchaseAreaDiv.classList.add(lowest_price_color_class);
                }

                if (purchase.historicalLowError !== null) {
                    var historicalLowElement = document.createElement("a");
                    historicalLowElement.href = purchase.historicalLowErrorURL;
                    historicalLowElement.target = "_blank";
                    historicalLowElement.title = `${purchase.historicalLowError}\n\nClick to visit the following site:\n${purchase.historicalLowErrorURL}`;
                    historicalLowElement.className = "historical-low error";
                } else {
                    if (purchase.historicalLowURL !== null) {
                        var historicalLowElement = document.createElement("a");
                        historicalLowElement.href = purchase.historicalLowURL;
                        historicalLowElement.target = "_blank";
                        historicalLowElement.className = "historical-low";
                    } else {
                        var historicalLowElement = document.createElement("div");
                        historicalLowElement.className = "historical-low";
                    }
                    historicalLowElement.title = purchase.historicalLowTitle;
                }

                const historicalLowLabelDiv = document.createElement("div");
                historicalLowLabelDiv.className = "small-font historical-low-label";
                historicalLowLabelDiv.textContent = "Historical low";
                historicalLowElement.appendChild(historicalLowLabelDiv);

                const historicalLowValueElement = document.createElement("div");
                if (purchase.historicalLowError !== null) {
                    historicalLowValueElement.textContent = "ERROR";
                } else if (purchase.historicalLowPrice === null) {
                    historicalLowValueElement.textContent = "N/A";
                    historicalLowElement.title = "Not available";
                    historicalLowElement.classList.add("grey-text");
                } else {
                    historicalLowValueElement.textContent = display_price(purchase.historicalLowPrice);
                }
                historicalLowValueElement.className = "small-font historical-low-value";
                historicalLowElement.appendChild(historicalLowValueElement);

                purchaseAreaDiv.appendChild(historicalLowElement);

                let priceElement = null;
                if (purchase.priceError !== null) {
                    priceElement = document.createElement("a");
                    priceElement.className = "price error";
                    priceElement.href = purchase.priceErrorURL;
                    priceElement.target = "_blank";
                    priceElement.title = `${purchase.priceError}\n\nClick to visit the following site:\n${purchase.priceErrorURL}`;
                    priceElement.textContent = "ERROR";
                } else {
                    priceElement = document.createElement("div");
                    priceElement.className = "price";
                    priceElement.title = purchase.priceTitle;
                    priceElement.textContent = display_price(purchase.price);
                }
                purchaseAreaDiv.appendChild(priceElement);

                const purchaseButton = document.createElement("a");
                purchaseButton.target = "_blank";
                if (purchase.priceError !== null) {
                    purchaseButton.href = purchase.priceErrorURL;
                    purchaseButton.title = `${purchase.priceError}\n\nClick to visit the following site:\n${purchase.priceErrorURL}`;
                    purchaseButton.textContent = "ERROR";
                    purchaseButton.className = "error-button";
                } else {
                    purchaseButton.href = purchase.buttonURL;
                    purchaseButton.textContent = purchase.buttonText;
                    purchaseButton.className = purchase.buttonClass;
                }
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

    return purchaseAreaContainerDiv;
}
