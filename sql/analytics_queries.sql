-- Last 7-day request volume, closure and open count
SELECT
    DATE(created_date) AS request_date,
    COUNT(*) AS total_requests,
    COUNT(CASE WHEN status = 'Closed' THEN 1 END) AS closed_requests,
    COUNT(CASE WHEN status != 'Closed' THEN 1 END) AS open_requests
FROM service_requests
GROUP BY DATE(created_date)
ORDER BY request_date DESC
LIMIT 7;

-- Top complaint types in the latest day loaded
SELECT complaint_type, COUNT(*) AS count
FROM service_requests
WHERE DATE(created_date) = (
    SELECT DATE(MAX(created_date)) FROM service_requests
)
GROUP BY complaint_type
ORDER BY count DESC
LIMIT 10;

-- Borough request trends over last 7 days
SELECT
    DATE(created_date) AS request_date,
    borough,
    COUNT(*) AS count
FROM service_requests
WHERE borough IS NOT NULL
  AND DATE(created_date) >= DATE(
        (SELECT MAX(created_date) FROM service_requests), '-6 days'
      )
GROUP BY DATE(created_date), borough
ORDER BY request_date ASC;

-- Open vs Closed over last 7 days
SELECT
    DATE(created_date) AS request_date,
    status,
    COUNT(*) AS count
FROM service_requests
WHERE DATE(created_date) >= DATE(
        (SELECT MAX(created_date) FROM service_requests), '-6 days'
      )
GROUP BY DATE(created_date), status
ORDER BY request_date ASC;

-- Top responding agencies for most recent day
SELECT agency_name, COUNT(*) AS count
FROM service_requests
WHERE DATE(created_date) = (
    SELECT DATE(MAX(created_date)) FROM service_requests
)
  AND agency_name IS NOT NULL
GROUP BY agency_name
ORDER BY count DESC
LIMIT 10;
