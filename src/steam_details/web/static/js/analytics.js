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
        data = await request("GET", "analyze");
    } catch (error) {
        console.error(error);
        // Display error
        const errorDiv = document.createElement("div");
        errorDiv.className = "error-text";
        errorDiv.innerText = error.message;
        elements.push(errorDiv);
    }

    if (elements.length == 0) {  // No error
        // Display cache stats
        const cacheStats = document.createElement("div");
        cacheStats.id = "cache-stats";

        // Cache entries
        const cacheDisplay = document.createElement("div");
        cacheDisplay.innerText = `Cache entries: ${data.cache_entries}`;
        cacheStats.appendChild(cacheDisplay);

        // Clear cache button
        const clearCacheButton = document.createElement("a");
        clearCacheButton.href = "javascript:void(0)";
        clearCacheButton.innerText = "Clear cache";
        clearCacheButton.className = "general-button";
        clearCacheButton.onclick = async () => {
            try {
                alert((await request("POST", "clear_cache")).message);
                location.reload();
            } catch (error) {
                console.error(error);
                alert(error.message);
            }
        }
        cacheStats.appendChild(clearCacheButton);

        elements.push(cacheStats);

        // Display module stats
        const moduleStats = document.createElement("div");
        moduleStats.id = "module-stats";
        moduleStats.className = "center-text";

        for (const module of data.modules) {
            const moduleElement = document.createElement("div");

            // Title
            const moduleTitle = document.createElement("div");
            moduleTitle.innerText = module.name;
            moduleTitle.className = "title";
            moduleElement.appendChild(moduleTitle);

            // Load time
            const moduleLoadTime = document.createElement("div");

            const moduleLoadTimeTitle = document.createElement("div");
            moduleLoadTimeTitle.innerText = "Load Time";
            moduleLoadTime.appendChild(moduleLoadTimeTitle);

            const moduleLoadTimeValue = document.createElement("div");
            if (module.load_time === null) {
                moduleLoadTimeValue.innerText = "Not loaded";
                moduleLoadTimeValue.className = "error-text";
            } else {
                moduleLoadTimeValue.innerText = module.load_time + "s";
                if (module.load_time > 10) {  // Very high load time
                    moduleLoadTimeValue.className = "red-text";
                } else if (module.load_time > 5) {  // High load time
                    moduleLoadTimeValue.className = "orange-text";
                } else if (module.load_time > 3) {  // Medium load time
                    moduleLoadTimeValue.className = "yellow-text";
                } else {  // Low load time
                    moduleLoadTimeValue.className = "green-text";
                }
            }

            moduleLoadTime.appendChild(moduleLoadTimeValue);

            moduleElement.appendChild(moduleLoadTime);

            // Timeout count
            const moduleTimeoutCount = document.createElement("div");

            const moduleTimeoutCountTitle = document.createElement("div");
            moduleTimeoutCountTitle.innerText = "Timeout Count";
            moduleTimeoutCount.appendChild(moduleTimeoutCountTitle);

            const moduleTimeoutCountValue = document.createElement("div");
            moduleTimeoutCountValue.innerText = module.timeout_count;
            moduleTimeoutCount.appendChild(moduleTimeoutCountValue);

            if (module.timeout_count >= 3) {  // Many timeouts
                moduleTimeoutCountValue.className = "red-text";
            } else if (module.timeout_count > 0) {  // Timeouts
                moduleTimeoutCountValue.className = "orange-text";
            } else {  // No timeouts
                moduleTimeoutCountValue.className = "green-text";
            }

            moduleElement.appendChild(moduleTimeoutCount);

            // Error count
            const moduleErrorCount = document.createElement("div");

            const moduleErrorCountTitle = document.createElement("div");
            moduleErrorCountTitle.innerText = "Error Count";
            moduleErrorCount.appendChild(moduleErrorCountTitle);

            const moduleErrorCountValue = document.createElement("div");
            moduleErrorCountValue.innerText = module.error_count;
            moduleErrorCount.appendChild(moduleErrorCountValue);

            if (module.error_count >= 3) {  // Many errors
                moduleErrorCountValue.className = "red-text";
            } else if (module.error_count > 0) {  // Errors
                moduleErrorCountValue.className = "orange-text";
            } else {  // No errors
                moduleErrorCountValue.className = "green-text";
            }

            moduleElement.appendChild(moduleErrorCount);

            // Add to list
            moduleStats.appendChild(moduleElement);
        }

        elements.push(moduleStats);

        // Display speed box plot
        if (data.speed_box_plot != null) {
            const speedBoxPlot = document.createElement("img");
            speedBoxPlot.id = "speed-box-plot";
            speedBoxPlot.src = `data:image/png;base64,${data.speed_box_plot}`
            elements.push(speedBoxPlot);
        } else {
            const noData = document.createElement("div");
            noData.id = "speed-box-plot";
            noData.className = "error-text center-text";
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
