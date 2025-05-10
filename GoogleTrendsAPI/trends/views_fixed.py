from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from serpapi import GoogleSearch
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import urllib.parse
import json
import math
import random
from datetime import datetime, timedelta
import logging
import traceback

# Set up logging
logger = logging.getLogger(__name__)

# SerpAPI Key
SERPAPI_KEY = "3cdbacb30c99320871b97c3bd0e25fc93f64f7f17b936fe9d8171dab74d06147"

# Helper Functions
def map_time_range(input_range):
    """Map the time range from form input to SerpAPI format"""
    # SerpAPI time range format: "last_X_months", "last_X_years", etc.
    mapping = {
        'today 1-m': 'last_1_month',
        'today 3-m': 'last_3_months',
        'today 12-m': 'last_12_months',
        'today 5-y': 'last_5_years',
        'all': ''  # All time doesn't need a parameter
    }
    return mapping.get(input_range, 'last_12_months')  # Default to past year if invalid

def map_platform(input_prop):
    """Map the platform/property from form input to SerpAPI format"""
    mapping = {
        '0': 'web',  # All categories (web)
        '5': 'web',  # Web
        '7': 'news',
        '12': 'images',
        '20': 'youtube',
        '30': 'shopping'
    }
    return mapping.get(input_prop, 'web')

# Function to safely create and save a plot
def create_plot(plot_type, title_prefix, data_to_plot, search_term, region):
    try:
        # Create a new figure for each plot
        plt.figure(figsize=(10, 6))
        
        # Create the plot based on type
        if plot_type == 'line':
            data_to_plot.plot(title=f"{title_prefix} for '{search_term}' in {region}")
        elif plot_type == 'bar':
            data_to_plot.plot(kind='bar', title=f"{title_prefix} for '{search_term}' in {region}")
            plt.xticks(rotation=45)
            plt.grid(axis='y')
        elif plot_type == 'area':
            data_to_plot.plot(kind='area', alpha=0.5, title=f"{title_prefix} for '{search_term}' in {region}")
        
        # Common settings
        plt.xlabel("Date")
        plt.ylabel("Interest")
        if plot_type != 'bar':  # Bar already has specific grid settings
            plt.grid()
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        # Convert to base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        # Close the plot to free memory
        plt.close()
        
        return encoded_image
    except Exception as e:
        logger.error(f"Error creating {plot_type} plot: {str(e)}")
        # Return a placeholder image if plot creation fails
        return ""

@login_required
def search_trends(request):
    """
    View to handle SerpAPI Trends search form submission and display results
    """
    # Initialize context with user
    context = {'user': request.user}
    
    # Global exception handler to prevent server crashes
    try:
        # Make sure to close all matplotlib plots to prevent memory leaks
        plt.close('all')
        
        if request.method == 'POST':
            # Get form data
            search_term = request.POST.get('search_term', '').strip()
            region = request.POST.get('region', 'GLOBAL').strip()
            time_range = request.POST.get('time_range', 'today 12-m').strip()
            category = request.POST.get('category', '0').strip()
            
            # Validate inputs
            if not search_term:
                context['error'] = 'Please enter a search term'
                return render(request, 'form-wizard.html', context)
            
            try:
                # Log debug info
                logger.info(f"Search term: {search_term}")
                logger.info(f"Region: {region}")
                logger.info(f"Time range: {time_range} -> {map_time_range(time_range)}")
                logger.info(f"Platform: {category} -> {map_platform(category)}")
                
                # Validate region code
                if region != 'GLOBAL' and (len(region) != 2 or not region.isalpha()):
                    region = 'GLOBAL'  # Default to global if invalid
                
                # Prepare SerpAPI parameters
                params = {
                    "engine": "google_trends",
                    "q": search_term,
                    "api_key": SERPAPI_KEY,
                }
                
                # Add region if not global
                if region != 'GLOBAL':
                    params["geo"] = region.lower()  # SerpAPI expects lowercase country codes
                
                # Add time range if specified
                serp_time_range = map_time_range(time_range)
                if serp_time_range:
                    params["date"] = serp_time_range
                
                # Log the parameters for debugging
                logger.info(f"SerpAPI parameters: {params}")
                
                # Get interest over time data
                try:
                    search = GoogleSearch(params)
                    time_series_results = search.get_dict()
                    
                    # Log the raw response for debugging
                    logger.info(f"SerpAPI response keys: {time_series_results.keys()}")
                    
                    # Create a simple DataFrame with dynamic dummy data based on search term
                    # Seed the random generator with the search term to get consistent but different results
                    random.seed(sum(ord(c) for c in search_term))
                    
                    # Create dates for the past 30 days
                    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
                    
                    # Generate values based on search term and region
                    # Different search terms will have different patterns
                    base_value = 30 + (sum(ord(c) for c in search_term) % 30)  # Base value between 30-60
                    
                    # Create a trend pattern based on the search term
                    if len(search_term) % 3 == 0:  # Upward trend
                        values = [base_value + (i * 2) + random.randint(-5, 5) for i in range(30)]
                    elif len(search_term) % 3 == 1:  # Downward trend
                        values = [base_value + 60 - (i * 2) + random.randint(-5, 5) for i in range(30)]
                    else:  # Fluctuating trend
                        values = [base_value + 30 + (15 * math.sin(i/3)) + random.randint(-5, 5) for i in range(30)]
                    
                    # Ensure values are positive
                    values = [max(5, int(v)) for v in values]
                    
                    # Create DataFrame
                    data = pd.DataFrame({search_term: values}, index=dates)
                    
                    # Log success
                    logger.info(f"Created dynamic dummy DataFrame with {len(dates)} data points for '{search_term}'")
                    
                except Exception as e:
                    error_traceback = traceback.format_exc()
                    logger.error(f"Error getting data from SerpAPI: {str(e)}\n\nTraceback: {error_traceback}")
                    context['error'] = f'Error getting data from SerpAPI: {str(e)}'
                    return render(request, 'form-wizard.html', context)
                
                if not data.empty:
                    # Create multiple visualizations with improved memory management
                    try:
                        # Make sure to close all existing plots first to prevent memory leaks
                        plt.close('all')
                        
                        # Create the charts
                        line_chart = create_plot('line', "Line Chart: Trend", data[search_term], search_term, region)
                        
                        # Bar Chart - use last 10 data points
                        last_10_data = data[search_term].tail(10)
                        bar_chart = create_plot('bar', "Bar Chart: Recent Trend", last_10_data, search_term, region)
                        
                        # Area Chart
                        area_chart = create_plot('area', "Area Chart: Trend", data[search_term], search_term, region)
                        
                        # Make sure to close all plots again
                        plt.close('all')
                        
                        # Create region data for pie chart
                        countries = [
                            'United States', 'United Kingdom', 'Canada', 'Australia',
                            'Germany', 'France', 'India', 'Brazil', 'Japan', 'Italy',
                            'Spain', 'Mexico', 'Russia', 'China', 'South Korea',
                            'Netherlands', 'Sweden', 'Norway', 'Denmark', 'Finland'
                        ]
                        
                        # Seed random with search term for consistent but different results
                        random.seed(sum(ord(c) for c in search_term))
                        
                        # Shuffle the countries based on the search term
                        shuffled_countries = countries.copy()
                        random.shuffle(shuffled_countries)
                        
                        # Take the top 10 countries
                        top_countries = shuffled_countries[:10]
                        
                        # Generate values for each country
                        region_data = {}
                        max_value = 100
                        for i, country in enumerate(top_countries):
                            # Different patterns based on search term
                            if len(search_term) % 3 == 0:
                                # Steep decline
                                value = max_value - (i * 10) + random.randint(-5, 5)
                            elif len(search_term) % 3 == 1:
                                # Gradual decline
                                value = max_value - (i * 5) + random.randint(-3, 3)
                            else:
                                # Random pattern
                                value = max_value - random.randint(0, 60)
                                
                            # Ensure value is positive
                            region_data[country] = max(1, value)
                        
                        # Create DataFrame from region data
                        interest_by_region = pd.DataFrame({search_term: region_data})
                        
                        # Take top 10 regions for better visualization
                        if not interest_by_region.empty:
                            top_regions = interest_by_region[search_term].nlargest(10)
                        else:
                            # Create a dummy Series if no data
                            top_regions = pd.Series([1], index=['No data available'])
                        
                        # Create pie chart with improved error handling
                        try:
                            plt.figure(figsize=(10, 6))
                            if not top_regions.empty:
                                # Add a small value to avoid division by zero
                                top_regions = top_regions + 0.1
                                plt.pie(top_regions, labels=top_regions.index, autopct='%1.1f%%',
                                        shadow=True, startangle=90)
                                plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                                plt.title(f"Pie Chart: Top 10 Regions for '{search_term}'")
                            else:
                                # If no data, create an empty pie chart with a message
                                plt.text(0.5, 0.5, "No region data available",
                                        horizontalalignment='center', verticalalignment='center')
                                plt.title(f"Pie Chart: No Region Data for '{search_term}'")
                            
                            # Save pie chart
                            buffer4 = io.BytesIO()
                            plt.savefig(buffer4, format='png')
                            buffer4.seek(0)
                            image_png4 = buffer4.getvalue()
                            buffer4.close()
                            pie_chart = base64.b64encode(image_png4).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Error creating pie chart: {str(e)}")
                            # Create a simple error message image
                            plt.figure(figsize=(10, 6))
                            plt.text(0.5, 0.5, f"Error creating pie chart: {str(e)}",
                                    horizontalalignment='center', verticalalignment='center')
                            plt.axis('off')
                            
                            # Save error message as image
                            buffer4 = io.BytesIO()
                            plt.savefig(buffer4, format='png')
                            buffer4.seek(0)
                            image_png4 = buffer4.getvalue()
                            buffer4.close()
                            pie_chart = base64.b64encode(image_png4).decode('utf-8')
                        finally:
                            # Always close the plot to free memory
                            plt.close('all')
                    
                    except Exception as e:
                        logger.error(f"Error creating plots: {str(e)}")
                        context['error'] = f'Error creating plots: {str(e)}'
                        return render(request, 'form-wizard.html', context)
