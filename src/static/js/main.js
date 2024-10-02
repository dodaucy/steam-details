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
