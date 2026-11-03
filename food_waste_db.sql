USE food_waste_db;

-- =====================================
-- Q1: How many food providers are there in each city?
-- =====================================
SELECT city, COUNT(*) AS total_providers
FROM providers_data
GROUP BY city;

-- =====================================
-- Q1: How many food receivers are there in each city?
-- =====================================
SELECT city, COUNT(*) AS total_receivers
FROM receivers_data
GROUP BY city;

-- =====================================
-- Q2: Which type of food provider contributes the most food?
-- =====================================
SELECT provider_type, SUM(quantity) AS total_food
FROM food_listings_data
GROUP BY provider_type
ORDER BY total_food DESC;

-- =====================================
-- Q3: Contact information of food providers in a specific city
-- =====================================
SELECT name, contact, city
FROM providers_data
WHERE city = 'Delhi';   -- change city if needed

-- =====================================
-- Q4: Which receivers have claimed the most food?
-- =====================================
SELECT r.name, COUNT(c.claim_id) AS total_claims
FROM claims_data c
JOIN receivers_data r ON c.receiver_id = r.receiver_id
GROUP BY r.name
ORDER BY total_claims DESC;

-- =====================================
-- Q5: Total quantity of food available
-- =====================================
SELECT SUM(quantity) AS total_food_available
FROM food_listings_data;

-- =====================================
-- Q6: Which city has highest number of food listings?
-- =====================================
SELECT location, COUNT(*) AS total_listings
FROM food_listings_data
GROUP BY location
ORDER BY total_listings DESC;

-- =====================================
-- Q7: Most commonly available food types
-- =====================================
SELECT food_type, COUNT(*) AS total_count
FROM food_listings_data
GROUP BY food_type
ORDER BY total_count DESC;

-- =====================================
-- Q8: Number of claims per food item
-- =====================================
SELECT food_id, COUNT(*) AS total_claims
FROM claims_data
GROUP BY food_id;

-- =====================================
-- Q9: Provider with highest successful claims
-- =====================================
SELECT p.name, COUNT(*) AS successful_claims
FROM claims_data c
JOIN food_listings_data f ON c.food_id = f.food_id
JOIN providers_data p ON f.provider_id = p.provider_id
WHERE c.status = 'Completed'
GROUP BY p.name
ORDER BY successful_claims DESC;

-- =====================================
-- Q10: Percentage of claim status
-- =====================================
SELECT status,
COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims_data) AS percentage
FROM claims_data
GROUP BY status;

-- =====================================
-- Q11: Average quantity claimed per receiver
-- =====================================
SELECT r.name, AVG(f.quantity) AS avg_quantity
FROM claims_data c
JOIN food_listings_data f ON c.food_id = f.food_id
JOIN receivers_data r ON c.receiver_id = r.receiver_id
GROUP BY r.name;

-- =====================================
-- Q12: Most claimed meal type
-- =====================================
SELECT f.meal_type, COUNT(*) AS total_claims
FROM claims_data c
JOIN food_listings_data f ON c.food_id = f.food_id
GROUP BY f.meal_type
ORDER BY total_claims DESC;

-- =====================================
-- Q13: Total food donated by each provider
-- =====================================
SELECT p.name, SUM(f.quantity) AS total_donated
FROM food_listings_data f
JOIN providers_data p ON f.provider_id = p.provider_id
GROUP BY p.name
ORDER BY total_donated DESC;