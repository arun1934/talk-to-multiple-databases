/**
 * Analyzes column types based on data values
 */
function analyzeColumnTypes(columns, rows) {
  return columns.map((col, colIndex) => {
    const sampleSize = 20; // Increase sample size for better accuracy
    const sampleValues = rows
      .map(row => row[colIndex])
      .filter(val => val !== null && val !== undefined && val !== '')
      .slice(0, sampleSize);

    if (sampleValues.length === 0) {
      return { name: col, type: 'unknown' };
    }

    // Check for date/time more robustly
    let dateCount = 0;
    const dateHintKeywords = ['date', 'time', 'year', 'month', 'period', 'quarter'];
    const hasDateKeywordInName = dateHintKeywords.some(hint => col.toLowerCase().includes(hint));

    sampleValues.forEach(val => {
      if (val instanceof Date) {
        dateCount++;
        return;
      }
      if (typeof val === 'string') {
        // Try direct parsing first
        if (!isNaN(new Date(val).getTime())) {
            // Further check to avoid misinterpreting numbers as dates e.g. "2023" as a date
            if (String(val).match(/^\d{4}$/) && !hasDateKeywordInName) { // if it's just a 4-digit number and no date keyword in name
                // Don't count as date unless column name suggests it
            } else if (String(val).match(/^\d{1,2}$/) && !hasDateKeywordInName) { // or just a 1-2 digit number
                // Don't count as date
            } else {
                 dateCount++;
                 return;
            }
        }
        // Check common date-like patterns (simplified, for full robustness use a library like date-fns on client if needed)
        const datePatterns = [
          /^\d{4}-\d{1,2}-\d{1,2}(T|\s|$)/, // YYYY-MM-DD
          /^\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}/, // MM/DD/YYYY or MM-DD-YY
          /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Q[1-4])[a-z]*\s*\d{1,2}(st|nd|rd|th)?([,-]?\s*\d{2,4})?/i, // Jan 1st, 2023 or Q1 2023
          /^\d{4}$/ // Year only, give less weight unless col name has date keyword
        ];
        if (datePatterns.some(pattern => pattern.test(val))) {
            if (String(val).match(/^\d{4}$/) && !hasDateKeywordInName) dateCount += 0.5; // Partial if just year and no name hint
            else dateCount++;
        }
      } else if (typeof val === 'number' && String(val).length === 4 && val >= 1900 && val <= 2100 && hasDateKeywordInName) {
          dateCount += 0.8; // Strong hint if it's a 4-digit number in date range AND col name suggests date
      }
    });

    if ((dateCount / sampleValues.length) >= 0.6) { // 60% threshold for dates
      return { name: col, type: 'datetime' }; // Use 'datetime' to match backend
    }

    // Check if numerical (integer or float)
    let numCount = 0;
    let floatHint = 0;
    sampleValues.forEach(val => {
        if (typeof val === 'number') {
            numCount++;
            if (val % 1 !== 0) floatHint++;
        } else if (typeof val === 'string') {
            const parsed = parseFloat(val.replace(/,/g, '')); // Handle numbers with commas
            if (!isNaN(parsed) && isFinite(parsed)) {
                numCount++;
                if (val.includes('.') || val.toLowerCase().includes('e')) floatHint++;
            }
        }
    });

    if ((numCount / sampleValues.length) >= 0.7) { // 70% threshold for numbers
      return { name: col, type: (floatHint > numCount * 0.2) ? 'float' : 'integer' }; // More than 20% float evidence -> float
    }

    // Check if categorical
    const uniqueValues = new Set(sampleValues);
    const isFewUniques = uniqueValues.size <= 20 || uniqueValues.size <= rows.length * 0.2;
    const categoryNameHints = ['category', 'type', 'status', 'region', 'country', 'state', 'city', 'department'];
    const nameSuggestsCategorical = categoryNameHints.some(hint =>
      col.toLowerCase().includes(hint)
    );

    if (isFewUniques || nameSuggestsCategorical) {
      return { name: col, type: 'categorical' };
    }

    // Default to text (string)
    return { name: col, type: 'string' }; // Use 'string' to match backend
  });
}

/**
 * Determines the best chart type based on data analysis
 */
function selectChartType(tableData, question, sql) {
  // Extract key information
  const { columns, rows } = tableData;
  if (!columns || !rows || columns.length === 0 || rows.length === 0) {
    return null; // No data to visualize
  }

  // Analyze column types
  const columnTypes = analyzeColumnTypes(columns, rows);

  // Analyze question intent
  const intent = analyzeQuestionIntent(question, sql);

  // Check for time series data
  const timeColumns = columnTypes.filter(c => c.type === 'date' || c.type === 'datetime');
  const hasTimeColumn = timeColumns.length > 0;

  // Check for categorical data
  const categoricalColumns = columnTypes.filter(c => c.type === 'categorical');
  const hasCategoricalColumn = categoricalColumns.length > 0;

  // Check for numerical data
  const numericalColumns = columnTypes.filter(c => c.type === 'numerical');
  const hasNumericalColumn = numericalColumns.length > 0;

  // Time series chart
  if (hasTimeColumn && hasNumericalColumn && (intent.includes('trend') || intent.includes('over time'))) {
    return {
      type: 'line',
      config: {
        xColumn: timeColumns[0].name,
        yColumns: numericalColumns.map(c => c.name).slice(0, 3), // Limit to 3 metrics for readability
        options: {
          title: `${numericalColumns[0].name} Over Time`,
          xAxisTitle: timeColumns[0].name,
          yAxisTitle: numericalColumns[0].name
        }
      }
    };
  }

  // Rest of chart type selection logic...
  // (simplified for brevity)

  // Default to bar chart if no specific pattern is detected
  if (hasNumericalColumn) {
    const xColumn = hasCategoricalColumn ?
      categoricalColumns[0].name :
      (hasTimeColumn ? timeColumns[0].name : columns[0]);

    return {
      type: 'bar',
      config: {
        xColumn: xColumn,
        yColumns: [numericalColumns[0].name],
        options: {
          title: `${numericalColumns[0].name} by ${xColumn}`,
          xAxisTitle: xColumn,
          yAxisTitle: numericalColumns[0].name
        }
      }
    };
  }

  // Table-only view if no good visualization is possible
  return null;
}

/**
 * Analyzes the intent of the question
 */
function analyzeQuestionIntent(question, sql) {
  const lowerQuestion = question.toLowerCase();
  const lowerSql = sql.toLowerCase();

  const intentMarkers = [
    { keywords: ['trend', 'over time', 'growth', 'increase', 'decrease'], intent: 'trend' },
    { keywords: ['compare', 'comparison', 'versus', 'vs'], intent: 'compare' },
    { keywords: ['distribution', 'breakdown', 'spread'], intent: 'distribution' },
    { keywords: ['percentage', 'proportion', 'share', 'ratio'], intent: 'percentage' },
    { keywords: ['composition', 'makeup', 'constituent'], intent: 'composition' },
    { keywords: ['correlation', 'relationship', 'between'], intent: 'correlation' },
    { keywords: ['top', 'bottom', 'highest', 'lowest', 'best', 'worst'], intent: 'ranking' }
  ];

  // Check question and SQL for intent markers
  const detectedIntents = intentMarkers
    .filter(marker =>
      marker.keywords.some(keyword =>
        lowerQuestion.includes(keyword) || lowerSql.includes(keyword)
      )
    )
    .map(marker => marker.intent);

  return detectedIntents;
}

/**
 * Extract a title from the question
 */
function extractChartTitle(question) {
  // Remove question marks and common question starters
  let title = question.replace(/\?/g, '');
  const starters = ['what is', 'show me', 'can you show', 'how many', 'display', 'graph'];

  starters.forEach(starter => {
    if (title.toLowerCase().startsWith(starter)) {
      title = title.substring(starter.length).trim();
    }
  });

  // Capitalize first letter
  title = title.charAt(0).toUpperCase() + title.slice(1);

  // Limit length
  if (title.length > 50) {
    title = title.substring(0, 47) + '...';
  }

  return title;
}