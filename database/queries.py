"""
Predefined analytical SQL queries for Food Waste Management Dashboard.
Preserves and organizes all 18 analytical questions from the original codebase.
"""

SAFE_READONLY_PATTERN = r"^\s*(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN)\b"

PREDEFINED_QUERIES = {
    "1. Providers & Receivers per City": {
        "description": "Compare food provider count vs receiver count across distinct cities.",
        "sql": """
            SELECT 
                p.City,
                COUNT(DISTINCT p.Provider_ID) AS Providers,
                COUNT(DISTINCT r.Receiver_ID) AS Receivers
            FROM providers_data p
            JOIN receivers_data r ON p.City = r.City
            GROUP BY p.City
            ORDER BY Providers DESC, Receivers DESC;
        """
    },
    "2. Top Provider Type by Food Volume": {
        "description": "Total quantity of surplus food contributed by each provider business type.",
        "sql": """
            SELECT 
                Provider_Type, 
                SUM(Quantity) AS Total_Food_Quantity,
                COUNT(*) AS Total_Listings
            FROM food_listings_data
            GROUP BY Provider_Type
            ORDER BY Total_Food_Quantity DESC;
        """
    },
    "3. Providers Contact Directory": {
        "description": "Full contact and location directory of registered food providers.",
        "sql": """
            SELECT 
                Provider_ID,
                Name, 
                Type, 
                Contact, 
                City 
            FROM providers_data
            ORDER BY City, Name;
        """
    },
    "4. Top Receivers by Claim Count": {
        "description": "Receivers who have claimed the largest number of food packages.",
        "sql": """
            SELECT 
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                r.Type AS Receiver_Type,
                r.City,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM claims_data c
            JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name, r.Type, r.City
            ORDER BY Total_Claims DESC;
        """
    },
    "5. Total Food Quantity & Overview": {
        "description": "Aggregate volume of all listed surplus food items.",
        "sql": """
            SELECT 
                COUNT(*) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity,
                AVG(Quantity) AS Avg_Quantity_Per_Listing,
                MIN(Quantity) AS Min_Listing_Quantity,
                MAX(Quantity) AS Max_Listing_Quantity
            FROM food_listings_data;
        """
    },
    "6. Cities with Highest Food Listings": {
        "description": "Cities ranked by total count of registered food listings.",
        "sql": """
            SELECT 
                Location AS City, 
                COUNT(*) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity
            FROM food_listings_data
            GROUP BY Location
            ORDER BY Total_Listings DESC;
        """
    },
    "7. Most Common Food Types": {
        "description": "Distribution of food items across dietary categories (Vegan, Veg, Non-Veg).",
        "sql": """
            SELECT 
                Food_Type, 
                COUNT(*) AS Listing_Count,
                SUM(Quantity) AS Total_Quantity
            FROM food_listings_data
            GROUP BY Food_Type
            ORDER BY Total_Quantity DESC;
        """
    },
    "8. Claims per Food Listing": {
        "description": "Number of claim interactions for each food listing ID.",
        "sql": """
            SELECT 
                f.Food_ID,
                f.Food_Name,
                f.Quantity,
                f.Location,
                COUNT(c.Claim_ID) AS Total_Claims,
                MAX(c.Status) AS Latest_Status
            FROM food_listings_data f
            LEFT JOIN claims_data c ON f.Food_ID = c.Food_ID
            GROUP BY f.Food_ID, f.Food_Name, f.Quantity, f.Location
            ORDER BY Total_Claims DESC;
        """
    },
    "9. Top Providers by Completed Claims": {
        "description": "Providers with the highest number of successfully redistributed/completed claims.",
        "sql": """
            SELECT 
                p.Provider_ID,
                p.Name AS Provider_Name,
                p.City,
                COUNT(c.Claim_ID) AS Completed_Claims,
                SUM(f.Quantity) AS Total_Redistributed_Qty
            FROM claims_data c
            JOIN food_listings_data f ON c.Food_ID = f.Food_ID
            JOIN providers_data p ON f.Provider_ID = p.Provider_ID
            WHERE c.Status = 'Completed'
            GROUP BY p.Provider_ID, p.Name, p.City
            ORDER BY Completed_Claims DESC;
        """
    },
    "10. Claim Status Percentage Distribution": {
        "description": "Proportion of claims in Completed, Pending, or Cancelled status.",
        "sql": """
            SELECT 
                Status,
                COUNT(*) AS Total_Count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims_data), 2) AS Percentage
            FROM claims_data
            GROUP BY Status
            ORDER BY Total_Count DESC;
        """
    },
    "11. Average Quantity Claimed per Receiver": {
        "description": "Average food volume claimed across completed receiver transactions.",
        "sql": """
            SELECT 
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                r.Type AS Receiver_Type,
                ROUND(AVG(f.Quantity), 2) AS Avg_Quantity_Per_Claim,
                SUM(f.Quantity) AS Total_Quantity_Claimed,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM claims_data c
            JOIN food_listings_data f ON c.Food_ID = f.Food_ID
            JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name, r.Type
            ORDER BY Total_Quantity_Claimed DESC;
        """
    },
    "12. Most Claimed Meal Type": {
        "description": "Meal types (Breakfast, Lunch, Dinner, Snacks) with the most claim activity.",
        "sql": """
            SELECT 
                f.Meal_Type, 
                COUNT(c.Claim_ID) AS Total_Claims,
                SUM(f.Quantity) AS Total_Quantity
            FROM food_listings_data f
            LEFT JOIN claims_data c ON f.Food_ID = c.Food_ID
            GROUP BY f.Meal_Type
            ORDER BY Total_Claims DESC;
        """
    },
    "13. Total Food Donated by Each Provider": {
        "description": "Total food quantity listed and contributed by each registered provider.",
        "sql": """
            SELECT 
                p.Provider_ID,
                p.Name AS Provider_Name,
                p.Type AS Provider_Type,
                p.City,
                SUM(f.Quantity) AS Total_Donated_Qty,
                COUNT(f.Food_ID) AS Total_Donations
            FROM food_listings_data f
            JOIN providers_data p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Provider_ID, p.Name, p.Type, p.City
            ORDER BY Total_Donated_Qty DESC;
        """
    },
    "14. Cities with Highest Food Waste (Unclaimed Food)": {
        "description": "Cities with the highest volume of food listings that have not been completed.",
        "sql": """
            SELECT 
                Location AS City, 
                SUM(Quantity) AS Total_Unclaimed_Waste_Qty,
                COUNT(*) AS Unclaimed_Listings_Count
            FROM food_listings_data
            WHERE Food_ID NOT IN (
                SELECT Food_ID FROM claims_data WHERE Status = 'Completed'
            )
            GROUP BY Location
            ORDER BY Total_Unclaimed_Waste_Qty DESC;
        """
    },
    "15. Providers with Most Unclaimed Food": {
        "description": "Providers having the highest quantity of uncompleted/unclaimed food listings.",
        "sql": """
            SELECT 
                p.Provider_ID,
                p.Name AS Provider_Name,
                p.City,
                p.Type,
                SUM(f.Quantity) AS Unclaimed_Food_Qty,
                COUNT(f.Food_ID) AS Unclaimed_Listings
            FROM food_listings_data f
            JOIN providers_data p ON f.Provider_ID = p.Provider_ID
            WHERE f.Food_ID NOT IN (
                SELECT Food_ID FROM claims_data WHERE Status = 'Completed'
            )
            GROUP BY p.Provider_ID, p.Name, p.City, p.Type
            ORDER BY Unclaimed_Food_Qty DESC;
        """
    },
    "16. Top 5 Most Active Receivers": {
        "description": "Top 5 receivers by total claim interactions.",
        "sql": """
            SELECT 
                r.Receiver_ID,
                r.Name AS Receiver_Name,
                r.Type AS Receiver_Type,
                r.City,
                COUNT(c.Claim_ID) AS Total_Claims
            FROM claims_data c
            JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name, r.Type, r.City
            ORDER BY Total_Claims DESC
            LIMIT 5;
        """
    },
    "17. Food Availability by Meal Type": {
        "description": "Total quantity and distribution of food available across meal times.",
        "sql": """
            SELECT 
                Meal_Type, 
                COUNT(*) AS Total_Listings,
                SUM(Quantity) AS Total_Quantity,
                ROUND(AVG(Quantity), 1) AS Avg_Per_Listing
            FROM food_listings_data
            GROUP BY Meal_Type
            ORDER BY Total_Quantity DESC;
        """
    },
    "18. Expired vs Active Food Listings": {
        "description": "Comparison of listings that have passed their expiry date vs active ones.",
        "sql": """
            SELECT 
                COUNT(*) AS Total_Listings,
                SUM(CASE WHEN Expiry_Date::date < CURRENT_DATE 
                    THEN 1 ELSE 0 END) AS Expired_Listings,
                SUM(CASE WHEN Expiry_Date::date >= CURRENT_DATE 
                    THEN 1 ELSE 0 END) AS Active_Listings
            FROM food_listings_data;
        """
    }
}
