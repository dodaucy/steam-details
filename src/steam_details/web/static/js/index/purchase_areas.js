function createPurchaseAreas(game, lowest_price, lowest_price_color_class) {
    const purchaseAreaContainerDiv = document.createElement("div");
    purchaseAreaContainerDiv.className = "purchase-area-container";

    if (game.modules.steam_core.data.released) {
        if (game.modules.steam_core.data.price === null) {
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
            if (game.modules.steam_historical_low.success) {
                if (game.modules.steam_historical_low.data !== null) {
                    historicalLowPrice = game.modules.steam_historical_low.data.price;

                    if (game.modules.steam_historical_low.data.iso_date === null) {
                        var date = "Today";
                    } else {
                        var date = display_date(game.modules.steam_historical_low.data.iso_date);
                    }

                    historicalLowTitle = `At Discount: ${game.modules.steam_historical_low.data.discount}%\nDate: ${date}`;

                    if (game.modules.steam_historical_low.data.external_url !== null) {
                        historicalLowTitle += `\n\nFrom: steamdb.info\nClick to visit site`;
                        historicalLowURL = game.modules.steam_historical_low.data.external_url;
                    }
                }
            } else {
                historicalLowError = game.modules.steam_historical_low.error;
                historicalLowErrorURL = game.modules.steam_historical_low.url;
            }
            let purchaseData = [{
                historicalLowError: historicalLowError,
                historicalLowErrorURL: historicalLowErrorURL,
                historicalLowPrice: historicalLowPrice,
                historicalLowTitle: historicalLowTitle,
                historicalLowURL: historicalLowURL,

                priceError: null,
                priceErrorURL: null,
                price: game.modules.steam_core.data.price,
                priceTitle: `Discount: ${game.modules.steam_core.data.discount}%`,

                buttonText: "Buy on Steam",
                buttonClass: "steam-button",
                buttonURL: game.modules.steam_core.data.external_url
            }];

            // Key and gift sellers price
            if (game.modules.key_and_gift_sellers.success) {
                if (game.modules.key_and_gift_sellers.data !== null) {
                    let historicalLowTitle = `Date: ${game.modules.key_and_gift_sellers.data.historical_low.iso_date === null ? "Today": display_date(game.modules.key_and_gift_sellers.data.historical_low.iso_date)}\nSeller: ${game.modules.key_and_gift_sellers.data.historical_low.seller}`;
                    let priceTitle = `Form: ${game.modules.key_and_gift_sellers.data.cheapest_offer.form}\nSeller: ${game.modules.key_and_gift_sellers.data.cheapest_offer.seller}\nEdition: ${game.modules.key_and_gift_sellers.data.cheapest_offer.edition}`;
                    if (!game.modules.key_and_gift_sellers.data.id_verified) {
                        historicalLowTitle += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
                        priceTitle += "\n\nThe steam id of the key or gift wasn't verified:\nThe key or gift price could be wrong!!";
                    }
                    purchaseData.push({
                        historicalLowError: null,
                        historicalLowErrorURL: null,
                        historicalLowPrice: game.modules.key_and_gift_sellers.data.historical_low.price,
                        historicalLowTitle: historicalLowTitle,
                        historicalLowURL: null,

                        priceError: null,
                        priceErrorURL: null,
                        price: game.modules.key_and_gift_sellers.data.cheapest_offer.price,
                        priceTitle: priceTitle,

                        buttonText: "Buy Key or Gift",
                        buttonClass: "keyforsteam-button",
                        buttonURL: game.modules.key_and_gift_sellers.data.external_url
                    })
                }
            } else {
                purchaseData.push({
                    historicalLowError: game.modules.key_and_gift_sellers.error,
                    historicalLowErrorURL: game.modules.key_and_gift_sellers.url,
                    historicalLowPrice: null,
                    historicalLowTitle: null,
                    historicalLowURL: null,

                    priceError: game.modules.key_and_gift_sellers.error,
                    priceErrorURL: game.modules.key_and_gift_sellers.url,
                    price: null,
                    priceTitle: null,

                    buttonText: "Buy Key or Gift",
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
                    historicalLowElement.className = "historical-low error-text";
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
                    priceElement.className = "price error-text";
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
                purchaseButton.textContent = purchase.buttonText;
                if (purchase.priceError !== null) {
                    purchaseButton.href = purchase.priceErrorURL;
                    purchaseButton.title = `${purchase.priceError}\n\nClick to visit the following site:\n${purchase.priceErrorURL}`;
                    purchaseButton.className = "error-button";
                } else {
                    purchaseButton.href = purchase.buttonURL;
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
