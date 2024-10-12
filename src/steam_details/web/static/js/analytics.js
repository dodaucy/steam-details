async function analyze() {
    const analyticsContent = document.getElementById("analytics-content");

    // Clear content
    analyticsContent.innerHTML = "";

    // Display loading
    const loading = document.createElement("div");
    loading.className = "title margin-top";
    loading.innerText = "Analyzing...";
    analyticsContent.appendChild(loading);

    const elements = [];

    try {
        data = await getRequest("analyze");
    } catch (error) {
        console.error(error);
        // Display error
        const errorDiv = document.createElement("div");
        errorDiv.className = "error";
        errorDiv.innerText = error.message;
        elements.push(errorDiv);
    }

    if (elements.length == 0) {  // No error
        // Display service stats
        const serviceStats = document.createElement("div");
        serviceStats.id = "service-stats";
        serviceStats.className = "center-text";

        for (const service of data.services) {
            const serviceElement = document.createElement("div");

            // Title
            const serviceTitle = document.createElement("div");
            serviceTitle.innerText = service.name;
            serviceTitle.className = "title";
            serviceElement.appendChild(serviceTitle);

            // Load time
            const serviceLoadTime = document.createElement("div");

            const serviceLoadTimeTitle = document.createElement("div");
            serviceLoadTimeTitle.innerText = "Load Time";
            serviceLoadTime.appendChild(serviceLoadTimeTitle);

            const serviceLoadTimeValue = document.createElement("div");
            serviceLoadTimeValue.innerText = service.load_time + "s";
            serviceLoadTime.appendChild(serviceLoadTimeValue);

            if (service.load_time > 10) {  // Very high load time
                serviceLoadTimeValue.className = "red-text";
            } else if (service.load_time > 5) {  // High load time
                serviceLoadTimeValue.className = "orange-text";
            } else if (service.load_time > 3) {  // Medium load time
                serviceLoadTimeValue.className = "yellow-text";
            } else {  // Low load time
                serviceLoadTimeValue.className = "green-text";
            }

            serviceElement.appendChild(serviceLoadTime);

            // Timeout count
            const serviceTimeoutCount = document.createElement("div");

            const serviceTimeoutCountTitle = document.createElement("div");
            serviceTimeoutCountTitle.innerText = "Timeout Count";
            serviceTimeoutCount.appendChild(serviceTimeoutCountTitle);

            const serviceTimeoutCountValue = document.createElement("div");
            serviceTimeoutCountValue.innerText = service.timeout_count;
            serviceTimeoutCount.appendChild(serviceTimeoutCountValue);

            if (service.timeout_count >= 3) {  // Many timeouts
                serviceTimeoutCountValue.className = "red-text";
            } else if (service.timeout_count > 0) {  // Timeouts
                serviceTimeoutCountValue.className = "orange-text";
            } else {  // No timeouts
                serviceTimeoutCountValue.className = "green-text";
            }

            serviceElement.appendChild(serviceTimeoutCount);

            // Error count
            const serviceErrorCount = document.createElement("div");

            const serviceErrorCountTitle = document.createElement("div");
            serviceErrorCountTitle.innerText = "Error Count";
            serviceErrorCount.appendChild(serviceErrorCountTitle);

            const serviceErrorCountValue = document.createElement("div");
            serviceErrorCountValue.innerText = service.error_count;
            serviceErrorCount.appendChild(serviceErrorCountValue);

            if (service.error_count >= 3) {  // Many errors
                serviceErrorCountValue.className = "red-text";
            } else if (service.error_count > 0) {  // Errors
                serviceErrorCountValue.className = "orange-text";
            } else {  // No errors
                serviceErrorCountValue.className = "green-text";
            }

            serviceElement.appendChild(serviceErrorCount);

            // Add to list
            serviceStats.appendChild(serviceElement);
        }

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
            noData.className = "error center-text";
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
