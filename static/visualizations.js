class SQLVisualizer {
  constructor() {
    // Custom colors for visualization
    this.colors = [
      'rgba(94, 44, 165, 0.6)', // Purple (primary)
      'rgba(46, 125, 201, 0.6)', // Blue
      'rgba(54, 162, 136, 0.6)', // Teal
      'rgba(120, 192, 77, 0.6)', // Green
      'rgba(220, 137, 34, 0.6)', // Orange
      'rgba(220, 77, 77, 0.6)'   // Red
    ];

    // Map visualization types from backend to chart.js types
    this.visualizationTypeMap = {
      'bar_chart': 'bar',
      'line_chart': 'line',
      'pie_chart': 'pie',
      'scatter_plot': 'scatter',
      'table': 'table',
      'area_chart': 'line', // We'll customize this to show area
      'horizontal_bar': 'horizontalBar',
      'stacked_bar': 'bar', // We'll customize this to be stacked
      'donut_chart': 'doughnut',
      'heatmap': 'matrix' // Updated for chartjs-chart-matrix plugin
    };
    
    this.currentRecommendation = null;
    this.currentTableData = null;
    this.currentQuestion = null;
    this.currentSQL = null;
  }

  /**
   * Main function to create a visualization from SQL results
   * Fetches recommendation from backend and renders the chart.
   */
  async createVisualization(container, tableData, question, sql) {
    console.log("[FE VIS] SQLVisualizer.createVisualization called. Container:", container, "TableData:", tableData, "Question:", question, "SQL:", sql);
    if (!container) {
      console.error("[FE VIS] No container provided for visualization.");
      return;
    }
    if (!tableData || !Array.isArray(tableData.columns) || !Array.isArray(tableData.rows)) {
        console.error("[FE VIS] Invalid or incomplete tableData for visualization (must have array for columns and rows):", tableData);
        container.innerHTML = '<p class="error-message">Cannot create visualization: Invalid data format.</p>';
        return;
    }

    // Clear previous content and show loading
    container.innerHTML = '<div class="loading">Analyzing data for visualization...</div>';

    try {
      // Store current context for chart switching
      this.currentTableData = tableData;
      this.currentQuestion = question;
      this.currentSQL = sql;

      console.log("[FE VIS] Fetching visualization recommendation with tableData:", tableData, "question:", question, "sql:", sql);
      let recommendation;
      try {
        recommendation = await this.getVisualizationRecommendation(tableData, question, sql);
        console.log("[FE VIS] Visualization recommendation RECEIVED:", recommendation);

        // Log data transformation hints if present
        if (recommendation.data_transformation) {
          console.log("Data Transformation Hints from Backend:", recommendation.data_transformation);
          if (recommendation.data_transformation.required) {
            console.warn("Backend suggests data transformation is required for optimal visualization: ", recommendation.data_transformation.instructions.join(', '));
            // TODO: Implement client-side data transformation based on these hints if feasible,
            // or ensure backend/LLM provides data in the most ready-to-plot format.
          }
        }

      } catch (error) {
        console.error("Error getting recommendation:", error);
        // Use fallback if API call fails
        recommendation = this.fallbackVisualizationRecommendation(tableData, question, sql);
      }

      // Replace loading indicator with visualization
      container.innerHTML = '';
      
      // Store the recommendation
      this.currentRecommendation = recommendation;

      this.renderChartWithRecommendation(container, tableData, question, recommendation);

    } catch (error) {
      console.error('Error creating visualization:', error);
      container.innerHTML = `<p class="error-message">Error creating visualization: ${error.message}</p>`;
    }
  }

  /**
   * Renders a chart based on a recommendation object.
   * Can be called by createVisualization or by the chart type switcher.
   */
  renderChartWithRecommendation(container, tableData, question, recommendation, existingTitleElement, existingSubtitleElement) {
      // Clear container *before* adding new elements, except if reusing title/subtitle
      if (!existingTitleElement) {
        container.innerHTML = ''; 
      }

      // Map the backend's visualization_type to our chart types if not already done
      if (recommendation.visualization_type && !recommendation.visualization && this.visualizationTypeMap[recommendation.visualization_type]) {
        recommendation.visualization = this.visualizationTypeMap[recommendation.visualization_type];
      } else if (!recommendation.visualization) {
        recommendation.visualization = this.visualizationTypeMap[recommendation.visualization_type] || 'bar';
      }
      
      // Check if visualization is recommended or not (e.g., table or none)
      if (recommendation.visualization === 'none' || recommendation.visualization_type === 'table') {
        this.createTableView(container, tableData); // This already calls addVisualizationControls
        return;
      }

      // Create container for the chart
      const chartContainer = document.createElement('div');
      chartContainer.className = 'chart-container';
      chartContainer.style.height = '400px';
      chartContainer.style.width = '100%';

      // Create canvas for the chart
      const canvas = document.createElement('canvas');
      chartContainer.appendChild(canvas);
      
      let titleElement = existingTitleElement;
      if (!titleElement) {
          titleElement = document.createElement('h3');
          titleElement.style.textAlign = 'center';
          titleElement.style.marginBottom = '5px';
          container.appendChild(titleElement); // Append to main container
      }
      titleElement.textContent = recommendation.config?.title || question || 'Data Visualization';
      
      if (existingSubtitleElement) {
          existingSubtitleElement.textContent = recommendation.config?.subtitle || '';
          if (!recommendation.config?.subtitle) existingSubtitleElement.style.display = 'none';
          else existingSubtitleElement.style.display = 'block';
      } else if (recommendation.config?.subtitle) {
        const subtitleElement = document.createElement('p');
        subtitleElement.style.textAlign = 'center';
        subtitleElement.style.marginBottom = '15px';
        subtitleElement.style.color = '#666';
        subtitleElement.textContent = recommendation.config.subtitle;
        container.insertBefore(subtitleElement, chartContainer); // Insert before chart container
      }
      
      // Insert chart container after title/subtitle
      if (existingTitleElement && existingTitleElement.nextSibling) {
          container.insertBefore(chartContainer, existingTitleElement.nextSibling);
      } else if (existingTitleElement) {
          container.appendChild(chartContainer);
      } else {
           // If no existing title, title was added first, now add chart.
          container.appendChild(chartContainer);
      }


      const ctx = canvas.getContext('2d');
      const chartConfig = this.prepareChartConfig(recommendation, tableData);

      switch (recommendation.visualization) {
        case 'bar':
          this.createBarChartWithConfig(ctx, tableData, chartConfig);
          break;
        case 'line':
          this.createLineChartWithConfig(ctx, tableData, chartConfig);
          break;
        case 'pie':
        case 'doughnut':
          this.createPieChartWithConfig(ctx, tableData, chartConfig, recommendation.visualization);
          break;
        case 'horizontalBar':
          this.createHorizontalBarChartWithConfig(ctx, tableData, chartConfig);
          break;
        case 'scatter':
          this.createScatterChartWithConfig(ctx, tableData, chartConfig);
          break;
        case 'matrix':
          this.createHeatmapChart(ctx, tableData, chartConfig);
          break;
        default:
          this.createBarChartWithConfig(ctx, tableData, chartConfig);
      }
      // Add controls AFTER rendering the chart. Pass the actual rendered type.
      this.addVisualizationControls(container, tableData, question, this.currentSQL, recommendation.visualization);
  }

  /**
   * Prepares chart configuration from recommendation
   */
  prepareChartConfig(recommendation, tableData) {
    const { columns } = tableData;
    const newVizType = recommendation.visualization_type; // e.g., 'bar_chart', 'line_chart'
    const oldConfig = recommendation.config || {}; // Config from original or previous recommendation

    let config = {
      title: oldConfig.title || null,
      subtitle: oldConfig.subtitle || null,
      showLegend: oldConfig.legend !== undefined ? oldConfig.legend : true,
      colors: oldConfig.colors || this.colors,
      isStacked: newVizType === 'stacked_bar',
      fill: newVizType === 'area_chart' // For area charts, set fill option to true
    };

    // Determine xColumn, yColumn, seriesColumn based on newVizType and oldConfig
    // Default column selections
    let defaultX = columns.length > 0 ? columns[0] : null;
    let defaultY = columns.length > 1 ? columns[1] : (columns.length > 0 ? columns[0] : null);
    let defaultSeries = null; 
    let defaultValueCol = columns.length > 2 ? columns[2] : (columns.length > 1 ? columns[1] : null);

    config.xColumn = oldConfig.x_axis || defaultX;
    config.yColumn = oldConfig.y_axis || defaultY;
    config.seriesColumn = oldConfig.series || defaultSeries;
    config.valueColumn = oldConfig.value_col || defaultValueCol; // For heatmap

    // Type-specific adjustments if switching chart types
    switch (newVizType) {
      case 'pie_chart':
      case 'donut_chart':
        // Pie/Donut typically use a category (xColumn) and a value (yColumn)
        config.xColumn = oldConfig.x_axis || defaultX; // Label for slices
        config.yColumn = oldConfig.y_axis || defaultY; // Value for slices
        config.seriesColumn = null; // No series for pie/donut
        break;
      case 'scatter_plot':
        // Scatter needs two numerical columns
        config.xColumn = oldConfig.x_axis || defaultX;
        config.yColumn = oldConfig.y_axis || defaultY;
        config.seriesColumn = oldConfig.series || null; // Optional series
        break;
      case 'heatmap':
        config.xColumn = oldConfig.x_axis || defaultX;
        config.yColumn = oldConfig.y_axis || defaultY;
        config.valueColumn = oldConfig.value_col || defaultValueCol;
        config.seriesColumn = null;
        break;
      case 'bar_chart':
      case 'line_chart':
      case 'area_chart':
      case 'horizontal_bar':
      case 'stacked_bar':
        config.xColumn = oldConfig.x_axis || defaultX;
        config.yColumn = oldConfig.y_axis || defaultY;
        config.seriesColumn = oldConfig.series || null;
        break;
      default: // Includes 'table' or unknown - rely on defaults or ensure they are not used by chart drawing methods
        config.xColumn = oldConfig.x_axis || defaultX;
        config.yColumn = oldConfig.y_axis || defaultY;
        config.seriesColumn = oldConfig.series || null;
        break;
    }

    // Final validation: ensure selected columns exist in tableData
    if (config.xColumn && !columns.includes(config.xColumn)) {
        console.warn(`Configured xColumn '${config.xColumn}' not found. Falling back to default.`);
        config.xColumn = defaultX;
    }
    if (config.yColumn && !columns.includes(config.yColumn)) {
        console.warn(`Configured yColumn '${config.yColumn}' not found. Falling back to default.`);
        config.yColumn = defaultY;
    }
    if (config.seriesColumn && !columns.includes(config.seriesColumn)) {
        console.warn(`Configured seriesColumn '${config.seriesColumn}' not found. Setting to null.`);
        config.seriesColumn = null;
    }
    if (config.valueColumn && !columns.includes(config.valueColumn)) {
        console.warn(`Configured valueColumn '${config.valueColumn}' not found. Falling back to default.`);
        config.valueColumn = defaultValueCol;
    }

    return config;
  }

  /**
   * Gets visualization recommendation from the backend with better debugging
   */
  async getVisualizationRecommendation(tableData, question, sql) {
    // Fallback to table if data is empty or only one row (unless it's a summary like kpi)
    // This logic might be better handled by the LLM based on query intent, but good as a basic client guard.
    if (!tableData || !tableData.rows || tableData.rows.length === 0) {
        console.warn("[FE VIS] getVisualizationRecommendation: No data results, falling back to table.");
        return this.fallbackVisualizationRecommendation(tableData, "No data to visualize.");
    }
    // if (tableData.results.length === 1 && tableData.columns.length > 2) { 
    // // Example: A single row with many stats might be better as table than a pie of one slice.
    // // This is a heuristic, real decision should be more nuanced.
    //     console.warn("[FE VIS] getVisualizationRecommendation: Single row with multiple columns, potentially falling back to table.");
    //     // return this.fallbackVisualizationRecommendation(tableData, "Single row data often best as table.");
    // }

    console.log("[FE VIS] Calling /api/visualization-recommendation with question:", question, "sql:", sql, "tableData:", tableData);
    const response = await fetch('/api/visualization-recommendation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        sqlQuery: sql,
        results: tableData
      })
    });

    // Debug: Log response status
    console.log("API response status:", response.status);

    if (!response.ok) {
      console.error("API returned error status:", response.status);
      const errorText = await response.text();
      console.error("Error details:", errorText);
      throw new Error(`Failed to get visualization recommendation: ${response.status} ${errorText}`);
    }

    const recommendationData = await response.json();

    // Debug: Log the raw recommendation
    console.log("Raw visualization recommendation:", recommendationData);

    // Validate the recommendation format
    if (!recommendationData || !recommendationData.visualization_type) {
      console.error("Invalid recommendation format", recommendationData);
      throw new Error("Invalid recommendation format returned by API");
    }

    return recommendationData;
  }

  /**
   * Fallback visualization recommendation if API call fails
   */
  fallbackVisualizationRecommendation(tableData, reason = "Failed to get recommendation or data unsuitable.") {
    console.warn(`[FE VIS] fallbackVisualizationRecommendation called. Reason: ${reason}. TableData:`, tableData);
    const columns = tableData && tableData.columns ? tableData.columns : [];
    const title = (tableData && tableData.rows && tableData.rows.length > 0) ? 
                  `Query Results (${tableData.rows.length} rows)` :
                  "No data to visualize.";

    // Check if we have multiple numeric columns
    const hasMultipleNumericColumns = this.hasMultipleNumericColumns(tableData);
    const analyzeResults = this.analyzeData(tableData);

    // Check if this is likely a descriptive result
    if (columns.length <= 2 && tableData.rows.length <= 1) {
      return {
        visualization_type: 'table',
        config: { title: title },
        reasoning: 'Direct display of data.' // Updated reason
      };
    }

    // For data with time-related first column, use line chart
    if (analyzeResults.hasDateColumn && tableData.rows && tableData.rows.length > 0) {
      return {
        visualization_type: 'line_chart',
        config: {
          x_axis: analyzeResults.dateColumn,
          y_axis: analyzeResults.numericColumns[0] || columns[1],
          title: "Trend Over Time"
        },
        reasoning: ''
      };
    }

    // For data with few categories and one numeric column, use pie chart
    if (tableData.rows.length <= 7 && analyzeResults.numericColumns.length === 1 && analyzeResults.categoricalColumns.length > 0) {
      return {
        visualization_type: 'pie_chart',
        config: {
          x_axis: analyzeResults.categoricalColumns[0],
          y_axis: analyzeResults.numericColumns[0],
          title: `Distribution by ${analyzeResults.categoricalColumns[0]}`
        },
        reasoning: ''
      };
    }

    // For data with many rows, use bar chart
    if (tableData.rows.length > 5) {
      // If many rows, use horizontal bar for better readability
      if (tableData.rows.length > 10) {
        return {
          visualization_type: 'horizontal_bar',
          config: {
            x_axis: columns[0],
            y_axis: analyzeResults.numericColumns[0] || columns[1],
            title: `Comparison by ${columns[0]}`
          },
          reasoning: ''
        };
      }

      return {
        visualization_type: 'bar_chart',
        config: {
          x_axis: columns[0],
          y_axis: analyzeResults.numericColumns[0] || columns[1],
          title: `Comparison by ${columns[0]}`
        },
        reasoning: ''
      };
    }

    // Default to bar chart for most cases
    return {
      visualization_type: 'bar_chart',
      config: {
        x_axis: columns[0],
        y_axis: columns.length > 1 ? columns[1] : columns[0],
        title: "Data Comparison"
      },
      reasoning: ''
    };
  }

  /**
   * Analyze the data for better visualization recommendations
   */
  analyzeData(tableData) {
    const { columns, rows } = tableData;
    const result = {
      numericColumns: [],
      categoricalColumns: [],
      dateColumn: null,
      hasDateColumn: false
    };

    // Check each column
    columns.forEach((col, colIndex) => {
      // Skip if no data
      if (!rows || rows.length === 0) return;

      // Sample values to determine column type
      const sampleValues = rows.slice(0, 5).map(row => row[colIndex]);

      // Check if date column
      const datePattern = /^\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}(\/\d{2,4})?|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i;
      const dateColumnHints = ['date', 'time', 'year', 'month', 'day'];

      const isDateColumn =
        dateColumnHints.some(hint => col.toLowerCase().includes(hint)) ||
        sampleValues.some(val => typeof val === 'string' && datePattern.test(val));

      if (isDateColumn) {
        result.hasDateColumn = true;
        result.dateColumn = col;
        return;
      }

      // Check if numeric column
      const isNumeric = sampleValues.every(val =>
        val !== null && val !== undefined && !isNaN(parseFloat(val)) && isFinite(val)
      );

      if (isNumeric) {
        result.numericColumns.push(col);
        return;
      }

      // Assume categorical otherwise
      result.categoricalColumns.push(col);
    });

    return result;
  }

  /**
   * Check if the dataset has multiple numeric columns
   */
  hasMultipleNumericColumns(tableData) {
    const { columns, rows } = tableData;

    if (!rows || rows.length === 0 || columns.length <= 2) {
      return false;
    }

    // Count numeric columns (skip first column which is usually labels)
    let numericColumnCount = 0;

    for (let i = 1; i < columns.length; i++) {
      // Check if at least half the values in the column are numeric
      const numericCount = rows.filter(row => !isNaN(parseFloat(row[i]))).length;
      if (numericCount >= rows.length / 2) {
        numericColumnCount++;
      }
    }

    return numericColumnCount > 1;
  }

  /**
   * Creates a bar chart with specific configuration
   */
  createBarChartWithConfig(ctx, tableData, config) {
    const { columns, rows } = tableData;

    // Find column indices
    const xColumnIndex = columns.indexOf(config.xColumn);
    const yColumnIndex = columns.indexOf(config.yColumn);
    const seriesColumnIndex = config.seriesColumn ? columns.indexOf(config.seriesColumn) : -1;

    // Default to first and second columns if not found
    const xIndex = xColumnIndex !== -1 ? xColumnIndex : 0;
    const yIndex = yColumnIndex !== -1 ? yColumnIndex : 1;

    // Check if we need to create a multi-series chart
    if (seriesColumnIndex !== -1) {
      // Get unique values for series
      const seriesValues = [...new Set(rows.map(row => row[seriesColumnIndex]))];

      // Create a dataset for each series value
      const datasets = seriesValues.map((seriesValue, i) => {
        // Filter rows for this series
        const seriesRows = rows.filter(row => row[seriesColumnIndex] === seriesValue);

        // Create dataset
        return {
          label: String(seriesValue),
          data: seriesRows.map(row => parseFloat(row[yIndex]) || 0),
          backgroundColor: config.colors[i % config.colors.length],
          borderColor: config.colors[i % config.colors.length].replace('0.6', '0.8'),
          borderWidth: 1,
          // If stacked, include stack property
          ...(config.isStacked ? { stack: 'stack1' } : {})
        };
      });

      // Create the chart
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: [...new Set(rows.map(row => row[xIndex]))], // Get unique x values
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: columns[xIndex]
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: columns[yIndex]
              },
              stacked: config.isStacked
            }
          }
        }
      });
    } else {
      // Simple bar chart
      const data = rows.map(row => parseFloat(row[yIndex]) || 0);
      const labels = rows.map(row => row[xIndex]);

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: columns[yIndex],
            data: data,
            backgroundColor: config.colors[0],
            borderColor: config.colors[0].replace('0.6', '0.8'),
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: columns[xIndex]
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: columns[yIndex]
              }
            }
          }
        }
      });
    }
  }

  /**
   * Creates a line chart with specific configuration
   */
  createLineChartWithConfig(ctx, tableData, config) {
    const { columns, rows } = tableData;

    // Find column indices
    const xColumnIndex = columns.indexOf(config.xColumn);
    const yColumnIndex = columns.indexOf(config.yColumn);
    const seriesColumnIndex = config.seriesColumn ? columns.indexOf(config.seriesColumn) : -1;

    // Default to first and second columns if not found
    const xIndex = xColumnIndex !== -1 ? xColumnIndex : 0;
    const yIndex = yColumnIndex !== -1 ? yColumnIndex : 1;

    // Check if we need to create a multi-series chart
    if (seriesColumnIndex !== -1) {
      // Get unique values for series
      const seriesValues = [...new Set(rows.map(row => row[seriesColumnIndex]))];

      // Create a dataset for each series value
      const datasets = seriesValues.map((seriesValue, i) => {
        // Filter rows for this series
        const seriesRows = rows.filter(row => row[seriesColumnIndex] === seriesValue);

        // Sort by x value if it's a date for proper line plotting
        const sortedRows = [...seriesRows].sort((a, b) => {
          const aVal = a[xIndex];
          const bVal = b[xIndex];
          // Try to parse as dates if possible
          const aDate = new Date(aVal);
          const bDate = new Date(bVal);
          if (!isNaN(aDate) && !isNaN(bDate)) {
            return aDate - bDate;
          }
          // Otherwise just compare values
          return String(aVal).localeCompare(String(bVal));
        });

        // Create dataset
        return {
          label: String(seriesValue),
          data: sortedRows.map(row => parseFloat(row[yIndex]) || 0),
          borderColor: config.colors[i % config.colors.length].replace('0.6', '0.8'),
          backgroundColor: config.fill ? config.colors[i % config.colors.length] : 'transparent',
          borderWidth: 2,
          tension: 0.1,
          fill: config.fill || false
        };
      });

      // Create the chart
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: [...new Set(rows.map(row => row[xIndex]))].sort((a, b) => {
            // Sort labels if they're dates
            const aDate = new Date(a);
            const bDate = new Date(b);
            if (!isNaN(aDate) && !isNaN(bDate)) {
              return aDate - bDate;
            }
            return String(a).localeCompare(String(b));
          }),
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: columns[xIndex]
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: columns[yIndex]
              }
            }
          }
        }
      });
    } else {
      // Simple line chart
      // Sort rows by x value for proper line plotting
      const sortedRows = [...rows].sort((a, b) => {
        const aVal = a[xIndex];
        const bVal = b[xIndex];
        // Try to parse as dates if possible
        const aDate = new Date(aVal);
        const bDate = new Date(bVal);
        if (!isNaN(aDate) && !isNaN(bDate)) {
          return aDate - bDate;
        }
        // Otherwise just compare values
        return String(aVal).localeCompare(String(bVal));
      });

      const data = sortedRows.map(row => parseFloat(row[yIndex]) || 0);
      const labels = sortedRows.map(row => row[xIndex]);

      new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: columns[yIndex],
            data: data,
            borderColor: config.colors[0].replace('0.6', '0.8'),
            backgroundColor: config.fill ? config.colors[0] : 'transparent',
            borderWidth: 2,
            tension: 0.1,
            fill: config.fill || false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: columns[xIndex]
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: columns[yIndex]
              }
            }
          }
        }
      });
    }
  }

  /**
   * Creates a horizontal bar chart with specific configuration
   */
  createHorizontalBarChartWithConfig(ctx, tableData, config) {
    const { columns, rows } = tableData;

    // Find column indices
    const xColumnIndex = columns.indexOf(config.xColumn);
    const yColumnIndex = columns.indexOf(config.yColumn);
    const seriesColumnIndex = config.seriesColumn ? columns.indexOf(config.seriesColumn) : -1;

    // Default to first and second columns if not found
    const xIndex = xColumnIndex !== -1 ? xColumnIndex : 0;
    const yIndex = yColumnIndex !== -1 ? yColumnIndex : 1;

    // Check if we need to create a multi-series chart
    if (seriesColumnIndex !== -1) {
      // Get unique values for series
      const seriesValues = [...new Set(rows.map(row => row[seriesColumnIndex]))];

      // Create a dataset for each series value
      const datasets = seriesValues.map((seriesValue, i) => {
        // Filter rows for this series
        const seriesRows = rows.filter(row => row[seriesColumnIndex] === seriesValue);

        // Create dataset
        return {
          label: String(seriesValue),
          data: seriesRows.map(row => parseFloat(row[xIndex]) || 0),
          backgroundColor: config.colors[i % config.colors.length],
          borderColor: config.colors[i % config.colors.length].replace('0.6', '0.8'),
          borderWidth: 1,
          // If stacked, include stack property
          ...(config.isStacked ? { stack: 'stack1' } : {})
        };
      });

      // Create the chart
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: [...new Set(rows.map(row => String(row[yIndex])))],
          datasets: datasets
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              title: {
                display: true,
                text: config.xColumn
              },
              stacked: config.isStacked
            },
            y: {
              title: {
                display: true,
                text: config.yColumn
              },
              stacked: config.isStacked
            }
          }
        }
      });
    } else {
      // Simple horizontal bar chart
      const data = rows.map(row => parseFloat(row[xIndex]) || 0);
      const labels = rows.map(row => String(row[yIndex]));

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: config.xColumn || columns[xIndex],
            data: data,
            backgroundColor: config.colors[0],
            borderColor: config.colors[0].replace('0.6', '0.8'),
            borderWidth: 1
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              title: {
                display: true,
                text: config.xColumn
              }
            },
            y: {
              title: {
                display: true,
                text: config.yColumn
              }
            }
          }
        }
      });
    }
  }

  /**
   * Creates a pie or doughnut chart with specific configuration
   */
  createPieChartWithConfig(ctx, tableData, config, chartType = 'pie') {
    const { columns, rows } = tableData;

    // Find column indices
    const labelColumnIndex = columns.indexOf(config.xColumn);
    const valueColumnIndex = columns.indexOf(config.yColumn);

    // Default to first and second columns if not found
    const labelIndex = labelColumnIndex !== -1 ? labelColumnIndex : 0;
    const valueIndex = valueColumnIndex !== -1 ? valueColumnIndex : 1;

    // Prepare data
    const labels = rows.map(row => row[labelIndex]);
    const data = rows.map(row => parseFloat(row[valueIndex]) || 0);

    // Calculate total for percentage
    const total = data.reduce((sum, value) => sum + value, 0);

    // Create the chart
    new Chart(ctx, {
      type: chartType, // 'pie' or 'doughnut'
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: config.colors
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: false,
            text: ''
          },
          subtitle: {
            display: false,
            text: ''
          },
          legend: {
            position: 'right',
            display: config.showLegend
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const value = context.raw;
                const percentage = Math.round((value / total) * 100);
                return `${context.label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  }

  /**
   * Creates a scatter chart with specific configuration
   */
  createScatterChartWithConfig(ctx, tableData, config) {
    const { columns, rows } = tableData;

    // Find column indices
    const xColumnIndex = columns.indexOf(config.xColumn);
    const yColumnIndex = columns.indexOf(config.yColumn);
    const seriesColumnIndex = config.seriesColumn ? columns.indexOf(config.seriesColumn) : -1;

    // Default to first and second columns if not found
    const xIndex = xColumnIndex !== -1 ? xColumnIndex : 0;
    const yIndex = yColumnIndex !== -1 ? yColumnIndex : 1;

    // Check if we need to create a multi-series chart
    if (seriesColumnIndex !== -1) {
      // Get unique values for series
      const seriesValues = [...new Set(rows.map(row => row[seriesColumnIndex]))];

      // Create a dataset for each series value
      const datasets = seriesValues.map((seriesValue, i) => {
        // Filter rows for this series
        const seriesRows = rows.filter(row => row[seriesColumnIndex] === seriesValue)
        // Create data points
        const data = seriesRows.map(row => ({
          x: parseFloat(row[xIndex]) || 0,
          y: parseFloat(row[yIndex]) || 0
        }));

        return {
          label: String(seriesValue),
          data: data,
          backgroundColor: config.colors[i % config.colors.length],
          borderColor: config.colors[i % config.colors.length].replace('0.6', '0.8'),
          pointRadius: 5,
          pointHoverRadius: 7
        };
      });

      // Create the chart
      new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend,
              position: 'top'
            },
            tooltip: {
              mode: 'nearest',
              intersect: true
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: columns[xIndex]
              }
            },
            y: {
              title: {
                display: true,
                text: columns[yIndex]
              }
            }
          }
        }
      });
    } else {
      // Simple scatter chart
      const data = rows.map(row => ({
        x: parseFloat(row[xIndex]) || 0,
        y: parseFloat(row[yIndex]) || 0
      }));

      new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: `${columns[xIndex]} vs ${columns[yIndex]}`,
            data: data,
            backgroundColor: config.colors[0],
            borderColor: config.colors[0].replace('0.6', '0.8'),
            pointRadius: 5,
            pointHoverRadius: 7
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: false,
              text: ''
            },
            subtitle: {
              display: false,
              text: ''
            },
            legend: {
              display: config.showLegend
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: columns[xIndex]
              }
            },
            y: {
              title: {
                display: true,
                text: columns[yIndex]
              }
            }
          }
        }
      });
    }
  }

  /**
   * Adds controls for different chart types and download
   */
  addVisualizationControls(container, tableData, question, sql, currentType) {
    const controlsContainer = document.createElement('div');
    controlsContainer.className = 'visualization-controls';
    controlsContainer.style.display = 'flex';
    controlsContainer.style.justifyContent = 'flex-end';
    controlsContainer.style.alignItems = 'center';
    controlsContainer.style.gap = '10px';
    controlsContainer.style.marginTop = '10px'; // Add some margin

    // Define compatible chart types (can be expanded)
    const compatibleTypes = {
      bar: ['bar', 'line', 'horizontalBar', 'table'],
      line: ['line', 'bar', 'area', 'table'], // area is line with fill
      pie: ['pie', 'doughnut', 'table'],
      doughnut: ['doughnut', 'pie', 'table'],
      scatter: ['scatter', 'table'],
      horizontalBar: ['horizontalBar', 'bar', 'table'],
      matrix: ['matrix', 'table'] // Heatmap
    };

    const currentMappedType = Object.keys(this.visualizationTypeMap).find(key => this.visualizationTypeMap[key] === currentType) || currentType;

    const availableTypes = compatibleTypes[currentType] || ['table'];

    // Chart type switcher (dropdown)
    if (availableTypes.length > 1) {
      const selectLabel = document.createElement('span');
      selectLabel.textContent = 'Change chart: ';
      selectLabel.style.fontSize = '0.9em';
      selectLabel.style.color = '#555';

      const select = document.createElement('select');
      select.className = 'chart-type-select';
      select.style.padding = '5px';
      select.style.border = '1px solid #ccc';
      select.style.borderRadius = '4px';
      select.style.fontSize = '0.9em';

      availableTypes.forEach(typeKey => {
        // Find the original backend type name for the label if possible
        const backendType = Object.keys(this.visualizationTypeMap).find(bt => this.visualizationTypeMap[bt] === typeKey) || typeKey;
        const option = document.createElement('option');
        option.value = typeKey;
        option.textContent = this.getChartTypeLabel(typeKey); // Use original type for display name
        if (typeKey === currentType) {
          option.selected = true;
        }
        select.appendChild(option);
      });

      select.onchange = (event) => {
        const newType = event.target.value;
        // Re-render the visualization with the new type
        // We need to get the original recommendation structure or adapt it
        const newRecommendation = {
            visualization_type: Object.keys(this.visualizationTypeMap).find(key => this.visualizationTypeMap[key] === newType) || newType,
            visualization: newType, // Chart.js type
            config: this.prepareChartConfig({ // Prepare config based on new type
                visualization_type: Object.keys(this.visualizationTypeMap).find(key => this.visualizationTypeMap[key] === newType) || newType,
                config: this.currentRecommendation?.config || {} // Reuse existing config details if possible
            }, tableData),
            reasoning: 'User selected chart type'
        };
        
        // Clear the specific chart area (not the whole message bubble)
        const chartArea = container.querySelector('.chart-container');
        if (chartArea) chartArea.remove();
        const existingControls = container.querySelector('.visualization-controls');
        if (existingControls) existingControls.remove();
        const existingTitle = container.querySelector('h3');
        const existingSubtitle = container.querySelector('p');

        this.renderChartWithRecommendation(container, tableData, question, newRecommendation, existingTitle, existingSubtitle);
      };
      controlsContainer.appendChild(selectLabel);
      controlsContainer.appendChild(select);
    }

    // Add CSV download button
    const downloadBtn = document.createElement('button');
    downloadBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px;">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>Download CSV`;
    downloadBtn.className = 'download-button'; // Use existing styles from index.html if desired
    downloadBtn.style.padding = '6px 10px';
    downloadBtn.style.fontSize = '0.9em';
    downloadBtn.style.backgroundColor = '#6c757d'; // A neutral color
    downloadBtn.style.color = 'white';
    downloadBtn.style.border = 'none';
    downloadBtn.style.borderRadius = '4px';
    downloadBtn.style.cursor = 'pointer';
    
    downloadBtn.onclick = () => {
      if (typeof downloadCSV === 'function') {
        const title = this.currentRecommendation?.config?.title || this.currentQuestion || 'query_results';
        downloadCSV(tableData, title); // Call the global downloadCSV function from index.html
      } else {
        console.error('downloadCSV function not found.');
        alert('Failed to initiate download.');
      }
    };

    controlsContainer.appendChild(downloadBtn);

    // Add PNG Export button (only if not a table)
    if (currentType !== 'table') {
      const exportPngBtn = document.createElement('button');
      exportPngBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px;">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path> {/* Using a generic image/attachment icon for PNG */}
        </svg>Export PNG`;
      exportPngBtn.className = 'export-png-button'; // For styling
      exportPngBtn.style.padding = '6px 10px';
      exportPngBtn.style.fontSize = '0.9em';
      exportPngBtn.style.backgroundColor = '#007bff'; // Blue
      exportPngBtn.style.color = 'white';
      exportPngBtn.style.border = 'none';
      exportPngBtn.style.borderRadius = '4px';
      exportPngBtn.style.cursor = 'pointer';

      exportPngBtn.onclick = () => {
        const chartCanvas = container.querySelector('.chart-container canvas');
        if (chartCanvas) {
          try {
            const dataURL = chartCanvas.toDataURL('image/png');
            const link = document.createElement('a');
            const title = this.currentRecommendation?.config?.title || this.currentQuestion || 'chart';
            const filename = title.toLowerCase().replace(/[^a-z0-9]+/g, '_').substring(0, 30) + '.png';
            link.download = filename;
            link.href = dataURL;
            document.body.appendChild(link); // Required for Firefox
            link.click();
            document.body.removeChild(link);
            if (typeof showStatusMessage === 'function') {
                showStatusMessage('Chart exported as PNG.');
            }
          } catch (e) {
            console.error("Error exporting chart to PNG:", e);
            alert("Failed to export chart as PNG. The chart might be too complex or an error occurred.");
          }
        } else {
          console.error('Chart canvas not found for PNG export.');
          alert('Could not find the chart to export.');
        }
      };
      controlsContainer.appendChild(exportPngBtn);
    }

    // Append controls to the main chart container (passed as 'container' to this function)
    // Ensure it's added only once if the container is being reused.
    const existingControls = container.querySelector('.visualization-controls');
    if (existingControls) existingControls.remove(); // Remove old controls if re-rendering
    container.appendChild(controlsContainer);
  }

  /**
   * Returns a user-friendly label for chart types
   */
  getChartTypeLabel(type) {
    switch(type) {
      case 'bar': return '📊 Bar Chart';
      case 'line': return '📈 Line Chart';
      case 'pie': return '🥧 Pie Chart';
      case 'doughnut': return '🍩 Donut Chart';
      case 'horizontalBar': return '📊 Horizontal Bar';
      case 'scatter': return '📍 Scatter Plot';
      case 'table': return '📋 Table View';
      default: return type;
    }
  }

  /**
   * Creates a table view when no chart is appropriate
   */
  createTableView(container, tableData) {
    // Clear the container
    container.innerHTML = '';

    // Add title if not rendering as part of a chart switch
    if (!container.querySelector('h3')) {
        const titleElement = document.createElement('h3');
        titleElement.style.textAlign = 'center';
        titleElement.style.marginBottom = '5px';
        // Try to get title from current recommendation or fallback
        const titleText = (this.currentRecommendation && this.currentRecommendation.config && this.currentRecommendation.config.title) 
                        ? this.currentRecommendation.config.title 
                        : (this.currentQuestion || (tableData && tableData.rows && tableData.rows.length > 0 ? `Table View (${tableData.rows.length} rows)`: 'Table View'));
        titleElement.textContent = titleText;
        container.appendChild(titleElement);
    }

    // Create table element
    const table = document.createElement('table');
    table.className = 'data-table';

    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    tableData.columns.forEach(column => {
      const th = document.createElement('th');
      th.textContent = column;
      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');

    tableData.rows.forEach(row => {
      const tr = document.createElement('tr');

      row.forEach(cell => {
        const td = document.createElement('td');
        td.textContent = cell;
        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);

    // Add download control and chart switcher for table view too
    this.addVisualizationControls(container, tableData, this.currentQuestion || '', this.currentSQL || '', 'table');
  }

  /**
   * Creates a Heatmap chart using chartjs-chart-matrix plugin.
   * Assumes data might need to be pivoted or transformed if not already in x, y, v format.
   * The backend recommendation should specify x_axis, y_axis, and value_col.
   */
  createHeatmapChart(ctx, tableData, config) {
    const { columns, rows } = tableData;
    const { xColumn, yColumn, valueColumn, title, colors } = config;

    // Validate required columns
    if (!xColumn || !yColumn || !valueColumn) {
      console.error('Heatmap requires xColumn, yColumn, and valueColumn in config.');
      this.createTableView(ctx.canvas.parentElement.parentElement, tableData); // Fallback to table
      return;
    }

    const xIndex = columns.indexOf(xColumn);
    const yIndex = columns.indexOf(yColumn);
    const valueIndex = columns.indexOf(valueColumn);

    if (xIndex === -1 || yIndex === -1 || valueIndex === -1) {
      console.error('One or more specified columns for heatmap not found in data.');
      this.createTableView(ctx.canvas.parentElement.parentElement, tableData); // Fallback to table
      return;
    }

    // Transform data to {x, y, v} format
    const chartData = rows.map(row => ({
      x: row[xIndex],
      y: row[yIndex],
      v: parseFloat(row[valueIndex]) || 0 // Ensure value is numeric
    }));

    // Determine unique x and y labels for the axes
    const xLabels = [...new Set(rows.map(row => row[xIndex]))].sort();
    const yLabels = [...new Set(rows.map(row => row[yIndex]))].sort();

    // Get min/max values for color scaling (optional, plugin might handle this)
    const values = chartData.map(d => d.v);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);

    new Chart(ctx, {
      type: 'matrix',
      data: {
        datasets: [{
          label: title || 'Heatmap',
          data: chartData,
          backgroundColor: (context) => {
            if (!context.raw) return 'rgba(0,0,0,0.1)'; // Handle null/undefined data points
            const value = context.raw.v;
            const alpha = (value - minValue) / (maxValue - minValue) || 0;
            // Use a color from the predefined list, or a gradient
            // Simple example: interpolate between two colors from the theme
            const color1 = this.colors[0] ? this.colors[0].replace(", 0.6", ", ") : 'rgba(94, 44, 165, '; // Primary purple
            const color2 = this.colors[4] ? this.colors[4].replace(", 0.6", ", ") : 'rgba(220, 137, 34, '; // Orange
            // This is a very basic interpolation. For better results, use a proper color scale library.
            const r = Math.floor(parseInt(color1.slice(5, color1.indexOf(','))) * (1 - alpha) + parseInt(color2.slice(5, color2.indexOf(','))) * alpha);
            const g = Math.floor(parseInt(color1.slice(color1.indexOf(',') + 1, color1.lastIndexOf(','))) * (1 - alpha) + parseInt(color2.slice(color2.indexOf(',') + 1, color2.lastIndexOf(','))) * alpha);
            const b = Math.floor(parseInt(color1.slice(color1.lastIndexOf(',') + 1, -1)) * (1 - alpha) + parseInt(color2.slice(color2.lastIndexOf(',') + 1, -1)) * alpha);
            return `rgba(${r}, ${g}, ${b}, 0.8)`;
          },
          borderColor: 'rgba(200, 200, 200, 0.5)',
          borderWidth: 1,
          width: (c) => (c.chart.chartArea || {}).width / xLabels.length - 1,
          height: (c) => (c.chart.chartArea || {}).height / yLabels.length - 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
          },
          tooltip: {
            callbacks: {
              title: function() { return '' }, // No title for tooltip
              label: function(context) {
                const item = context.raw;
                return `${xColumn}: ${item.x}, ${yColumn}: ${item.y}, Value: ${item.v.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'category',
            labels: xLabels,
            ticks: {
              autoSkip: false,
              maxRotation: 90,
              minRotation: 45
            },
            grid: { display: false }
          },
          y: {
            type: 'category',
            labels: yLabels,
            offset: true,
            ticks: { autoSkip: false }, 
            grid: { display: false }
          }
        }
      }
    });
  }
}