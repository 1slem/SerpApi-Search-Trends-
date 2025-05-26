from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from serpapi import GoogleSearch
import pandas as pd
from .forms import ContactForm
from .models import UserSearch, UserPlan, ContactMessage
from django_countries import countries

import matplotlib
matplotlib.use('Agg')  # This must be done before importing pyplot
import matplotlib.pyplot as plt
import io
import base64
import urllib.parse
import json
import math
from datetime import datetime, timedelta
from .models import UserSearch, UserPlan

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

@login_required
def pricing_page(request):
    """
    View to display pricing plans
    """
    message = request.GET.get('message', None)
    context = {
        'user': request.user,
        'message': message
    }
    return render(request, 'pricing-table.html', context)

@login_required
def search_history(request):
    """
    View to display user's search history
    """
    # Get the user's search history
    searches = UserSearch.objects.filter(user=request.user).order_by('-search_date')

    # Get user's plan information
    user_plan, created = UserPlan.objects.get_or_create(
        user=request.user,
        defaults={'plan_type': 'free', 'max_searches': 3, 'status': 'active'}
    )

    # Calculate searches left
    search_count = searches.count()
    searches_left = max(0, user_plan.max_searches - search_count)

    context = {
        'user': request.user,
        'searches': searches,
        'search_count': search_count,
        'searches_left': searches_left,
        'max_searches': user_plan.max_searches
    }

    return render(request, 'search-history.html', context)

@login_required
@require_POST
def delete_search_history(request):
    """
    View to delete selected search history entries
    """
    try:
        # Get the list of search IDs to delete
        search_ids = request.POST.getlist('search_ids[]')

        if not search_ids:
            return JsonResponse({'success': False, 'error': 'No searches selected'})

        # Convert to integers and filter by user to ensure security
        search_ids = [int(id) for id in search_ids if id.isdigit()]

        # Delete only the user's own searches
        deleted_count = UserSearch.objects.filter(
            id__in=search_ids,
            user=request.user
        ).delete()[0]

        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} search(es)',
            'deleted_count': deleted_count
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})

@login_required
@require_POST
def delete_single_search(request, search_id):
    """
    View to delete a single search history entry
    """
    try:
        # Get the search entry and ensure it belongs to the current user
        search = UserSearch.objects.get(id=search_id, user=request.user)
        search_term = search.search_term
        search.delete()

        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted search "{search_term}"'
        })

    except UserSearch.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Search not found or access denied'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})

@login_required
def search_trends(request):
    """
    View to handle Google Trends search form submission and display results
    """
    context = {'user': request.user}

    # Get or create user plan
    user_plan, created = UserPlan.objects.get_or_create(
        user=request.user,
        defaults={'plan_type': 'free', 'max_searches': 3, 'status': 'active'}
    )

    # Calculate searches left for display in the template
    search_count = UserSearch.objects.filter(user=request.user).count()
    searches_left = user_plan.max_searches - search_count

    # Add search limit info to context
    context.update({
        'search_count': search_count,
        'searches_left': searches_left,
        'max_searches': user_plan.max_searches,
        'countries': countries  # Add all countries from django-countries
    })

    if request.method == 'POST':
        search_term = request.POST.get('search_term', '').strip()
        region = request.POST.get('region', 'GLOBAL').strip()
        time_range = request.POST.get('time_range', 'today 12-m').strip()
        category = request.POST.get('category', '0').strip()

        if not search_term:
            context['error'] = 'Please enter a search term'
            return render(request, 'form-wizard.html', context)

        # Check if user has reached their search limit
        if searches_left <= 0:
            # Instead of redirecting, show an alert on the same page
            context.update({
                'error': "You've reached your search limit. Please upgrade your plan to continue searching.",
                'search_count': search_count,
                'searches_left': searches_left,
                'max_searches': user_plan.max_searches
            })
            return render(request, 'form-wizard.html', context)

        try:
            # Print debug info
            print(f"Search term: {search_term}")
            print(f"Region: {region}")
            print(f"Time range: {time_range} -> {map_time_range(time_range)}")
            print(f"Platform: {category} -> {map_platform(category)}")

            # Validate region code using django-countries
            if region != 'GLOBAL':
                # Check if the region code is valid according to django-countries
                valid_country_codes = [code for code, _ in countries]
                if region not in valid_country_codes:
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

            # Print the parameters for debugging
            print(f"SerpAPI parameters: {params}")

            # Get interest over time data
            try:
                search = GoogleSearch(params)
                time_series_results = search.get_dict()

                # Print the raw response for debugging
                print(f"SerpAPI response keys: {time_series_results.keys()}")

                # Create a simple DataFrame with dynamic dummy data based on search term
                # This will allow us to see different visualizations for different inputs
                import random

                # Seed the random generator with both search term and region to get consistent but different results
                # This ensures results change when either search term or region changes
                seed_string = search_term + region
                random.seed(sum(ord(c) for c in seed_string))

                # Generate dates based on the selected time range
                num_points = 0
                end_date = datetime.now()

                if time_range == 'today 1-m':
                    # Last month - daily data points
                    num_points = 30
                    dates = [end_date - timedelta(days=i) for i in range(num_points)]
                elif time_range == 'today 3-m':
                    # Last 3 months - weekly data points
                    num_points = 12  # ~12 weeks in 3 months
                    dates = [end_date - timedelta(weeks=i) for i in range(num_points)]
                elif time_range == 'today 12-m':
                    # Last 12 months - monthly data points
                    num_points = 12
                    dates = []
                    for i in range(num_points):
                        # Go back i months from current date
                        month_delta = end_date.month - (i % 12)
                        year_delta = end_date.year - (i // 12)
                        if month_delta <= 0:
                            month_delta += 12
                            year_delta -= 1
                        dates.append(datetime(year_delta, month_delta, 1))
                    dates.reverse()  # Reverse to get chronological order
                elif time_range == 'today 5-y':
                    # Last 5 years - quarterly data points
                    num_points = 20  # 4 quarters * 5 years
                    dates = []
                    for i in range(num_points):
                        year = end_date.year - (i // 4)
                        quarter = 4 - (i % 4)
                        # Set month based on quarter (Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct)
                        month = (quarter - 1) * 3 + 1
                        dates.append(datetime(year, month, 1))
                    dates.reverse()  # Reverse to get chronological order
                else:  # 'all' or default
                    # All time - yearly data points for the past 10 years
                    num_points = 10
                    dates = []
                    for i in range(num_points):
                        dates.append(datetime(end_date.year - i, 1, 1))
                    dates.reverse()  # Reverse to get chronological order

                # Generate values based on search term and region
                # Different search terms and regions will have different patterns
                seed_string = search_term + region
                base_value = 30 + (sum(ord(c) for c in seed_string) % 30)  # Base value between 30-60

                # Create a trend pattern based on both search term and region
                pattern_seed = (sum(ord(c) for c in seed_string) % 5)  # 5 different patterns

                # Use num_points instead of hardcoded 30
                if pattern_seed == 0:  # Upward trend
                    values = [base_value + (i * 2) + random.randint(-5, 5) for i in range(num_points)]
                elif pattern_seed == 1:  # Downward trend
                    values = [base_value + 60 - (i * 2) + random.randint(-5, 5) for i in range(num_points)]
                elif pattern_seed == 2:  # Fluctuating trend (sine wave)
                    # Adjust the sine wave frequency based on the number of points
                    freq_factor = 3 * (30 / max(1, num_points))
                    values = [base_value + 30 + (15 * math.sin(i/freq_factor)) + random.randint(-5, 5) for i in range(num_points)]
                elif pattern_seed == 3:  # Spike in the middle
                    # Adjust the spike position to be in the middle of the data points
                    mid_point = num_points / 2
                    spike_factor = 0.01 * (30 / max(1, num_points))
                    values = [base_value + 20 + (30 * math.exp(-spike_factor * (i - mid_point)**2)) + random.randint(-5, 5) for i in range(num_points)]
                else:  # Plateau pattern
                    # Adjust the plateau position based on the number of points
                    plateau_start = int(num_points * 0.3)
                    plateau_end = int(num_points * 0.7)
                    values = [base_value + (30 if plateau_start <= i <= plateau_end else 10) + random.randint(-5, 5) for i in range(num_points)]

                # Ensure values are positive
                values = [max(5, int(v)) for v in values]

                # Create DataFrame
                data = pd.DataFrame({search_term: values}, index=dates)

                # Log success
                print(f"Created dynamic dummy DataFrame with {len(dates)} data points for '{search_term}'")

            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                context['error'] = f'Error getting data from SerpAPI: {str(e)}\n\nTraceback: {error_traceback}'
                return render(request, 'form-wizard.html', context)

            if not data.empty:
                # Create multiple visualizations
                try:
                    # Get a human-readable time range description
                    time_range_display = {
                        'today 1-m': 'Last Month',
                        'today 3-m': 'Last 3 Months',
                        'today 12-m': 'Last 12 Months',
                        'today 5-y': 'Last 5 Years',
                        'all': 'All Time'
                    }.get(time_range, 'Last 12 Months')

                    # 1. Line Chart (Original)
                    plt.figure(figsize=(10, 6))
                    data[search_term].plot(title=f"Line Chart: Trend for '{search_term}' in {region} - {time_range_display}")
                    plt.xlabel("Date")
                    plt.ylabel("Interest")
                    plt.grid()

                    # Save line chart
                    buffer1 = io.BytesIO()
                    plt.savefig(buffer1, format='png')
                    buffer1.seek(0)
                    image_png1 = buffer1.getvalue()
                    buffer1.close()
                    line_chart = base64.b64encode(image_png1).decode('utf-8')
                    plt.close()

                    # 2. Bar Chart
                    plt.figure(figsize=(10, 6))
                    # Get the last 10 data points for the bar chart (or all if less than 10)
                    last_n_data = data[search_term].tail(min(10, len(data)))
                    last_n_data.plot(kind='bar', title=f"Bar Chart: Recent Trend for '{search_term}' in {region} - {time_range_display}")
                    plt.xlabel("Date")
                    plt.ylabel("Interest")
                    plt.xticks(rotation=45)
                    plt.grid(axis='y')

                    # Save bar chart
                    buffer2 = io.BytesIO()
                    plt.savefig(buffer2, format='png')
                    buffer2.seek(0)
                    image_png2 = buffer2.getvalue()
                    buffer2.close()
                    bar_chart = base64.b64encode(image_png2).decode('utf-8')
                    plt.close()

                    # 3. Area Chart
                    plt.figure(figsize=(10, 6))
                    data[search_term].plot(kind='area', alpha=0.5, title=f"Area Chart: Trend for '{search_term}' in {region} - {time_range_display}")
                    plt.xlabel("Date")
                    plt.ylabel("Interest")
                    plt.grid()

                    # Save area chart
                    buffer3 = io.BytesIO()
                    plt.savefig(buffer3, format='png')
                    buffer3.seek(0)
                    image_png3 = buffer3.getvalue()
                    buffer3.close()
                    area_chart = base64.b64encode(image_png3).decode('utf-8')
                    plt.close()

                    # 4. Pie Chart for Interest by Region
                    # Create dynamic dummy region data based on search term
                    # Define a list of country names for demo data
                    demo_countries = [
                        'United States', 'United Kingdom', 'Canada', 'Australia',
                        'Germany', 'France', 'India', 'Brazil', 'Japan', 'Italy',
                        'Spain', 'Mexico', 'Russia', 'China', 'South Korea',
                        'Netherlands', 'Sweden', 'Norway', 'Denmark', 'Finland'
                    ]

                    # Seed random with both search term and region for consistent but different results
                    seed_string = search_term + region
                    random.seed(sum(ord(c) for c in seed_string))

                    # Shuffle the countries based on the search term
                    shuffled_countries = demo_countries.copy()
                    random.shuffle(shuffled_countries)

                    # Take the top 10 countries
                    top_countries = shuffled_countries[:10]

                    # Generate values for regions within the selected country
                    region_data = {}
                    max_value = 100

                    # Define regions based on the selected country
                    if region == 'GLOBAL':
                        # If global is selected, show top countries
                        regions = top_countries
                        region_label = "Countries"
                    else:
                        # Define regions for specific countries
                        country_regions = {
                            'US': ['California', 'Texas', 'Florida', 'New York', 'Pennsylvania',
                                  'Illinois', 'Ohio', 'Georgia', 'North Carolina', 'Michigan'],
                            'GB': ['London', 'Manchester', 'Birmingham', 'Glasgow', 'Liverpool',
                                  'Edinburgh', 'Bristol', 'Sheffield', 'Leeds', 'Newcastle'],
                            'CA': ['Ontario', 'Quebec', 'British Columbia', 'Alberta', 'Manitoba',
                                  'Saskatchewan', 'Nova Scotia', 'New Brunswick', 'Newfoundland', 'Prince Edward Island'],
                            'AU': ['New South Wales', 'Victoria', 'Queensland', 'Western Australia', 'South Australia',
                                  'Tasmania', 'Australian Capital Territory', 'Northern Territory', 'Sydney', 'Melbourne'],
                            'DE': ['Bavaria', 'North Rhine-Westphalia', 'Baden-Württemberg', 'Lower Saxony', 'Hesse',
                                  'Saxony', 'Berlin', 'Rhineland-Palatinate', 'Hamburg', 'Schleswig-Holstein'],
                            'FR': ['Île-de-France', 'Auvergne-Rhône-Alpes', 'Nouvelle-Aquitaine', 'Occitanie', 'Hauts-de-France',
                                  'Provence-Alpes-Côte d\'Azur', 'Grand Est', 'Normandy', 'Brittany', 'Pays de la Loire'],
                            'IN': ['Maharashtra', 'Tamil Nadu', 'Karnataka', 'Delhi', 'Telangana',
                                  'Uttar Pradesh', 'Gujarat', 'West Bengal', 'Rajasthan', 'Kerala'],
                            'BR': ['São Paulo', 'Rio de Janeiro', 'Minas Gerais', 'Bahia', 'Paraná',
                                  'Rio Grande do Sul', 'Pernambuco', 'Ceará', 'Pará', 'Santa Catarina'],
                            'JP': ['Tokyo', 'Osaka', 'Kanagawa', 'Aichi', 'Saitama',
                                  'Chiba', 'Hyogo', 'Hokkaido', 'Fukuoka', 'Shizuoka'],
                            'IT': ['Lombardy', 'Lazio', 'Campania', 'Sicily', 'Veneto',
                                  'Emilia-Romagna', 'Piedmont', 'Apulia', 'Tuscany', 'Calabria']
                        }

                        # Get regions for the selected country, or use default regions if not found
                        regions = country_regions.get(region.upper(),
                                                     [f'Region {i+1}' for i in range(10)])
                        region_label = f"Regions in {region.upper()}"

                    # Use a pattern based on both search term and region
                    pattern_seed = (sum(ord(c) for c in seed_string) % 5)  # 5 different patterns

                    for i, region_name in enumerate(regions):
                        if pattern_seed == 0:
                            # Steep decline
                            value = max_value - (i * 10) + random.randint(-5, 5)
                        elif pattern_seed == 1:
                            # Gradual decline
                            value = max_value - (i * 5) + random.randint(-3, 3)
                        elif pattern_seed == 2:
                            # Exponential decline
                            value = max_value * math.exp(-0.2 * i) + random.randint(-5, 5)
                        elif pattern_seed == 3:
                            # First few regions dominate
                            value = max_value if i < 3 else max_value / (i + 1) + random.randint(-5, 5)
                        else:
                            # More even distribution
                            value = max_value - (i * 3) + random.randint(-3, 3)

                        # Ensure value is positive
                        region_data[region_name] = max(1, int(value))

                    # Create DataFrame from region data
                    interest_by_region = pd.DataFrame({search_term: region_data})

                    # Take top 10 regions for better visualization
                    if not interest_by_region.empty:
                        top_regions = interest_by_region[search_term].nlargest(10)
                    else:
                        # Create a dummy Series if no data
                        top_regions = pd.Series([1], index=['No data available'])

                    # Create pie chart
                    plt.figure(figsize=(10, 6))
                    if not top_regions.empty:
                        # Add a small value to avoid division by zero
                        top_regions = top_regions + 0.1
                        plt.pie(top_regions, labels=top_regions.index, autopct='%1.1f%%',
                                shadow=True, startangle=90)
                        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                        if region == 'GLOBAL':
                            plt.title(f"Pie Chart: Top Countries for '{search_term}'")
                        else:
                            plt.title(f"Pie Chart: Top Regions in {region.upper()} for '{search_term}'")
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
                    plt.close()

                    # 5. Additional Pie Chart - Interest by Platform
                    try:
                        # Generate platform interest data
                        platforms = {
                            'Web Search': 0,
                            'News Search': 0,
                            'Image Search': 0,
                            'YouTube': 0
                        }

                        # Seed random with search term and region
                        random.seed(sum(ord(c) for c in seed_string))

                        # Generate values based on the search term and region
                        total = 100
                        remaining = total

                        # Generate random values for each platform
                        for i, platform in enumerate(platforms.keys()):
                            if i == len(platforms) - 1:
                                # Last platform gets the remainder
                                platforms[platform] = remaining
                            else:
                                # Generate a random value for this platform
                                value = random.randint(10, min(50, remaining - 10))
                                platforms[platform] = value
                                remaining -= value

                        # Create the pie chart
                        plt.figure(figsize=(10, 6))
                        plt.pie(platforms.values(), labels=platforms.keys(), autopct='%1.1f%%',
                                shadow=True, startangle=90)
                        plt.axis('equal')
                        plt.title(f"Interest by Platform for '{search_term}'")

                        # Save platform pie chart
                        buffer5 = io.BytesIO()
                        plt.savefig(buffer5, format='png')
                        buffer5.seek(0)
                        image_png5 = buffer5.getvalue()
                        buffer5.close()
                        platform_pie_chart = base64.b64encode(image_png5).decode('utf-8')
                        plt.close()

                        # Create DataFrame for platform data
                        platform_df = pd.DataFrame({search_term: platforms})
                        platform_html = platform_df.to_html(classes='table table-striped')
                    except Exception as e:
                        print(f"Error creating platform pie chart: {str(e)}")
                        platform_pie_chart = ""
                        platform_html = "<div class='alert alert-warning'>Error displaying platform data.</div>"

                    # 6. Horizontal Bar Chart for Top Regions
                    try:
                        # Use the existing region data
                        plt.figure(figsize=(10, 6))

                        # Sort the data for better visualization
                        sorted_regions = interest_by_region[search_term].sort_values(ascending=True)

                        # Take only top 10 regions
                        top_10_regions = sorted_regions.tail(10)

                        # Create horizontal bar chart
                        top_10_regions.plot(kind='barh')

                        if region == 'GLOBAL':
                            plt.title(f"Top Countries for '{search_term}'")
                            plt.xlabel("Interest")
                            plt.ylabel("Country")
                        else:
                            plt.title(f"Top Regions in {region.upper()} for '{search_term}'")
                            plt.xlabel("Interest")
                            plt.ylabel("Region")

                        plt.grid(axis='x')

                        # Save horizontal bar chart
                        buffer6 = io.BytesIO()
                        plt.savefig(buffer6, format='png')
                        buffer6.seek(0)
                        image_png6 = buffer6.getvalue()
                        buffer6.close()
                        horizontal_bar_chart = base64.b64encode(image_png6).decode('utf-8')
                        plt.close()
                    except Exception as e:
                        print(f"Error creating horizontal bar chart: {str(e)}")
                        horizontal_bar_chart = ""

                    # 7. Radar Chart for Multiple Metrics
                    try:
                        # Generate metrics data
                        metrics = {
                            'Search Volume': random.randint(60, 100),
                            'Growth Rate': random.randint(40, 90),
                            'Competition': random.randint(30, 80),
                            'Click-through Rate': random.randint(50, 95),
                            'User Engagement': random.randint(45, 85)
                        }

                        # Create radar chart
                        # Number of variables
                        categories = list(metrics.keys())
                        N = len(categories)

                        # Values for each variable
                        values = list(metrics.values())

                        # Repeat the first value to close the polygon
                        values += values[:1]

                        # Calculate angle for each category
                        angles = [n / float(N) * 2 * math.pi for n in range(N)]
                        angles += angles[:1]  # Close the polygon

                        # Create the plot
                        plt.figure(figsize=(10, 6))
                        plt.subplot(111, polar=True)

                        # Draw the polygon
                        plt.plot(angles, values, linewidth=2, linestyle='solid')

                        # Fill the polygon
                        plt.fill(angles, values, alpha=0.25)

                        # Add labels
                        plt.xticks(angles[:-1], categories)

                        # Add title
                        plt.title(f"Metrics for '{search_term}'")

                        # Save radar chart
                        buffer7 = io.BytesIO()
                        plt.savefig(buffer7, format='png')
                        buffer7.seek(0)
                        image_png7 = buffer7.getvalue()
                        buffer7.close()
                        radar_chart = base64.b64encode(image_png7).decode('utf-8')
                        plt.close()
                    except Exception as e:
                        print(f"Error creating radar chart: {str(e)}")
                        radar_chart = ""

                except Exception as e:
                    context['error'] = f'Error creating plots: {str(e)}'
                    return render(request, 'form-wizard.html', context)

                # Create dynamic related queries data based on search term and region
                # Define possible query suffixes
                top_suffixes = [
                    'news', 'meaning', 'definition', 'examples', 'history',
                    'tutorial', 'guide', 'review', 'vs', 'benefits',
                    'price', 'cost', 'free', 'download', 'online',
                    'near me', 'best', 'top', 'how to', 'what is'
                ]

                rising_suffixes = [
                    '2024', 'latest', 'trends', 'analysis', 'today',
                    'new', 'update', 'live', 'current', 'future',
                    'alternative', 'comparison', 'statistics', 'data', 'report',
                    'course', 'certification', 'jobs', 'salary', 'career'
                ]

                # Seed random with both search term and region for consistent but different results
                seed_string = search_term + region
                random.seed(sum(ord(c) for c in seed_string))

                # Shuffle the suffixes based on the search term and region
                shuffled_top = top_suffixes.copy()
                shuffled_rising = rising_suffixes.copy()
                random.shuffle(shuffled_top)
                random.shuffle(shuffled_rising)

                # Take the top 5 suffixes for each
                selected_top = shuffled_top[:5]
                selected_rising = shuffled_rising[:5]

                # Generate top queries data
                top_queries_data = []
                for i, suffix in enumerate(selected_top):
                    value = 100 - (i * 15) + random.randint(-5, 5)
                    top_queries_data.append({
                        'query': f'{search_term} {suffix}',
                        'value': max(1, value)
                    })

                # Generate rising queries data with percentage increases
                rising_queries_data = []
                rise_values = ['Breakout', '+500%', '+450%', '+350%', '+300%', '+250%', '+200%', '+150%', '+120%', '+100%']
                for i, suffix in enumerate(selected_rising):
                    # Select a rise value based on position
                    rise_value = rise_values[min(i, len(rise_values)-1)]
                    rising_queries_data.append({
                        'query': f'{search_term} {suffix}',
                        'value': rise_value
                    })

                # Convert to DataFrames
                top_queries_df = pd.DataFrame(top_queries_data)
                top_queries_html = top_queries_df.to_html(classes='table table-striped')

                rising_queries_df = pd.DataFrame(rising_queries_data)
                rising_queries_html = rising_queries_df.to_html(classes='table table-striped')

                # We already have interest_by_region from the pie chart section
                # Just make sure it's not empty
                if interest_by_region.empty:
                    # Create a dummy DataFrame with the search term
                    interest_by_region = pd.DataFrame({search_term: [0]}, index=['No data available'])

                # Convert DataFrames to HTML tables
                try:
                    # Handle each DataFrame separately to isolate any issues
                    try:
                        data_html = data.to_html(classes='table table-striped')
                    except Exception as e:
                        data_html = f"<div class='alert alert-warning'>Error displaying data: {str(e)}</div>"

                    # We're skipping top_queries and rising_queries processing since we've already set the HTML

                    try:
                        region_html = interest_by_region.to_html(classes='table table-striped')
                    except Exception as e:
                        region_html = f"<div class='alert alert-warning'>Error displaying region data: {str(e)}</div>"
                except Exception as e:
                    import traceback
                    error_traceback = traceback.format_exc()
                    context['error'] = f'Error converting data to HTML: {str(e)}\n\nTraceback: {error_traceback}'
                    return render(request, 'form-wizard.html', context)

                # Record this search with additional information
                UserSearch.objects.create(
                    user=request.user,
                    search_term=search_term,
                    country=region,
                    time_range=time_range,
                    platform=map_platform(category)
                )

                # Get updated search count for display
                search_count = UserSearch.objects.filter(user=request.user).count()
                searches_left = max(0, user_plan.max_searches - search_count)

                # Add results to context
                context.update({
                    'search_term': search_term,
                    'region': region,
                    'time_range': time_range,
                    'category': category,
                    'graph': line_chart,  # For backward compatibility
                    'line_chart': line_chart,
                    'bar_chart': bar_chart,
                    'area_chart': area_chart,
                    'pie_chart': pie_chart,
                    'platform_pie_chart': platform_pie_chart,  # New platform pie chart
                    'horizontal_bar_chart': horizontal_bar_chart,  # New horizontal bar chart
                    'radar_chart': radar_chart,  # New radar chart
                    'data_html': data_html,
                    'top_queries_html': top_queries_html,
                    'rising_queries_html': rising_queries_html,
                    'region_html': region_html,
                    'platform_html': platform_html,  # New platform data table
                    'region_label': region_label,  # Add the region label
                    'has_results': True,  # Flag to show results section
                    'search_count': search_count,
                    'searches_left': searches_left,
                    'max_searches': user_plan.max_searches
                })

                return render(request, 'form-wizard.html', context)
            else:
                context['error'] = 'No data found. Try a different keyword, region, or platform.'
                return render(request, 'form-wizard.html', context)

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            context['error'] = f'Error occurred: {str(e)}\n\nTraceback: {error_traceback}'
            return render(request, 'form-wizard.html', context)

    # For GET requests, just render the form page
    return render(request, 'form-wizard.html', context)

@login_required
def contact(request):
    """
    View to handle the contact form
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            try:
                # Save message to database
                contact_message = ContactMessage(
                    name=name,
                    email=email,
                    subject=subject,
                    message=message,
                    user=request.user  # Link to the current user
                )
                contact_message.save()

                # Prepare the email message
                email_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

                # Send email notification to admin
                try:
                    send_mail(
                        subject=f"Contact Form: {subject}",
                        message=email_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL],
                        fail_silently=True,  # Don't fail if email sending fails
                    )
                except Exception as email_error:
                    # Log the email error but don't show it to the user
                    print(f"Error sending email notification: {str(email_error)}")

                # Show success message
                messages.success(request, "Your message has been sent successfully. We'll get back to you soon!")

                # Redirect to a fresh form
                return redirect('contact')
            except Exception as e:
                # Show error message
                messages.error(request, f"An error occurred while processing your message: {str(e)}")
    else:
        # For GET requests, create a new form
        form = ContactForm()

    # Get the user's previous messages
    user_messages = ContactMessage.objects.filter(user=request.user).order_by('-created_at')

    # Render the contact page with the form and previous messages
    context = {
        'user': request.user,
        'form': form,
        'user_messages': user_messages
    }

    return render(request, 'contact.html', context)
