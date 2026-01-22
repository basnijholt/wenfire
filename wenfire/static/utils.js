// Toggle post-FIRE spending mode
function togglePostFireSpending() {
    const checkbox = document.getElementById('enable_post_fire_spending');
    const group = document.getElementById('post_fire_spending_group');
    const input = document.getElementById('post_fire_spending_per_month');
    const hiddenInput = document.getElementById('post_fire_spending_hidden');

    if (checkbox.checked) {
        group.style.display = 'block';
        input.disabled = false;
        input.name = 'post_fire_spending_per_month';
        hiddenInput.disabled = true;
    } else {
        group.style.display = 'none';
        input.disabled = true;
        input.name = '';
        hiddenInput.disabled = false;
    }
}

// Parameter change date/years sync function
const DAYS_PER_YEAR = 365.25;
const MS_PER_YEAR = DAYS_PER_YEAR * 24 * 60 * 60 * 1000; // milliseconds in a year

const syncDateYears = (target) => {
    const container = target.closest('.parameter-change');
    const dateInput = container.querySelector('.date-input');
    const yearsInput = container.querySelector('.years-input');

    if (target.classList.contains('date-input') && dateInput.value) {
        const years = Math.max(0, (new Date(dateInput.value) - Date.now()) / MS_PER_YEAR);
        yearsInput.value = years.toFixed(1);
    } else if (target.classList.contains('years-input') && yearsInput.value) {
        dateInput.value = new Date(Date.now() + parseFloat(yearsInput.value) * MS_PER_YEAR).toISOString().split('T')[0];
    }
};

// Update hidden date inputs when main date changes
const updateHiddenDateInputs = (parameterChange) => {
    const mainDateInput = parameterChange.querySelector('.date-input');
    const hiddenDateInputs = parameterChange.querySelectorAll('input[name="change_dates"][type="hidden"]');

    hiddenDateInputs.forEach(hiddenInput => {
        hiddenInput.value = mainDateInput.value;
    });
};

// Update visibility of remove buttons based on number of rows
const updateParameterRowVisibility = (container) => {
    const show = container.querySelectorAll('.parameter-row').length > 1 ? 'block' : 'none';
    container.querySelectorAll('.remove-parameter-row').forEach(btn => btn.style.display = show);
};

document.addEventListener('DOMContentLoaded', function () {
    // Initialize theme system
    initializeTheme();

    // Auto-calculate if URL parameters exist
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.toString()) {
        htmx.trigger('#calculate-form', 'submit');
    }

    // Initialize parameter change date/years sync for existing data
    document.querySelectorAll('.parameter-change .date-input').forEach(dateInput => {
        if (dateInput.value) {
            syncDateYears(dateInput);
        }
    });

    // Initialize parameter row visibility for existing blocks
    document.querySelectorAll('.parameter-rows-container').forEach(updateParameterRowVisibility);

    // Add loading states to form submission
    const form = document.getElementById('calculate-form');
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.dataset.original = submitBtn.innerHTML; // Store original on page load

    const toggleLoading = (isLoading) => {
        submitBtn.disabled = isLoading;
        submitBtn.innerHTML = isLoading
            ? '<span class="loading me-2"></span>Calculating...'
            : submitBtn.dataset.original;
    };

    form.addEventListener('htmx:beforeRequest', () => toggleLoading(true));
    form.addEventListener('htmx:afterRequest', () => toggleLoading(false));

    // Add smooth scrolling to results
    document.addEventListener('htmx:afterSwap', function (event) {
        if (event.detail.target.id === 'results-container') {
            event.detail.target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });

            // Trigger chart rendering after a small delay to ensure DOM is ready
            setTimeout(() => {
                if (typeof window.renderChartsFromData === 'function') {
                    window.renderChartsFromData();
                }
            }, 200);
        }

        // Handle newly added parameter rows via HTMX
        if (event.detail.target.classList.contains('parameter-rows-container')) {
            const container = event.detail.target;

            // Newly inserted row is the last child of the container
            const newRow = container.lastElementChild;
            if (newRow && newRow.classList.contains('parameter-row')) {
                const parameterChange = newRow.closest('.parameter-change');
                updateHiddenDateInputs(parameterChange);
            }

            // Update remove button visibility for this container
            updateParameterRowVisibility(container);
        }

        // Initialize new parameter change blocks added via HTMX
        if (event.detail.target.classList.contains('parameter-change')) {
            const container = event.detail.target.querySelector('.parameter-rows-container');
            if (container) {
                updateParameterRowVisibility(container);
            }
        }
    });

    // Handle parameter row removal via HTMX - use beforeSwap to catch removal
    document.addEventListener('htmx:beforeSwap', function (event) {
        // Check if this is a parameter row removal request
        if (event.detail.xhr && event.detail.xhr.responseURL && event.detail.xhr.responseURL.includes('/remove-parameter-row')) {
            // The target element is about to be removed, so find its container now
            const rowToRemove = event.detail.target;
            const container = rowToRemove.closest('.parameter-rows-container');

            // Update visibility after the DOM change (use setTimeout to ensure removal is complete)
            if (container) {
                setTimeout(() => {
                    updateParameterRowVisibility(container);
                }, 10);
            }
        }
    });

    // Chart rendering setup (runs once, doesn't get re-executed by HTMX)
    setupChartRendering();
});

// Event listeners for parameter change sync
['input', 'change'].forEach(eventType => {
    document.addEventListener(eventType, (e) => {
        if (e.target.matches('.date-input, .years-input')) {
            syncDateYears(e.target);

            // Update hidden date inputs when main date changes
            if (e.target.classList.contains('date-input')) {
                const parameterChange = e.target.closest('.parameter-change');
                updateHiddenDateInputs(parameterChange);
            }
        }
    });
});

// Simplified theme management
function initializeTheme() {
    const toggleBtn = document.getElementById('theme-toggle');
    const userPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const currentTheme = localStorage.getItem('theme') || (userPrefersDark ? 'dark' : 'light');

    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-bs-theme', theme);
        const isDark = theme === 'dark';
        toggleBtn.innerHTML = `<i class="fas fa-${isDark ? 'sun' : 'moon'}"></i> ${isDark ? 'Light' : 'Dark'} Mode`;
        toggleBtn.className = `btn btn-outline-${isDark ? 'warning' : 'secondary'}`;
        localStorage.setItem('theme', theme);
    };

    setTheme(currentTheme);
    toggleBtn.addEventListener('click', () => {
        const newTheme = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });
}

function setupChartRendering() {
    // Store chart instances for theme switching
    window.chartInstances = { netWorth: null, monthlyFlows: null };

    // Utility functions
    const formatCurrency = (val) => {
        if (val < 1_000) return '$' + val.toFixed(0);
        if (val < 100_000) return '$' + (val / 1_000).toFixed(1) + 'k';
        if (val < 1_000_000) return '$' + (val / 1_000).toFixed(0) + 'k';
        if (val < 10_000_000) return '$' + (val / 1_000_000).toFixed(1) + 'M';
        return '$' + (val / 1_000_000).toFixed(0) + 'M';
    };

    const enhanceConfig = (config) => {
        if (config.yaxis?.labels) {
            config.yaxis.labels.formatter = formatCurrency;
        }
        if (config.tooltip) {
            config.tooltip.custom = ({ series, seriesIndex, dataPointIndex, w }) => {
                const data = w.config.series[seriesIndex].data[dataPointIndex];
                const date = new Date(w.globals.seriesX[seriesIndex][dataPointIndex]);

                const title = `<div class="apexcharts-tooltip-title" style="font-family: inherit; font-size: 12px;">${date.toLocaleDateString()} (Age: ${data.age.toFixed(1)}, ${data.time_from_now_text})</div>`;

                const items = series.map((s, i) => s[dataPointIndex] !== undefined ?
                    `<div class="apexcharts-tooltip-series-group apexcharts-active" style="order: 1; display: flex;">
                        <span class="apexcharts-tooltip-marker" style="background-color: ${w.globals.colors[i]};"></span>
                        <div class="apexcharts-tooltip-text" style="font-family: inherit; font-size: 12px;">
                            <div class="apexcharts-tooltip-y-group">
                                <span class="apexcharts-tooltip-text-y-label">${w.globals.seriesNames[i]}: </span>
                                <span class="apexcharts-tooltip-text-y-value">${formatCurrency(s[dataPointIndex])}</span>
                            </div>
                        </div>
                    </div>`
                    : ''
                ).join('');

                return title + items;
            };
        }
        return config;
    };

    const renderChart = (chartKey, containerId, dataKey) => {
        const container = document.querySelector(containerId);
        if (!container || !window.chartData?.[dataKey]) return;

        // Destroy existing chart
        if (window.chartInstances[chartKey]) {
            window.chartInstances[chartKey].destroy();
            window.chartInstances[chartKey] = null;
        }

        const plotData = window.chartData[dataKey];
        const theme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const config = enhanceConfig(theme === 'dark' ? plotData.config_dark : plotData.config_light);

        window.chartInstances[chartKey] = new ApexCharts(container, config);
        window.chartInstances[chartKey].render().then(() => {
            container.addEventListener('dblclick', () => {
                window.chartInstances[chartKey].resetSeries();
                const dates = config.series[0].data.map(d => new Date(d.x).getTime());
                window.chartInstances[chartKey].zoomX(Math.min(...dates), Math.max(...dates));
            });
        }).catch(error => console.error(`Error rendering ${chartKey} chart:`, error));
    };

    // Main render function
    window.renderChartsFromData = () => {
        if (!window.chartData) return;
        renderChart('netWorth', '#age-vs-net-worth-plot', 'netWorth');
        renderChart('monthlyFlows', '#monthly-financial-flows-plot', 'monthlyFlows');
    };

    // Theme change monitoring
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-bs-theme') {
                window.renderChartsFromData();
            }
        });
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] });

    window.addEventListener('storage', e => {
        if (e.key === 'theme') window.renderChartsFromData();
    });
}
