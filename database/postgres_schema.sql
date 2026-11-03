-- =====================================================================
-- Food Waste Management Dashboard - PostgreSQL Database Schema
-- Compatible with PostgreSQL 12+ and pgAdmin 4
-- Database: food_waste_db
-- =====================================================================

-- 1. Table: providers_data
CREATE TABLE IF NOT EXISTS providers_data (
    provider_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    contact VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India'
);

-- 2. Table: receivers_data
CREATE TABLE IF NOT EXISTS receivers_data (
    receiver_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    city VARCHAR(100),
    contact VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India'
);

-- 3. Table: food_listings_data
CREATE TABLE IF NOT EXISTS food_listings_data (
    food_id SERIAL PRIMARY KEY,
    food_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    expiry_date DATE,
    provider_id INT REFERENCES providers_data(provider_id) ON DELETE SET NULL,
    provider_type VARCHAR(100),
    location VARCHAR(100),
    food_type VARCHAR(100),
    meal_type VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India'
);

-- 4. Table: claims_data
CREATE TABLE IF NOT EXISTS claims_data (
    claim_id SERIAL PRIMARY KEY,
    food_id INT REFERENCES food_listings_data(food_id) ON DELETE SET NULL,
    receiver_id INT REFERENCES receivers_data(receiver_id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    timestamp TIMESTAMP
);

-- =====================================================================
-- Performance Indexes
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_food_listings_provider_id ON food_listings_data(provider_id);
CREATE INDEX IF NOT EXISTS idx_food_listings_location ON food_listings_data(location);
CREATE INDEX IF NOT EXISTS idx_food_listings_expiry_date ON food_listings_data(expiry_date);
CREATE INDEX IF NOT EXISTS idx_food_listings_food_type ON food_listings_data(food_type);
CREATE INDEX IF NOT EXISTS idx_food_listings_meal_type ON food_listings_data(meal_type);

CREATE INDEX IF NOT EXISTS idx_claims_food_id ON claims_data(food_id);
CREATE INDEX IF NOT EXISTS idx_claims_receiver_id ON claims_data(receiver_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims_data(status);

CREATE INDEX IF NOT EXISTS idx_providers_city ON providers_data(city);
CREATE INDEX IF NOT EXISTS idx_receivers_city ON receivers_data(city);

