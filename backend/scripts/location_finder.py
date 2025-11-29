"""
Complete Business Location Finder - All-in-One Script
Finds top 3 best locations for any business type in Delhi

Required files (same directory):
1. Delhi_Areas_All_11_Criteria_Real_Data.csv
2. categoryAndSuper.csv
3. poi_weightage_by_category.csv (optional - weights are hardcoded)

Usage:
    python location_finder.py cafe
    python location_finder.py gym
    python location_finder.py restaurant
"""
import pandas as pd
import sqlite3
import sys


# ============================================================================
# HARDCODED WEIGHTS FOR 13 SUPER CATEGORIES
# ============================================================================
WEIGHTS = {
    'Accommodation & Lodging': {
        'Score_Population_Density': 15.0, 'Score_Footfall': 20.0, 'Score_Transit': 12.0,
        'Score_Traffic': 5.0, 'Score_Rent_Value': 8.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 5.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 8.0,
        'Score_Safety': 6.0
    },
    'Education & Training': {
        'Score_Population_Density': 28.0, 'Score_Footfall': 10.0, 'Score_Transit': 12.0,
        'Score_Traffic': 8.0, 'Score_Rent_Value': 8.0, 'Score_Parking': 15.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 5.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 5.0
    },
    'Entertainment & Leisure': {
        'Score_Population_Density': 20.0, 'Score_Footfall': 25.0, 'Score_Transit': 10.0,
        'Score_Traffic': 5.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 15.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 2.0,
        'Score_Safety': 1.0
    },
    'Financial & Legal Services': {
        'Score_Population_Density': 20.0, 'Score_Footfall': 5.0, 'Score_Transit': 12.0,
        'Score_Traffic': 8.0, 'Score_Rent_Value': 15.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 12.0,
        'Score_Safety': 4.0
    },
    'Fitness & Wellness': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 20.0, 'Score_Transit': 8.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 8.0, 'Score_Walkability': 10.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 3.0
    },
    'Food & Beverages': {
        'Score_Population_Density': 20.0, 'Score_Footfall': 30.0, 'Score_Transit': 5.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 5.0,
        'Score_Night_Activity': 15.0, 'Score_Walkability': 12.0, 'Score_POI_Synergy': 3.0,
        'Score_Safety': 2.0
    },
    'Government & Public Services': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 10.0, 'Score_Transit': 15.0,
        'Score_Traffic': 8.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 12.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 5.0, 'Score_POI_Synergy': 8.0,
        'Score_Safety': 2.0
    },
    'Health & Medical': {
        'Score_Population_Density': 30.0, 'Score_Footfall': 15.0, 'Score_Transit': 10.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 12.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 7.0,
        'Score_Safety': 5.0
    },
    'Other / Misc': {
        'Score_Population_Density': 9.09, 'Score_Footfall': 9.09, 'Score_Transit': 9.09,
        'Score_Traffic': 9.09, 'Score_Rent_Value': 9.09, 'Score_Parking': 9.09,
        'Score_Night_Activity': 9.09, 'Score_Walkability': 9.09, 'Score_POI_Synergy': 9.09,
        'Score_Safety': 9.09
    },
    'Parks & Outdoor Recreation': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 20.0, 'Score_Transit': 12.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 2.0, 'Score_Walkability': 12.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 6.0
    },
    'Religious & Spiritual Places': {
        'Score_Population_Density': 28.0, 'Score_Footfall': 15.0, 'Score_Transit': 10.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 5.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 5.0
    },
    'Shopping & Retail': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 25.0, 'Score_Transit': 8.0,
        'Score_Traffic': 5.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 5.0, 'Score_Walkability': 10.0, 'Score_POI_Synergy': 2.0,
        'Score_Safety': 2.0
    },
    'Transport & Auto Services': {
        'Score_Population_Density': 15.0, 'Score_Footfall': 10.0, 'Score_Transit': 15.0,
        'Score_Traffic': 25.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 3.0, 'Score_Walkability': 5.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 2.0
    }
}


# ============================================================================
# COMPLEMENTARY CATEGORIES
# ============================================================================
COMPLEMENTARY_CATEGORIES = {
    'Food & Beverages': ['Shopping & Retail', 'Entertainment & Leisure', 'Parks & Outdoor Recreation', 'Transport & Auto Services', 'Fitness & Wellness'],
    'Fitness & Wellness': ['Food & Beverages', 'Health & Medical', 'Parks & Outdoor Recreation', 'Shopping & Retail', 'Accommodation & Lodging'],
    'Health & Medical': ['Fitness & Wellness', 'Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services', 'Accommodation & Lodging'],
    'Shopping & Retail': ['Food & Beverages', 'Entertainment & Leisure', 'Transport & Auto Services', 'Fitness & Wellness', 'Accommodation & Lodging'],
    'Entertainment & Leisure': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services', 'Accommodation & Lodging', 'Parks & Outdoor Recreation'],
    'Education & Training': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services', 'Accommodation & Lodging', 'Parks & Outdoor Recreation'],
    'Accommodation & Lodging': ['Food & Beverages', 'Entertainment & Leisure', 'Shopping & Retail', 'Transport & Auto Services', 'Parks & Outdoor Recreation'],
    'Transport & Auto Services': ['Food & Beverages', 'Shopping & Retail', 'Accommodation & Lodging', 'Entertainment & Leisure', 'Financial & Legal Services'],
    'Financial & Legal Services': ['Shopping & Retail', 'Food & Beverages', 'Government & Public Services', 'Transport & Auto Services', 'Accommodation & Lodging'],
    'Government & Public Services': ['Financial & Legal Services', 'Food & Beverages', 'Transport & Auto Services', 'Shopping & Retail', 'Parks & Outdoor Recreation'],
    'Parks & Outdoor Recreation': ['Food & Beverages', 'Fitness & Wellness', 'Entertainment & Leisure', 'Shopping & Retail', 'Accommodation & Lodging'],
    'Religious & Spiritual Places': ['Food & Beverages', 'Shopping & Retail', 'Parks & Outdoor Recreation', 'Transport & Auto Services', 'Accommodation & Lodging'],
    'Other / Misc': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services']
}


# ============================================================================
# STEP 1: AREA SCORE CALCULATION
# ============================================================================
def load_category_mapping():
    """Load category to super category mapping"""
    df = pd.read_csv('categoryAndSuper.csv')
    category_map = {}
    
    for _, row in df.iterrows():
        super_cat = row['super_category']
        cat_dict_str = row['category_dict']
        
        try:
            cat_dict_str = cat_dict_str.strip('{}')
            pairs = cat_dict_str.split(', ')
            for pair in pairs:
                if '=' in pair:
                    category = pair.split('=')[0].strip().strip("'\"")
                    category_map[category.lower()] = super_cat
        except:
            pass
    
    return category_map


def get_super_category(business_category):
    """Map business category to super category"""
    category_map = load_category_mapping()
    return category_map.get(business_category.lower(), 'Other / Misc')


def calculate_area_scores(business_category):
    """Calculate area scores for all areas and return top 10"""
    areas_df = pd.read_csv('Delhi_Areas_All_11_Criteria_Real_Data.csv')
    super_category = get_super_category(business_category)
    weights = WEIGHTS[super_category]
    
    scores = []
    for _, row in areas_df.iterrows():
        score = 0.0
        for feature, weight in weights.items():
            if feature in row:
                score += (row[feature] * weight / 100)
        
        scores.append({
            'Area': row['name'],
            'Score': round(score, 2)
        })
    
    result_df = pd.DataFrame(scores)
    result_df = result_df.sort_values('Score', ascending=False).head(10).reset_index(drop=True)
    result_df.index = result_df.index + 1
    
    return result_df, super_category


# ============================================================================
# STEP 2: COMPOSITE SCORE CALCULATION
# ============================================================================
def count_competitors_in_area(conn, area_name, super_category):
    """Count competitors (same super category) in the area"""
    query = """
    SELECT COUNT(*) as competitor_count
    FROM pointsSuper ps
    INNER JOIN pointsArea pa ON ps.id = pa.id
    WHERE pa.area = ? AND ps.super_category = ?
    """
    try:
        result = pd.read_sql_query(query, conn, params=(area_name, super_category))
        return result['competitor_count'].iloc[0]
    except:
        return 50


def count_complementary_businesses(conn, area_name, complementary_categories):
    """Count complementary businesses in the area"""
    if not complementary_categories:
        return 0
    
    placeholders = ','.join('?' * len(complementary_categories))
    query = f"""
    SELECT COUNT(*) as complementary_count
    FROM pointsSuper ps
    INNER JOIN pointsArea pa ON ps.id = pa.id
    WHERE pa.area = ? AND ps.super_category IN ({placeholders})
    """
    try:
        params = [area_name] + complementary_categories
        result = pd.read_sql_query(query, conn, params=params)
        return result['complementary_count'].iloc[0]
    except:
        return 30


def calculate_opportunity_score(competitor_count, all_counts):
    """Calculate opportunity score (fewer competitors = higher score)"""
    min_val = min(all_counts)
    max_val = max(all_counts)
    if max_val == min_val:
        return 50.0
    return ((max_val - competitor_count) / (max_val - min_val)) * 100


def calculate_ecosystem_score(complementary_count, all_counts):
    """Calculate ecosystem score (more complementary = higher score)"""
    min_val = min(all_counts)
    max_val = max(all_counts)
    if max_val == min_val:
        return 50.0
    return ((complementary_count - min_val) / (max_val - min_val)) * 100


def calculate_composite_scores(business_category, db_path=None, use_database=False):
    """Calculate composite scores and return top 3 areas"""
    
    print("\n" + "="*80)
    print("STEP 1: Calculating Area Scores (11 Criteria)")
    print("="*80)
    
    top_10_df, super_category = calculate_area_scores(business_category)
    print(f"\n✓ Business: {business_category}")
    print(f"✓ Super Category: {super_category}")
    print(f"\nTop 10 Areas by Area Score:")
    print(top_10_df.to_string())
    
    complementary_cats = COMPLEMENTARY_CATEGORIES.get(super_category, [])
    
    print("\n" + "="*80)
    print("STEP 2: Calculating Composite Scores (Opportunity + Ecosystem)")
    print("="*80)
    
    results = []
    
    if use_database and db_path:
        try:
            conn = sqlite3.connect(db_path)
            print("\n✓ Database connected")
            print(f"✓ Querying {len(complementary_cats)} complementary categories...")
            
            for _, row in top_10_df.iterrows():
                area = row['Area']
                competitors = count_competitors_in_area(conn, area, super_category)
                complementary = count_complementary_businesses(conn, area, complementary_cats)
                results.append({
                    'Area': area,
                    'Area_Score': row['Score'],
                    'Competitors': competitors,
                    'Complementary': complementary
                })
            conn.close()
        except Exception as e:
            print(f"\n⚠️  Database error: {e}")
            print("⚠️  Falling back to mock data...")
            use_database = False
    
    if not use_database:
        import random
        random.seed(42)
        print("\n⚠️  Using mock data (no database)")
        
        for _, row in top_10_df.iterrows():
            results.append({
                'Area': row['Area'],
                'Area_Score': row['Score'],
                'Competitors': random.randint(20, 100),
                'Complementary': random.randint(50, 200)
            })
    
    results_df = pd.DataFrame(results)
    
    # Normalize scores
    all_competitors = results_df['Competitors'].tolist()
    all_complementary = results_df['Complementary'].tolist()
    
    results_df['Opportunity_Score'] = results_df['Competitors'].apply(
        lambda x: calculate_opportunity_score(x, all_competitors)
    )
    results_df['Ecosystem_Score'] = results_df['Complementary'].apply(
        lambda x: calculate_ecosystem_score(x, all_complementary)
    )
    
    # Calculate composite score
    results_df['Composite_Score'] = (
        results_df['Area_Score'] * 0.60 +
        results_df['Opportunity_Score'] * 0.20 +
        results_df['Ecosystem_Score'] * 0.20
    )
    
    # Sort and get top 3
    results_df = results_df.sort_values('Composite_Score', ascending=False).reset_index(drop=True)
    results_df = results_df.round(2)
    results_df.index = results_df.index + 1
    
    return results_df.head(3), results_df


# ============================================================================
# MAIN FUNCTION
# ============================================================================
def find_best_locations(business_type, db_path=None, use_database=False):
    """
    Find top 3 best locations for a business
    
    Parameters:
        business_type (str): e.g., 'cafe', 'gym', 'restaurant'
        db_path (str): Path to SQLite database (optional)
        use_database (bool): Use real database or mock data
    """
    print("\n" + "🎯"*40)
    print(f"FINDING BEST LOCATIONS FOR: {business_type.upper()}")
    print("🎯"*40)
    
    top_3, all_10 = calculate_composite_scores(business_type, db_path, use_database)
    
    print("\n" + "="*80)
    print("🏆 TOP 3 RECOMMENDED AREAS")
    print("="*80)
    
    for idx, row in top_3.iterrows():
        print(f"\n#{idx}. {row['Area']}")
        print(f"   {'─'*74}")
        print(f"   📊 Area Score:      {row['Area_Score']:6.2f}/100  (Weight: 60%)")
        print(f"   💼 Opportunity:     {row['Opportunity_Score']:6.2f}/100  (Weight: 20%) - {row['Competitors']} competitors")
        print(f"   🌐 Ecosystem:       {row['Ecosystem_Score']:6.2f}/100  (Weight: 20%) - {row['Complementary']} complementary")
        print(f"   {'─'*74}")
        print(f"   ⭐ COMPOSITE SCORE: {row['Composite_Score']:6.2f}/100")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n💡 Recommendation: Start with #{top_3.index[0]} - {top_3.iloc[0]['Area']}")
    print(f"   Composite Score: {top_3.iloc[0]['Composite_Score']}/100\n")
    
    return top_3


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================
if __name__ == '__main__':
    if len(sys.argv) > 1:
        business = sys.argv[1]
    else:
        print("\n" + "="*80)
        print("BUSINESS LOCATION FINDER - DELHI")
        print("="*80)
        print("\nSupported business types:")
        print("  Food: cafe, restaurant, bakery, bar, pizza, fast food")
        print("  Fitness: gym, yoga studio, spa, beauty salon")
        print("  Health: hospital, clinic, pharmacy, dentist")
        print("  Retail: clothing store, electronics, shoe store, furniture")
        print("  Entertainment: cinema, theatre, club, music venue")
        print("  Education: school, college, training center")
        print("  Accommodation: hotel, hostel, resort")
        print("  And many more...")
        print()
        business = input("Enter your business type: ").strip()
    
    if not business:
        print("❌ Please provide a business type")
        sys.exit(1)
    
    # Run analysis
    # Set use_database=True and db_path='your_db.db' to use real database
    find_best_locations(business, use_database=False)
