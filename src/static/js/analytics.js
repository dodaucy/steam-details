async function analyze() {
    const analyticsContent = document.getElementById("analytics-content");

    // Display loading
    const loading = document.createElement("div");
    loading.className = "title";
    analyticsContent.appendChild(loading);

    const elements = [];

    try {
        data = await getRequest("/analyze");
    } catch (error) {
        // Display error
        const errorDiv = document.createElement("div");
        errorDiv.className = "red-text";
        errorDiv.innerText = error.message;
        elements.push(errorDiv);
    }

    if (elements.length == 0) {
        // Display service stats
        const serviceStats = document.createElement("div");
        serviceStats.id = "service-stats";
        Object.keys(data.services).forEach((service) => {
            const serviceElement = document.createElement("div");

            // Title
            const serviceTitle = document.createElement("div");
            serviceTitle.innerText = service;
            serviceTitle.className = "title";
            serviceElement.appendChild(serviceTitle);

            // Stats
            const serviceStatsElement = document.createElement("div");
            Object.keys(data.services[service]).forEach((key) => {
                const serviceStat = document.createElement("div");
                let stat_name = key;
                let end = "";
                if (key == "load_time") {  // Load time
                    stat_name = "Load Time";
                    end = "s";
                    if (data.services[service][key] > 10) {  // Very high load time
                        serviceStat.className = "red-text";
                    } else if (data.services[service][key] > 5) {  // High load time
                        serviceStat.className = "orange-text";
                    } else if (data.services[service][key] > 3) {  // Medium load time
                        serviceStat.className = "yellow-text";
                    } else {  // Low load time
                        serviceStat.className = "green-text";
                    }
                } else if (key == "timeout_count") {  // Timeout count
                    stat_name = "Timeout Count";
                    if (data.services[service][key] > 3) {  // Many timeouts
                        serviceStat.className = "red-text";
                    } else if (data.services[service][key] > 0) {  // Timeouts
                        serviceStat.className = "orange-text";
                    } else {  // No timeouts
                        serviceStat.className = "green-text";
                    }
                } else if (key == "error_count") {  // Error count
                    stat_name = "Error Count";
                    if (data.services[service][key] > 3) {  // Many errors
                        serviceStat.className = "red-text";
                    } else if (data.services[service][key] > 0) {  // Errors
                        serviceStat.className = "orange-text";
                    } else {  // No errors
                        serviceStat.className = "green-text";
                    }
                }
                serviceStat.innerText = `${stat_name}: ${data.services[service][key]}${end}`;
                serviceStatsElement.appendChild(serviceStat);

                serviceElement.appendChild(serviceStatsElement);

            })
            serviceStats.appendChild(serviceElement);
        });
        elements.push(serviceStats);

        // Display speed box plot
        if (data.speed_box_plot != null) {
            const speedBoxPlot = document.createElement("img");
            speedBoxPlot.id = "speed-box-plot";
            speedBoxPlot.src = `data:image/png;base64,${data.speed_box_plot}`
            elements.push(speedBoxPlot);
        } else {
            const noData = document.createElement("div");
            noData.id = "speed-box-plot";
            noData.className = "red-text center-text";
            noData.innerText = "No data for the speed box plot available. Search for some games first. The more games you search, the better the results will be.";
            elements.push(noData);
        }
    }

    // Clear content
    analyticsContent.innerHTML = "";

    // Add children
    elements.forEach((element) => {
        analyticsContent.appendChild(element);
    });
}


document.addEventListener("DOMContentLoaded", analyze);
