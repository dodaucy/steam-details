function createDetailsGrid(game) {
    const detailsGridDiv = document.createElement("div");
    detailsGridDiv.className = "small-font details-grid";

    let detailsData = [];

    // Get release difference
    let releaseDifferenceInDays = null;
    let releaseDifferenceInYears = null;
    if (game.services.steam.data.released && game.services.steam.data.release_date !== null) {
        const date = new Date(game.services.steam.data.release_date.iso_date);
        const now = new Date();
        const dateDiff = now - date;
        releaseDifferenceInDays = Math.floor(dateDiff / (1000 * 60 * 60 * 24));
        releaseDifferenceInYears = Math.floor(releaseDifferenceInDays / 365 * 10) / 10;
    }

    // Price difference
    let lowest_price_color_class = null;
    let lowest_price = null;
    if (!game.services.steam_historical_low.success && !game.services.key_and_gift_sellers.success) {
        detailsData.push({
            label: "PRICE DIFFERENCE:",
            value: "ERROR",
            title: `${game.services.steam_historical_low.error}\n${game.services.key_and_gift_sellers.error}`,
            color_class: "error-text"
        });
    } else if (!game.services.steam_historical_low.success) {
        detailsData.push({
            label: "PRICE DIFFERENCE:",
            value: "ERROR",
            title: game.services.steam_historical_low.error,
            color_class: "error-text"
        });
    } else if (!game.services.key_and_gift_sellers.success) {
        detailsData.push({
            label: "PRICE DIFFERENCE:",
            value: "ERROR",
            title: game.services.key_and_gift_sellers.error,
            color_class: "error-text"
        });
    } else {
        if (game.services.steam_historical_low.data !== null) {  // SteamDB data available
            if (game.services.key_and_gift_sellers.data !== null) {  // KeyForSteam data also available
                lowest_price = Math.min(game.services.steam.data.price, game.services.key_and_gift_sellers.data.cheapest_offer.price);
                var lowest_historical_low = Math.min(game.services.steam_historical_low.data.price, game.services.key_and_gift_sellers.data.historical_low.price);
            } else {  // Only SteamDB data available
                lowest_price = game.services.steam.data.price;
                var lowest_historical_low = game.services.steam_historical_low.data.price;
            }

            const price_difference = lowest_price - lowest_historical_low;

            let title = `How much money you could save if you wait longer\n\nHow this is calculated:\nlowest price (${display_price(lowest_price)}) - lowest historical low (${display_price(lowest_historical_low)})`;
            if (game.services.steam.data.price === 0.0) {
                var color_class = "rainbow-text";
                lowest_price_color_class = "rainbow-purchase-area";
            } else if (game.services.steam.data.release_date === null) {
                var color_class = "grey-text";
                title += "\n\nThe release date is unknown!!";
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
            if (game.services.key_and_gift_sellers.data !== null && !game.services.key_and_gift_sellers.data.id_verified) {
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
    }

    // Release date
    let title = "Release date of the game";
    if (game.services.steam.data.release_date === null) {
        detailsData.push({
            label: "RELEASE DATE:",
            value: null
        })
    } else {
        if (game.services.steam.data.released) {
            if (releaseDifferenceInYears >= 1) {
                title = `Released ${releaseDifferenceInYears.toString().replace(".", ",")} year${releaseDifferenceInYears !== 1 ? "s" : ""} ago`;
            } else if (releaseDifferenceInDays >= 0) {
                title = `Released ${releaseDifferenceInDays} day${releaseDifferenceInDays !== 1 ? "s" : ""} ago`;
            }
            var value = display_date(game.services.steam.data.release_date.iso_date);
        } else {
            var value = game.services.steam.data.release_date.display_string;
        }
        detailsData.push({
            label: "RELEASE DATE:",
            value: value,
            title: title
        });
    }

    // Reviews
    if (game.services.steam.data.released) {
        let color_class = "red-text";
        if (game.services.steam.data.overall_reviews.score >= 75) {
            color_class = "green-text";
        } else if (game.services.steam.data.overall_reviews.score >= 50) {
            color_class = "yellow-text";
        } else if (game.services.steam.data.overall_reviews.score >= 25) {
            color_class = "orange-text";
        }
        detailsData.push({
            label: "OVERALL REVIEWS:",
            value: `${game.services.steam.data.overall_reviews.desc} (${game.services.steam.data.overall_reviews.score}%)`,
            title: `${game.services.steam.data.overall_reviews.score}% of ${game.services.steam.data.overall_reviews.total_reviews.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")} reviews are positive`,
            color_class: color_class
        });
    } else {
        detailsData.push({
            label: "OVERALL REVIEWS:",
            value: null
        });
    }

    // Game length
    if (!game.services.game_length.success) {
        detailsData.push({
            label: "GAME LENGTH:",
            value: "ERROR",
            title: `${game.services.game_length.error}\n\nClick to visit the following site:\n${game.services.game_length.url}`,
            color_class: "error-text",
            url: game.services.game_length.url
        });
    } else {
        if (game.services.game_length.data === null){
            detailsData.push({
                label: "GAME LENGTH:",
                value: null
            });
        } else {
            let title_list = [];
            if (game.services.game_length.data.main !== null) {
                title_list.push(`Main Story: ${display_time(game.services.game_length.data.main)}`);
            }
            if (game.services.game_length.data.plus !== null) {
                title_list.push(`Main + Extras: ${display_time(game.services.game_length.data.plus)}`);
            }
            if (game.services.game_length.data.completionist !== null) {
                title_list.push(`Completionist: ${display_time(game.services.game_length.data.completionist)}`);
            }
            if (title_list.length > 0) {
                if (game.services.game_length.data.plus === null) {
                    detailsData.push({
                        label: "GAME LENGTH:",
                        value: "Hover for info",
                        title: `${title_list.join("\n")}\n\nFrom: howlongtobeat.com\nClick to visit site`,
                        url: game.services.game_length.data.external_url
                    });
                } else {
                    const hours = game.services.game_length.data.plus / 3600;
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
                        value: display_time_as_float(game.services.game_length.data.plus),
                        title: `${title_list.join("\n")}\n\nFrom: howlongtobeat.com\nClick to visit site`,
                        color_class: color_class,
                        url: game.services.game_length.data.external_url
                    });
                }
            } else {
                detailsData.push({
                    label: "GAME LENGTH:",
                    value: null
                });
            }
        }
    }

    // Achievements
    if (game.services.steam.data.released) {
        if (game.services.steam.data.achievement_count >= 20) {
            color_class = "green-text";
        } else if (game.services.steam.data.achievement_count >= 10) {
            color_class = "yellow-text";
        } else if (game.services.steam.data.achievement_count >= 1) {
            color_class = "orange-text";
        } else {
            color_class = "red-text";
        }
        detailsData.push({
            label: "ACHIEVEMENTS:",
            value: game.services.steam.data.achievement_count,
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
    if (!game.services.linux_support.success) {
        detailsData.push({
            label: "LINUX SUPPORT:",
            value: "ERROR",
            title: `${game.services.linux_support.error}\n\nClick to visit the following site:\n${game.services.linux_support.url}`,
            color_class: "error-text",
            url: game.services.linux_support.url
        });
    } else {
        if (game.services.steam.data.native_linux_support) {
            detailsData.push({
                label: "LINUX SUPPORT:",
                value: "NATIVE",
                title: "The game is natively supported on Linux",
                color_class: "green-text"
            });
        } else {
            if (game.services.linux_support.data == null || game.services.linux_support.data.tier == "PENDING") {
                detailsData.push({
                    label: "LINUX SUPPORT:",
                    value: null
                });
            } else {
                let color_class = "grey-text";
                if (["moderate", "good", "strong"].includes(game.services.linux_support.data.confidence)) {
                    if (game.services.linux_support.data.tier == "PLATINUM" || game.services.linux_support.data.tier == "GOLD") {
                        color_class = "green-text";
                    } else if (game.services.linux_support.data.tier == "SILVER") {
                        color_class = "yellow-text";
                    } else if (game.services.linux_support.data.tier == "BRONZE") {
                        color_class = "orange-text";
                    } else if (game.services.linux_support.data.tier == "BORKED") {
                        color_class = "red-text";
                    }
                }
                detailsData.push({
                    label: "LINUX SUPPORT:",
                    value: game.services.linux_support.data.tier,
                    title: `Confidence: ${game.services.linux_support.data.confidence}\nReports: ${game.services.linux_support.data.report_count}\n\nFrom: protondb.com\nClick to visit site`,
                    color_class: color_class,
                    url: game.services.linux_support.data.external_url
                });
            }
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

    return [detailsGridDiv, lowest_price, lowest_price_color_class];
}
