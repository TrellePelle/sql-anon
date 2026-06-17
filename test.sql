SELECT k.kundnamn, SUM(o.belopp) AS total
FROM kund k
JOIN ordrar o ON o.kund_id = k.id
WHERE o.datum >= '2025-01-01'
GROUP BY k.kundnamn
ORDER BY total DESC
